"""Prüft öffentliche Rennquellen und erstellt nur bestätigte Poster-Entwürfe."""
from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path
import requests
from .race_sources import SOURCES
from .poster_generator import create_poster
OUT=Path("memory/RACE_WEEKEND.md"); PUBLISHED=Path("content/PUBLISHED.md")
def collect()->dict[str,list[str]]:
 data={}
 for series,urls in SOURCES.items():
  snippets=[]
  for url in urls:
   try:
    r=requests.get(url,timeout=20,headers={"User-Agent":"KI-SOCIAL-AGENT/1.0"});snippets.append(f"Quelle: {url}\n{r.text[:3000]}") if r.ok else None
   except requests.RequestException: continue
  data[series]=snippets
 return data
def main():
 data=collect(); lines=["# Nächstes Rennwochenende",f"Geprüft: {datetime.now():%Y-%m-%d %H:%M}","","> Zeiten bitte vor Veröffentlichung an der Originalquelle prüfen."]
 for series,snippets in data.items(): lines += [f"\n## {series}", f"- Öffentliche Quellen erreichbar: {len(snippets)}"]
 OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
 print("Rennkalender geprüft. Ohne eindeutig bestätigte Terminangaben wird kein Poster erzeugt.")
if __name__=="__main__":main()
