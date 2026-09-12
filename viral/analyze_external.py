"""Analysiert öffentliche Inspirationsreports, ohne fremde Inhalte zu kopieren."""
from __future__ import annotations
from pathlib import Path
FILES=[Path("memory/INSPIRATION_APIFY.md"),Path("memory/INSPIRATION_BRIGHTDATA.md"),Path("memory/INSPIRATION_CRAWLBASE.md")]
def analyze()->str:
 text="\n".join(path.read_text(encoding="utf-8") for path in FILES if path.exists())
 return "# Externe Muster\n\n" + ("- Öffentliche Reports vorhanden: Hooks, Formate und Themen nur als Muster bewerten.\n" if text else "- Noch keine öffentlichen Reports verfügbar.\n")
