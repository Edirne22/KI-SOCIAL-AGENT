"""Liest eigene Performance-Snapshots und benennt nur nachweisbare Muster."""
from __future__ import annotations
from pathlib import Path
def analyze()->str:
 text=Path("memory/PERFORMANCE.md").read_text(encoding="utf-8") if Path("memory/PERFORMANCE.md").exists() else ""
 return "# Interne Muster\n\n" + ("- Performance-Daten vorhanden; Likes, Kommentare, Shares und Reichweite vergleichen.\n" if "Likes:" in text else "- Noch nicht genug Performance-Daten.\n")
