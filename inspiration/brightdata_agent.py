"""Bright-Data-REST-Adapter; GitHub Actions kann keinen lokalen MCP-Server aufrufen."""
from __future__ import annotations
import os
from pathlib import Path
import requests
from .search_config import BRIGHTDATA_DATASETS, MAX_REQUESTS_PER_PLATFORM
OUT=Path("memory/INSPIRATION_BRIGHTDATA.md")
def run() -> str:
 token=os.environ.get("BRIGHTDATA_API_TOKEN"); lines=["# Inspiration · Bright Data"]
 if not token: lines.append("\nNicht konfiguriert: BRIGHTDATA_API_TOKEN fehlt.")
 else:
  for platform,dataset in BRIGHTDATA_DATASETS.items():
   dataset=os.environ.get(f"BRIGHTDATA_{platform.upper()}_DATASET_ID",dataset)
   if not dataset: lines.append(f"\n## {platform}\nÜbersprungen: Dataset-ID fehlt."); continue
   try:
    r=requests.post("https://api.brightdata.com/datasets/v3/scrape",headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},params={"dataset_id":dataset},json=[{"url":f"https://www.{platform}.com/"}],timeout=90)
    lines.append(f"\n## {platform}\n" + (f"Anfrage gestartet (HTTP {r.status_code}); Abruf erfolgt beim nächsten Lauf." if r.status_code in (200,201,202) else f"Übersprungen: HTTP {r.status_code}."))
   except requests.RequestException as e: lines.append(f"\n## {platform}\nÜbersprungen: {type(e).__name__}.")
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text("\n".join(lines)+"\n",encoding="utf-8");return OUT.read_text(encoding="utf-8")
if __name__=="__main__":run()
