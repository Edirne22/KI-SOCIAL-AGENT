"""Erstellt einen kompakten, quellenbewussten Inspirationsreport."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from .search_config import SEARCH_PRIORITIES
MEM=Path("memory")
def build(provider_reports:dict[str,str])->str:
 lines=["# Inspiration-Ideen",f"Stand: {datetime.now():%Y-%m-%d %H:%M}","","## Priorisierte Themen"]
 for priority,terms in SEARCH_PRIORITIES[:5]: lines.append(f"- {priority}: {', '.join(terms[:3])}")
 lines += ["","## Quellenstatus"]
 for name,report in provider_reports.items(): lines.append(f"- {name}: {'Daten vorhanden' if 'Nicht konfiguriert' not in report else 'nicht konfiguriert'}")
 lines += ["","## Content-Ideen für Bülent","1. Türkischer Racer: aktueller, belegter Anlass mit persönlichem Community-Hook.","2. Rennwochenende: Vorschau mit praktischer Frage an die Community.","3. Motorrad & KI: nützlicher Tipp statt reines Trend-Kopieren.","","Hinweis: Preise, Fakten und Meldungen vor Veröffentlichung an den Originalquellen prüfen."]
 return "\n".join(lines)+"\n"
