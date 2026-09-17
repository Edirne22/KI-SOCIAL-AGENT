"""Prüft öffentliche Rennquellen und erstellt nur bestätigte Poster-Entwürfe."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

from .poster_generator import create_poster
from .race_sources import SOURCES

OUT = Path("memory/RACE_WEEKEND.md")
PUBLISHED = Path("content/PUBLISHED.md")
EVENT_OVERRIDE = Path("config/RACE_EVENT_OVERRIDE.json")
CALENDAR_FILE = Path("memory/RACE_CALENDAR.json")


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


def confirmed_override() -> tuple[str, str] | None:
    """Liest einen zeitlich begrenzten, offiziell belegten Termin-Fallback."""
    if not EVENT_OVERRIDE.exists():
        return None
    try:
        event = json.loads(EVENT_OVERRIDE.read_text(encoding="utf-8"))
        valid_until = datetime.strptime(event["valid_until"], "%Y-%m-%d").date()
        if datetime.now().date() > valid_until:
            return None
        source = event["source"].strip()
        details = f'{event["details"].strip()} | Quelle: {source}'
        print(f"[race] Verwende bestätigten Termin-Fallback bis {valid_until}: {event['series']}")
        return event["series"].strip(), details
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"[race] Termin-Fallback ungültig, Online-Recherche wird verwendet: {error}")
        return None


def confirmed_weekend() -> tuple[str, str] | None:
    """Liest das nächste Rennwochenende aus memory/RACE_CALENDAR.json.

    Prüft, ob heute oder in den nächsten 3 Tagen ein Event startet.
    """
    if not CALENDAR_FILE.exists():
        print("RACE-CALENDAR: keine Daten in memory/RACE_CALENDAR.json")
        sys.exit(0)

    try:
        data = json.loads(CALENDAR_FILE.read_text(encoding="utf-8"))
        events = data.get("events", [])
        if not isinstance(events, list) or not events:
            print("RACE-CALENDAR: keine Daten in memory/RACE_CALENDAR.json")
            sys.exit(0)
    except (OSError, json.JSONDecodeError, ValueError):
        print("RACE-CALENDAR: keine Daten in memory/RACE_CALENDAR.json")
        sys.exit(0)

    today = datetime.now().date()
    for event in events:
        try:
            start_str = event.get("date_start", "")
            if not start_str:
                continue
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            delta = (start_date - today).days
            if 0 <= delta <= 3:
                series = event.get("series", "MotoGP").strip()
                track = event.get("track", "").strip()
                end_str = event.get("date_end", start_str).strip()
                source = event.get("source", "").strip()
                details = f"{track} — {start_str} bis {end_str} | Quelle: {source}"
                print(f"[race] Bestätigtes Rennwochenende aus JSON: {series} / {details}")
                return series, details
        except (ValueError, TypeError):
            continue

    print("[race] Kein anstehendes Rennwochenende (Start in 0-3 Tagen) in memory/RACE_CALENDAR.json gefunden.")
    return None


def append_draft(series: str, details: str, posters: list[Path]) -> None:
    """Legt getrennte, normale Publisher-Blöcke an; Freigabe bleibt bei Bülent."""
    if len(posters) < 3:
        return
    existing = PUBLISHED.read_text(encoding="utf-8") if PUBLISHED.exists() else "# Freigegebene Beiträge\n"
    marker = f"Rennkalender: {datetime.now():%Y-W%W}-{series}"
    if marker in existing:
        return
    source = SOURCES.get(series, ["https://www.motogp.com/"])[0]
    common = (
        f"Status: ENTWURF\nFreigabe: Rennkalender\n{marker}\n"
        f"Titel: 🏁 {series} – Rennwochenende\nText: {details}\n"
        f"Quelle: {source}\nMedienstatus: EIGENES_MATERIAL\n"
    )
    entry = (
        f"\n## Instagram\n{common}Bild: {posters[0].as_posix()}\n"
        f"\n## Story\n{common}Bild: {posters[1].as_posix()}\n"
        f"\n## Facebook\n{common}Bild: {posters[2].as_posix()}\n"
    )
    PUBLISHED.write_text(existing.rstrip() + "\n" + entry, encoding="utf-8")


def main() -> None:
    sources = collect()
    found = confirmed_override() or confirmed_weekend()
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
