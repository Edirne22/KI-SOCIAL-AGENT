"""Koordiniert Inspirationsquellen und erstellt einen detaillierten, belegten Report."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
from pathlib import Path

import requests

from . import apify_agent, brightdata_agent, crawlbase_agent
from .report_builder import build, build_evidence_text, evidence_count
from telegram_bot import send_message

MEM = Path("memory")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"


def _gemini(prompt: str, api_key: str, grounded: bool = False) -> tuple[str, list[dict]]:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if grounded:
        payload["tools"] = [{"google_search": {}}]
    response = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    candidate = response.json().get("candidates", [{}])[0]
    text = "".join(part.get("text", "") for part in candidate.get("content", {}).get("parts", [])).strip()
    return text, candidate.get("groundingMetadata", {}).get("groundingChunks", [])


def _grounded_evidence(api_key: str) -> str:
    prompt = """Recherchiere öffentliche, aktuelle Themen der letzten 7 Tage für eine deutsch-türkische Motorrad-Community:
Toprak Razgatlıoğlu, Deniz und Can Öncü, MotoGP, WorldSBK sowie Motorrad-Reise. Nenne ausschließlich Fakten, die du mit öffentlichen Quellen belegen kannst. Keine erfundenen Zahlen oder Links."""
    try:
        text, chunks = _gemini(prompt, api_key, grounded=True)
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        return f"# Gemini Search Grounding\n\nKeine Grounding-Daten verfügbar: {type(error).__name__}.\n"

    lines = ["# Gemini Search Grounding", "", "## Öffentliche Quellen"]
    seen = set()
    for index, chunk in enumerate(chunks, start=1):
        web = chunk.get("web", {}) if isinstance(chunk, dict) else {}
        url = web.get("uri")
        title = web.get("title", "Ohne Titel")
        if not url or url in seen:
            continue
        seen.add(url)
        lines += [f"### Datensatz {index}", f"- Titel: {title}", "- Datum: nicht verfügbar", f"- URL: {url}", "- Engagement: nicht verfügbar"]
    if not seen:
        lines.append("Keine verifizierbaren Grounding-Links erhalten.")
    if text:
        lines += ["", "## Recherche-Notiz", text]
    return "\n".join(lines) + "\n"


def summarize(reports: dict[str, str]) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    fallback = build(reports)
    if not api_key:
        return fallback

    enriched = dict(reports)
    if evidence_count(enriched) < 5:
        enriched["Gemini Search Grounding"] = _grounded_evidence(api_key)

    evidence = build_evidence_text(enriched, limit_per_provider=None)
    prompt = f"""Hier sind öffentliche Social-Media- und Suchdaten der letzten 7 Tage. Die Daten sind als strukturierter Text mit Titel, Datum, URL und gegebenenfalls Engagement-Zahlen formatiert.

{evidence}

Erstelle einen unmittelbar nutzbaren, deutschsprachigen Report für Bülents deutsch-türkische Motorrad-/Reise-Community.

## Top-5 Trending Themen (mit Belegen)
Für jedes Thema: Name, Quelle als vollständige URL, Datum und warum es trending ist. Nutze Engagement-Zahlen nur, wenn sie in den Daten stehen; sonst schreibe „Engagement: nicht verfügbar“. Wenn weniger als fünf belegte Themen vorliegen, schreibe deutlich: „Report eingeschränkt – nur X belegte Themen gefunden.“ Erfinde niemals Namen, Daten, URLs oder Zahlen.

## 3 konkrete Content-Ideen für Bülent
Für jede Idee zwingend:
- Titel:
- Format: Reel, Post oder Story
- Hook: „vollständig ausgeschriebene erste Zeile“
- Inspirations-Quelle: vollständige URL aus den Daten
- Warum passend: kurzer, konkreter Satz
Keine abstrakten Platzhalter und keine Quelle erfinden. Falls es keine belegte Quelle gibt, kennzeichne die Idee als „nicht erstellt“.

## Quellen
Alle verwendeten URLs nummeriert. Verwende ausschließlich URLs, die in den obigen strukturierten Daten stehen.
"""
    try:
        text, _ = _gemini(prompt, api_key)
        if text:
            return "# Inspiration-Ideen\n\n" + text + "\n"
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        print(f"Gemini-Zusammenfassung übersprungen: {type(error).__name__}")
    return build(enriched)


def main() -> None:
    jobs = {"Apify": apify_agent.run, "Bright Data": brightdata_agent.run, "Crawlbase": crawlbase_agent.run}
    reports: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        future_to_name = {pool.submit(function): name for name, function in jobs.items()}
        for task in as_completed(future_to_name):
            name = future_to_name[task]
            try:
                reports[name] = task.result()
            except Exception as error:
                reports[name] = f"# {name}\n\nKeine Daten: {type(error).__name__}.\n"

    report = summarize(reports)
    (MEM / "INSPIRATION_IDEAS.md").write_text(report, encoding="utf-8")
    week = datetime.now().strftime("%Y-W%W")
    archive = MEM / "INSPIRATION_ARCHIVE"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / f"{week}.md").write_text(report, encoding="utf-8")
    log = MEM / "INSPIRATION_LOG.md"
    old = log.read_text(encoding="utf-8") if log.exists() else "# Inspiration-Log\n"
    log.write_text(old + f"\n- {datetime.now():%Y-%m-%d %H:%M}: " + ", ".join(reports) + "\n", encoding="utf-8")
    try:
        send_message("Inspiration-Analyse fertig. Der Report enthält nur belegte Themen und Quellen.")
    except RuntimeError as error:
        print(f"Telegram übersprungen: {error}")


if __name__ == "__main__":
    main()
