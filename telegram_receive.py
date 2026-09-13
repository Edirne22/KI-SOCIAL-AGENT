"""Verarbeitet Telegram-Freigaben und schreibt nur freigegebene Entwürfe nach PUBLISHED.md."""

from __future__ import annotations

import os
import re

import requests
from datetime import datetime
from pathlib import Path

from deal_hunter import compact_for_telegram, search_deal
from deal_hunter_browser import test_coupon
from price_tracking import (
    WATCHLIST,
    get_auto_track,
    set_auto_track,
    stop_tracking,
    track_product,
    trend_message,
)
from telegram_bot import get_chat_id, get_updates, send_message

SESSION_FILE = Path("memory/TELEGRAM_SESSION.md")
PUBLISHED_FILE = Path("content/PUBLISHED.md")


def load_session() -> tuple[int, dict[int, dict[str, str]]]:
    if not SESSION_FILE.is_file():
        raise FileNotFoundError(
            "Keine Telegram-Sitzung gefunden. Zuerst muss telegram_morning.py erfolgreich laufen."
        )

    content = SESSION_FILE.read_text(encoding="utf-8")
    timestamp_match = re.search(r"(?m)^Session-Timestamp:\s*(\d+)\s*$", content)
    if not timestamp_match:
        raise RuntimeError("Telegram-Sitzung enthält keinen gültigen Session-Timestamp.")

    posts: dict[int, dict[str, str]] = {}
    matches = list(
        re.finditer(
            r"^## Beitrag\s+([1-3])\s*\n(.*?)(?=^## Beitrag\s+[1-3]\s*$|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
    )
    for match in matches:
        number = int(match.group(1))
        section = match.group(2).strip()
        full_match = re.search(r"^### Vollständiger Entwurf\s*\n(.*)$", section, re.MULTILINE | re.DOTALL)
        if not full_match:
            continue
        full_text = full_match.group(1).strip()
        posts[number] = {
            "title": _field(section, "Titel"),
            "hook": _field(section, "Hook"),
            "platform": _field(section, "Plattform"),
            "full_text": full_text,
        }

    if len(posts) != 3:
        raise RuntimeError("Telegram-Sitzung enthält nicht drei lesbare Beiträge.")
    return int(timestamp_match.group(1)), posts


def _field(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+)$", text)
    return match.group(1).strip() if match else "–"


def parse_approval(text: str) -> list[int] | None:
    normalized = text.strip().lower()
    if normalized in {"alle", "✅"}:
        return [1, 2, 3]
    if normalized in {"nein", "❌"}:
        return []

    compact = re.sub(r"\s+", "", normalized)
    if re.fullmatch(r"[1-3](,[1-3])*", compact):
        return sorted({int(number) for number in compact.split(",")})
    return None


def _instagram_caption(draft: str) -> str:
    """Holt nur die Instagram-Caption aus einem vollständigen Content-Entwurf."""
    match = re.search(
        r"^Instagram-Caption:\s*\n(.+?)(?=^\s*(?:Facebook-Post|TikTok-Skript|Visuelle Idee|Hashtags Instagram|Hashtags TikTok|Trend-Bezug):|\Z)",
        draft,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else draft.strip()


def _published_targets(platform: str) -> list[tuple[str, str]]:
    """Übersetzt eine Plattformangabe in eindeutig veröffentlichbare Formate.

    Sammel-Angaben werden in getrennte Instagram- und Facebook-Blöcke geteilt.
    TikTok wird bewusst nicht erzeugt: Dafür gibt es noch keinen getesteten
    Publisher. Instagram-Feed-Posts erhalten Bild: auto für den Mediengenerator.
    """
    value = platform.strip().lower()
    if "reel" in value:
        return [("Instagram Reel", "Video: auto")]
    targets: list[tuple[str, str]] = []
    if "instagram" in value:
        targets.append(("Instagram", "Bild: auto"))
    if "facebook" in value:
        targets.append(("Facebook", ""))
    if "tiktok" in value:
        print("TikTok in der Freigabe erkannt, aber ohne Publisher nicht angelegt.")
    if targets:
        return targets
    return [(platform.strip(), "")]


def append_approved_posts(posts: dict[int, dict[str, str]], selected: list[int], update_id: int) -> None:
    PUBLISHED_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = PUBLISHED_FILE.read_text(encoding="utf-8") if PUBLISHED_FILE.exists() else "# Freigegebene Beiträge\n"
    marker = f"Telegram-Update-ID: {update_id}"
    if marker in existing:
        print(f"Telegram-Update {update_id} wurde bereits verarbeitet.")
        return

    entries = []
    for number in selected:
        post = posts[number]
        source = _field(post["full_text"], "Inspirations-Quelle")
        source_line = f"Quelle: {source}" if source.startswith(("https://", "http://")) else ""
        media_status = "Medienstatus: QUELLE_PRÜFEN" if source_line else ""
        for header, media_line in _published_targets(post["platform"]):
            entries.extend(
                [
                    f"## {header}",
                    "Status: FREIGEGEBEN",
                    "Freigabe: Telegram",
                    marker,
                    "Text:",
                    _instagram_caption(post["full_text"]),
                    source_line,
                    media_status,
                    media_line,
                    "",
                ]
            )
    PUBLISHED_FILE.write_text(existing.rstrip() + "\n\n" + "\n".join(entries).rstrip() + "\n", encoding="utf-8")
    print(f"{len(selected)} freigegebene Beiträge nach {PUBLISHED_FILE} geschrieben.")


def acknowledge_through(update_id: int) -> None:
    # Telegram verwirft Updates mit kleinerer ID nach diesem Aufruf.
    get_updates(offset=update_id + 1)



WORKFLOW_COMMANDS = {
    "inspiration": ("inspiration-agent.yml", "Inspiration-Analyse gestartet. Ich melde mich mit dem Ergebnis."),
    "race": ("race-calendar.yml", "Rennkalender-Prüfung gestartet. Poster bleiben Entwürfe."),
    "viral": ("viral-analysis.yml", "Viral-Analyse gestartet. Die Muster werden im Memory aktualisiert."),
    "follow-analyse": ("follow-analyzer.yml", "Follow-Analyse gestartet. Ich melde mich mit dem Ergebnis."),
}


def dispatch_workflow(workflow_file: str, inputs: dict[str, str] | None = None) -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repository:
        raise RuntimeError("GitHub-Workflow-Auslösung ist in diesem Lauf nicht konfiguriert.")
    response = requests.post(
        f"https://api.github.com/repos/{repository}/actions/workflows/{workflow_file}/dispatches",
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"},
        json={"ref": "main", "inputs": inputs or {}},
        timeout=30,
    )
    if response.status_code != 204:
        raise RuntimeError(f"GitHub-Workflow konnte nicht gestartet werden (HTTP {response.status_code}).")


def approve_race_draft() -> bool:
    if not PUBLISHED_FILE.exists():
        return False
    content = PUBLISHED_FILE.read_text(encoding="utf-8")
    pattern = r"(?ms)(## .*?Rennposter.*?\nStatus:\s*)ENTWURF(?=\n.*?Freigabe:\s*Rennkalender)"
    updated, count = re.subn(pattern, r"\1FREIGEGEBEN", content, count=1)
    if not count:
        return False
    PUBLISHED_FILE.write_text(updated, encoding="utf-8")
    return True


TRACK_HELP = (
    "Format: track: <Produkt> [max: X €] [min: Y] [netz: Z]\n"
    "Beispiele:\n• track: Motorradhandschuhe max 50 €\n"
    "• track: Handyvertrag 80GB D1 max 13 €"
)


def _named_command(text: str, names: tuple[str, ...]) -> str | None:
    alternatives = "|".join(re.escape(name) for name in names)
    match = re.match(rf"(?is)^\s*(?:{alternatives})\s*:?\s*(.*)$", text)
    return match.group(1).strip() if match else None


def parse_track_command(text: str) -> tuple[str, str] | None:
    """Erkennt mobilfreundliche Track-Varianten ohne die Produktschreibweise zu verändern."""
    value = _named_command(text, ("track",))
    if value is None:
        return None
    if not value:
        return "", ""

    separator = re.search(r"[|,(]", value)
    product_part = value[:separator.start()] if separator else value
    criteria_part = value[separator.end():].rstrip(")") if separator else ""

    patterns = (
        ("max", re.compile(r"(?i)\b(?:max|bis|unter)\s*:?\s*(\d+(?:[.,]\d+)?)\s*€?")),
        ("min", re.compile(r"(?i)\b(?:min|mindestens)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(GB)?\b")),
        ("netz", re.compile(r"(?i)\bnetz\s*:?\s*(D1|D2|O2)\b")),
        ("netz", re.compile(r"(?i)\b(D1|D2|O2)\s+netz\b")),
    )
    matches = []
    for label, pattern in patterns:
        for match in pattern.finditer(value):
            matches.append((match.start(), match.end(), label, match.group(1), match.group(0)))

    if matches and not separator:
        first_criterion = min(start for start, *_ in matches)
        product_part = value[:first_criterion]
        criteria_part = value[first_criterion:]

    product_name = product_part.strip(" \t,|()")
    if not product_name:
        return "", ""

    criteria = []
    seen = set()
    criteria_scope = criteria_part or value[len(product_part):]
    for _, _, label, raw_value, raw_text in matches:
        if raw_text not in criteria_scope and not separator:
            continue
        if label == "max":
            item = f"max: {raw_value.replace(',', '.')} €"
        elif label == "min":
            unit = " GB" if "gb" in raw_text.lower() else ""
            item = f"min: {raw_value.replace(',', '.')}{unit}"
        else:
            item = f"Netz: {raw_value.upper()}"
        if item not in seen:
            criteria.append(item)
            seen.add(item)
    return product_name, " | ".join(criteria)



def parse_deal_command(text: str) -> tuple[str, str] | None:
    deal_test = _named_command(text, ("deal-test",))
    if deal_test is not None:
        return "test", deal_test
    query = _named_command(text, ("deal", "suche"))
    return ("search", query) if query is not None else None



def create_carousel_draft(topic: str) -> str:
    """Legt einen kontrollierten Karussell-Entwurf an; eine Freigabe bleibt erforderlich."""
    cleaned = re.sub(r"\s+", " ", topic).strip()
    if not cleaned:
        return "Bitte nutze: karussell: <Thema>"
    PUBLISHED_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = PUBLISHED_FILE.read_text(encoding="utf-8") if PUBLISHED_FILE.exists() else ""
    caption = f"{cleaned}\n\nWelcher Slide gefällt dir am besten? 🏍️"
    block = (
        f"\n\n## Instagram Karussell\n"
        f"Status: ENTWURF\n"
        f"Freigabe: Telegram\n"
        f"Titel: {cleaned}\n"
        f"Text: {caption}\n"
        f"Bilder: auto\n"
    )
    PUBLISHED_FILE.write_text(existing.rstrip() + block, encoding="utf-8")
    return "Karussell-Entwurf erstellt. Drei Bilder werden durch den Mediengenerator erzeugt. Vor der Veröffentlichung ist weiterhin eine Freigabe nötig."



EXPERIMENTS_FILE = Path("memory/EXPERIMENTS.md")
FUNNEL_FILE = Path("memory/FUNNEL_ANALYSIS.md")
GROWTH_FILE = Path("memory/GROWTH_LOG.md")
COMPETITORS_FILE = Path("memory/COMPETITOR_TRACKING.md")


def _memory_preview(path: Path, title: str) -> str:
    if not path.exists():
        return f"{title}: Noch keine Daten verfügbar."
    return (title + "\n" + path.read_text(encoding="utf-8").strip())[:3500]


def start_experiment(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        return "Bitte nutze: experiment: start <Name>"
    content = EXPERIMENTS_FILE.read_text(encoding="utf-8") if EXPERIMENTS_FILE.exists() else "# A/B-Experimente\n\n## Laufende Experimente\n"
    if name.lower() in content.lower():
        return f"Experiment „{name}“ ist bereits dokumentiert."
    block = (
        f"\n### {name}\n"
        f"- Start: {datetime.now():%Y-%m-%d}\n"
        f"- Hypothese: Bitte vor dem ersten Beitrag konkret ergänzen.\n"
        f"- Variante A: Bitte ergänzen\n"
        f"- Variante B: Bitte ergänzen\n"
        f"- Metrik: Kommentare pro Reichweite\n"
        f"- Status: läuft\n"
        f"- Ergebnis: –\n"
    )
    marker = "## Laufende Experimente"
    content = content.replace(marker, marker + block, 1) if marker in content else content.rstrip() + "\n\n" + marker + block
    EXPERIMENTS_FILE.write_text(content.rstrip() + "\n", encoding="utf-8")
    return f"✅ Experiment „{name}“ gestartet. Ergänze Hypothese und Varianten vor dem ersten Vergleichspost."


def main() -> None:
    allowed_chat_id = get_chat_id()
    updates = get_updates()

    for update in sorted(updates, key=lambda item: item.get("update_id", 0)):
        update_id = update.get("update_id")
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        message_text = message.get("text")

        if not isinstance(update_id, int):
            continue
        if str(chat.get("id", "")) != str(allowed_chat_id):
            acknowledge_through(update_id)
            continue
        if not isinstance(message_text, str):
            acknowledge_through(update_id)
            continue

        text_lower = message_text.strip().lower()
        print(f"DEBUG: Text='{message_text}'")
        print(f"DEBUG: lower='{text_lower}'")
        print(f"DEBUG: match_trend={text_lower.startswith('trend:')}")
        print(f"DEBUG: match_track={text_lower.startswith('track:')}")
        print(f"DEBUG: match_watchlist={text_lower.strip() in ('watchlist', 'liste')}")

        auto_track_prefixes = ("auto-track:", "autotrack:", "auto track:")
        carousel_command = text_lower.startswith(("karussell:", "karussell ", "karussell\t"))
        experiment_start = re.match(r"(?is)^experiment\s*:\s*start\s+(.+)$", message_text)
        is_experiment = text_lower == "experiment"
        is_funnel = text_lower == "funnel"
        is_growth = text_lower == "growth"
        is_competitors = text_lower in ("competitors", "wettbewerber")
        verify_username = _named_command(message_text, ("verify",))
        is_trend_command = text_lower.startswith(("trend:", "trend ", "trend\t"))
        is_track_command = text_lower == "track" or text_lower.startswith(("track:", "track ", "track\t"))
        deal_command = parse_deal_command(message_text)
        stop_product = _named_command(message_text, ("stop", "beenden"))
        done_product = _named_command(message_text, ("erledigt", "gekauft"))

        # Exklusive Reihenfolge: Eine Telegram-Nachricht kann nur einen Handler erreichen.
        if text_lower.startswith(auto_track_prefixes):
            print(f"Empfangen: {message_text} → erkannt als: Auto-Track")
            value = message_text.split(":", 1)[1].strip().lower()
            if value not in {"on", "off"}:
                send_message("Bitte nutze: auto-track: on oder auto-track: off")
            else:
                enabled = value == "on"
                set_auto_track(enabled)
                send_message(
                    "✅ Auto-Track aktiv. Alle zukünftigen deal:-Suchen werden automatisch beobachtet."
                    if enabled
                    else "⏸️ Auto-Track aus. Bei deal:-Suche frage ich wieder nach."
                )

        elif experiment_start:
            print(f"Empfangen: {message_text} → erkannt als: Experiment starten")
            send_message(start_experiment(experiment_start.group(1)))

        elif is_experiment:
            print(f"Empfangen: {message_text} → erkannt als: Experimente")
            send_message(_memory_preview(EXPERIMENTS_FILE, "🧪 A/B-Experimente"))

        elif is_funnel:
            print(f"Empfangen: {message_text} → erkannt als: Funnel")
            send_message(_memory_preview(FUNNEL_FILE, "📊 Conversion-Funnel"))

        elif is_growth:
            print(f"Empfangen: {message_text} → erkannt als: Growth")
            send_message(_memory_preview(GROWTH_FILE, "📈 Growth-Log"))

        elif is_competitors:
            print(f"Empfangen: {message_text} → erkannt als: Wettbewerber")
            send_message(_memory_preview(COMPETITORS_FILE, "🔎 Wettbewerber-Tracking"))

        elif carousel_command:
            print(f"Empfangen: {message_text} → erkannt als: Karussell")
            topic = re.sub(r"(?is)^\s*karussell\s*:?[ \t]*", "", message_text).strip()
            send_message(create_carousel_draft(topic))

        elif is_trend_command:
            print(f"Empfangen: {message_text} → erkannt als: Trend")
            product = re.sub(r"(?is)^\s*trend\s*:?\s*", "", message_text).strip()
            send_message(trend_message(product) if product else "Bitte nutze: trend: <Produkt>")

        elif is_track_command:
            print(f"Empfangen: {message_text} → erkannt als: Track")
            name, criteria = parse_track_command(message_text) or ("", "")
            if not name:
                from deal_hunter import LAST_QUERY_FILE
                if LAST_QUERY_FILE.exists() and text_lower == "track":
                    send_message(track_product(LAST_QUERY_FILE.read_text(encoding="utf-8").strip()))
                else:
                    send_message(TRACK_HELP)
            else:
                send_message(track_product(name, criteria))

        elif deal_command:
            command, value = deal_command
            print(f"Empfangen: {message_text} → erkannt als: {'Deal-Test' if command == 'test' else 'Deal-Suche'}")
            if command == "search":
                if not value:
                    send_message("Bitte nutze: deal: <Produkt> oder suche: <Produkt>")
                else:
                    send_message("Ich recherchiere – das kann ein bis zwei Minuten dauern.")
                    try:
                        answer = compact_for_telegram(search_deal(value, status_callback=send_message))
                        if get_auto_track():
                            answer += "\n\n✅ Wird automatisch beobachtet.\n" + track_product(value)
                        else:
                            answer += "\n\n💡 Soll ich das beobachten? Antworte mit track."
                        send_message(answer)
                    except (RuntimeError, ValueError) as error:
                        send_message(f"Deal-Recherche nicht möglich: {error}")
            else:
                parts = value.split(maxsplit=1)
                if len(parts) != 2:
                    send_message("Bitte nutze: deal-test: <HTTPS-URL> <CODE>")
                else:
                    result = test_coupon(parts[0], parts[1])
                    send_message(f"Code-Test: {result['status']} – {result['reason']}")

        elif stop_product is not None:
            print(f"Empfangen: {message_text} → erkannt als: Stop")
            if not stop_product:
                send_message("Bitte nenne ein Produkt, zum Beispiel: stop: Motorradhandschuhe")
            else:
                send_message(stop_tracking(stop_product, False))

        elif done_product is not None:
            print(f"Empfangen: {message_text} → erkannt als: Erledigt")
            if not done_product:
                send_message("Bitte nenne ein Produkt, zum Beispiel: erledigt: Motorradhandschuhe")
            else:
                send_message(stop_tracking(done_product, True))

        elif verify_username is not None:
            print(f"Empfangen: {message_text} → erkannt als: Follow-Verify")
            username = verify_username.lstrip("@").strip()
            if not re.fullmatch(r"[A-Za-z0-9._-]{1,30}", username):
                send_message("Bitte nutze: verify: <öffentlicher Instagram-Username>")
            else:
                try:
                    dispatch_workflow("follow-analyzer.yml", {"verify_username": username})
                    send_message(f"Profilprüfung für @{username} gestartet. Das Ergebnis kommt per Telegram.")
                except RuntimeError as error:
                    send_message(f"Profilprüfung konnte nicht gestartet werden: {error}")

        elif text_lower in WORKFLOW_COMMANDS:
            workflow_file, confirmation = WORKFLOW_COMMANDS[text_lower]
            print(f"Empfangen: {message_text} → erkannt als: Agenten-Workflow")
            try:
                dispatch_workflow(workflow_file, {"all_accounts": "true"} if text_lower == "follow-analyse" else None)
                send_message(confirmation)
            except RuntimeError as error:
                send_message(f"Analyse konnte nicht gestartet werden: {error}")

        elif text_lower == "go":
            print(f"Empfangen: {message_text} → erkannt als: Rennposter-Freigabe")
            if approve_race_draft():
                send_message("Rennposter freigegeben. Es bleibt bis zum Publisher-Lauf ein kontrollierter Entwurf.")
            else:
                send_message("Kein offener Rennposter-Entwurf gefunden.")

        elif text_lower in ("watchlist", "liste"):
            print(f"Empfangen: {message_text} → erkannt als: Watchlist")
            active = WATCHLIST.read_text(encoding="utf-8") if WATCHLIST.exists() else "Keine Watchlist vorhanden."
            send_message("📋 Watchlist\n" + active[:3000])

        else:
            print(f"DEBUG: Kein Kommando erkannt für: {message_text}")
            session_timestamp, posts = load_session()
            message_timestamp = message.get("date", 0)
            if message_timestamp < session_timestamp:
                acknowledge_through(update_id)
                continue

            selected = parse_approval(message_text)
            if selected is None:
                send_message("Danke! Bitte antworte mit 1,3, alle, ✅, nein oder ❌; für Recherche: deal: <Produkt>.")
            elif not selected:
                send_message("Keine Beiträge freigegeben. In PUBLISHED.md wurde nichts eingetragen.")
            else:
                append_approved_posts(posts, selected, update_id)
                selected_text = "+".join(str(number) for number in selected)
                send_message(
                    f"Beitrag {selected_text} freigegeben – für 12:00 vorgemerkt. "
                    "Die Veröffentlichung bleibt manuell."
                )

        acknowledge_through(update_id)
        return

    print("Keine neue Telegram-Antwort für die aktuelle Sitzung.")


if __name__ == "__main__":
    main()
