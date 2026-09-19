"""Wöchentlicher Finanzplaner-Agent. Recherchiert Zinsen, vergleicht mit Plan, meldet per Telegram."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from llm_router import quick_chat
from telegram_bot import send_message

PLAN_JSON = Path("memory/FINANCE_PLAN.json")
PLAN_MD = Path("memory/FINANCE_PLAN.md")
RATES_CACHE = Path("memory/FINANCE_RATES_CACHE.md")
EVENTS = Path("memory/FINANCE_EVENTS.jsonl")

# Kostenlose Direktabfrage der öffentlichen Zins-Übersichten
RATE_SOURCES = [
    {"name": "Finanztip", "url": "https://www.finanztip.de/tagesgeld/"},
    {"name": "Check24", "url": "https://www.check24.de/tagesgeld/"},
    {"name": "Verivox", "url": "https://www.verivox.de/tagesgeld/"},
    {"name": "Biallo", "url": "https://www.biallo.de/tagesgeld/"},
]


def fetch_source(name: str, url: str) -> str:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return ""
        # Ganzes HTML – die KI filtert die relevanten Zahlen
        return r.text[:50000]  # nur die ersten 50k Zeichen reichen
    except Exception as e:
        print(f"[finance] {name} fehlgeschlagen: {e}")
        return ""


def gather_all_sources() -> list[dict]:
    results = []
    for source in RATE_SOURCES:
        html = fetch_source(source["name"], source["url"])
        if html:
            results.append({"name": source["name"], "url": source["url"], "html": html})
    return results


def _is_valid_analysis(text: str) -> bool:
    """Prüft, ob die Antwort eine echte Analyse enthält."""
    if not text or len(text.strip()) < 80:
        return False
    low = text.lower()
    bad_markers = ["user safety", "safety: safe", "cannot provide", "kann nicht"]
    if any(m in low for m in bad_markers):
        return False
    # Muss mindestens eine Zahl/Zinssatz enthalten
    if not any(c.isdigit() for c in text):
        return False
    return True


def analyze_with_router(plan: dict, sources: list[dict]) -> str:
    if not sources:
        return "Diese Woche konnten keine Zinsquellen abgerufen werden."
    prompt = f"""Du bist Finanz-Rechercheur (keine Anlageberatung!).

Aktueller Plan:
{json.dumps(plan, ensure_ascii=False, indent=2)}

Öffentliche Zins-Übersichten:
"""
    for source in sources[:2]:
        # Nur relevante Snippets senden, nicht das ganze HTML
        stripped = re.sub(r"<[^>]+>", " ", source["html"])
        stripped = re.sub(r"\s+", " ", stripped)
        prompt += f"\n--- {source['name']} ---\n{stripped[:4000]}\n"

    prompt += """
Aufgabe:
1. Nenne die 3 aktuell besten Tagesgeld-Zinsen (Anbieter + Zinssatz).
2. Vergleiche mit dem aktuellen Chase-Zins aus dem Plan.
3. Falls Chase schlechter wird (nach 26.12.2026): nenne eine Alternative.
4. Formuliere eine kurze Empfehlung für Bülent (max. 4 Sätze, direkt, community-nah).

WICHTIG:
- Keine Anlageberatung. Nur Recherche-Zusammenfassung.
- Antworte NIEMALS nur mit Sicherheitshinweisen wie "User Safety: safe".
- Liefere IMMER eine inhaltliche Analyse mit konkreten Zinssätzen, Anbietern und einem Vergleich zum Chase-Zins.
- Falls du keine aktuellen Zinssätze aus den Quellen extrahieren kannst, schreibe das klar und nenne trotzdem die 3 aus deinem Wissen bekanntesten Tagesgeld-Anbieter mit ungefähren Zinssätzen.
- Maximal 4 Sätze.
Antworte auf Deutsch, kompakt.
"""
    first_try = quick_chat(prompt, task_type="fast_chat").strip()
    if _is_valid_analysis(first_try):
        return first_try

    second_try = quick_chat(prompt, task_type="default").strip()
    if _is_valid_analysis(second_try):
        return second_try

    return "Analyse diese Woche nicht möglich. Bitte Quellen manuell prüfen: Finanztip, Check24, Verivox."


def build_telegram_summary(analysis: str, plan: dict) -> str:
    chase = plan["current_accounts"][0]
    header = (
        f"💰 Finanz-Update ({datetime.now(timezone.utc):%Y-%m-%d})\n\n"
        f"Chase aktuell: {chase['rate_percent']}% bis {chase['rate_valid_until']}, "
        f"danach {chase['rate_after_percent']}%\n\n"
    )
    return header + analysis[:1200]


def update_cache(analysis: str, sources: list[dict]) -> None:
    RATES_CACHE.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"\n## Lauf {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC\n\n"
        f"Quellen: {', '.join(s['name'] for s in sources)}\n\n"
        f"{analysis}\n"
    )
    existing = RATES_CACHE.read_text(encoding="utf-8") if RATES_CACHE.exists() else "# Zins-Cache\n"
    # Nur die letzten 20 Einträge behalten
    RATES_CACHE.write_text(existing.rstrip() + entry, encoding="utf-8")


def append_event(analysis: str) -> None:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "weekly_check",
        "analysis_excerpt": analysis[:200],
    }
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def update_plan_md(plan: dict) -> None:
    next_check = (datetime.now(timezone.utc) + timedelta(days=7)).replace(microsecond=0).isoformat()
    content = f"""# Finanzplan

Stand: {datetime.now(timezone.utc):%Y-%m-%d}

## Investierbar
- {plan['investable_eur']} € bei Chase
- {plan['cash_separate_eur']} € Cash separat (nicht getrackt)

## Aktuelle Konten
"""
    for acc in plan["current_accounts"]:
        content += (
            f"- **{acc['bank']}** {acc['product']}: "
            f"{acc['rate_percent']}% bis {acc['rate_valid_until']}, "
            f"danach {acc['rate_after_percent']}%\n"
            f"  {acc.get('note', '')}\n"
        )
    content += "\n## Regeln\n"
    for rule in plan["rules"]:
        content += f"- {rule}\n"
    content += f"\n## Nächste Prüfung\n- {next_check}\n"
    PLAN_MD.write_text(content, encoding="utf-8")


def main() -> None:
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    sources = gather_all_sources()
    analysis = analyze_with_router(plan, sources)
    update_cache(analysis, sources)
    append_event(analysis)
    update_plan_md(plan)
    summary = build_telegram_summary(analysis, plan)
    try:
        send_message(summary)
    except Exception as e:
        print(f"[finance] Telegram-Versand fehlgeschlagen: {e}")


if __name__ == "__main__":
    main()
