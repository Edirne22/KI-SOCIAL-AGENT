"""Bewertet öffentliche Inspirationsreports und führt ein transparentes Wettbewerber-Tracking."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

FILES = [
    Path("memory/INSPIRATION_APIFY.md"),
    Path("memory/INSPIRATION_BRIGHTDATA.md"),
    Path("memory/INSPIRATION_CRAWLBASE.md"),
]
COMPETITORS = Path("memory/COMPETITOR_TRACKING.md")


def analyze() -> str:
    reports = [path.read_text(encoding="utf-8") for path in FILES if path.exists()]
    if reports:
        summary = "- Öffentliche Inspirationsreports vorhanden: Themen, Formate und Hooks nur als Muster bewerten.\n"
        competitor = f"""# Wettbewerber-Tracking

Stand: {datetime.now():%Y-%m-%d %H:%M}

## Öffentliche Beobachtung
- Es liegen öffentliche Recherche-Reports vor. Ausgewertet werden nur wiederkehrende Themen, Video-Formate und Interaktionsmuster.
- Konkrete Account- oder Leistungsbehauptungen werden erst gespeichert, wenn sie in den Reports eindeutig belegt sind.

## Eigene Adaption
- Keine Beiträge kopieren. Stattdessen eigene deutsch-türkische Motorrad- und Reiseerlebnisse mit klarer Haltung, Route oder Frage entwickeln.
"""
    else:
        summary = "- Noch keine öffentlichen Wettbewerber-Reports verfügbar.\n"
        competitor = """# Wettbewerber-Tracking

## Status
- Noch keine belastbaren öffentlichen Reports verfügbar; daher keine erfundenen Vergleichs-Accounts oder Leistungswerte.

## Eigene Adaption
- Erst öffentliche Daten sammeln, dann Themen, Formate und Interaktionsmuster vergleichen. Keine Beiträge kopieren.
"""
    COMPETITORS.write_text(competitor, encoding="utf-8")
    return "# Externe Muster\n\n" + summary
