"""Prüft öffentliche Rennquellen und erstellt nur bestätigte Poster-Entwürfe."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

import requests

from .poster_generator import create_poster
from .race_sources import SOURCES

OUT = Path("memory/RACE_WEEKEND.md")
PUBLISHED = Path("content/PUBLISHED.md")
MODEL = "gemini-3.8-flash"


def collect() -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    for series, urls in SOURCES.items():
        available = []
        for url in urls:
            try:
                response = requests.get(url, timeout=20, headers={"User-Agent": "KI-SOCIAL-AGENT/1.0"})
                if response.ok:
                    available.append(url)
            except requests.RequestException:
                continue
        data[series] = available
    return data


def confirmed_weekend() -> tuple[str, str] | None:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    prompt = """Prüfe anhand öffentlicher, offizieller Rennkalender das nächste MotoGP-, WorldSBK- oder Formel-1-Wochenende.
Antworte nur exakt in diesem Format:
BESTÄTIGT: ja oder nein
SERIE: MotoGP oder WorldSBK oder Formel 1
DETAILS: Datum, Strecke und nur bestätigte Sessionzeiten
Wenn ein Datum, eine Serie oder Zeiten nicht sicher belegt sind, antworte BESTÄTIGT: nein.
Erfinde keine Zeiten."""
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": key},
            json={"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]},
            timeout=120,
        )
        if response.status_code != 200:
            return None
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (requests.RequestException, KeyError, IndexError):
        return None
    if not re.search(r"(?im)^BESTÄTIGT:\s*ja\s*$", text):
        return None
    series = re.search(r"(?im)^SERIE:\s*(.+)$", text)
    details = re.search(r"(?im)^DETAILS:\s*(.+)$", text)
    return (series.group(1).strip(), details.group(1).strip()) if series and details else None


def append_draft(series: str, details: str, posters: list[Path]) -> None:
    if not posters:
        return
    existing = PUBLISHED.read_text(encoding="utf-8") if PUBLISHED.exists() else "# Freigegebene Beiträge\n"
    marker = f"Rennkalender: {datetime.now():%Y-W%W}-{series}"
    if marker in existing:
        return
    entry = (
        f"\n## Instagram Rennposter\nStatus: ENTWURF\nFreigabe: Rennkalender\n{marker}\n"
        f"Titel: 🏁 {series} – Rennwochenende\nText: {details}\nBild: {posters[0].as_posix()}\n"
    )
    PUBLISHED.write_text(existing.rstrip() + "\n" + entry, encoding="utf-8")


def main() -> None:
    sources = collect()
    found = confirmed_weekend()
    lines = ["# Nächstes Rennwochenende", f"Geprüft: {datetime.now():%Y-%m-%d %H:%M}", "", "> Zeiten bitte vor Veröffentlichung an der Originalquelle prüfen."]
    for series, urls in sources.items():
        lines += [f"\n## {series}", f"- Öffentliche Quellen erreichbar: {len(urls)}"]
    if not found:
        lines += ["", "Kein eindeutig bestätigtes Rennwochenende gefunden; kein Poster-Entwurf erzeugt."]
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("Keine bestätigten Renndaten – Poster sicher übersprungen.")
        return
    series, details = found
    posters = create_poster(series, details)
    lines += ["", f"Bestätigt: {series}", f"Details: {details}", f"Poster-Entwürfe: {len(posters)}"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_draft(series, details, posters)
    print("Bestätigter Rennkalender und Poster-Entwurf erstellt.")


if __name__ == "__main__":
    main()
