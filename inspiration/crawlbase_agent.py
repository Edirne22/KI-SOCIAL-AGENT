"""Crawlbase-Adapter: öffentliche Seiten, maximal zehn Anforderungen je Plattform."""
from __future__ import annotations
import os
from pathlib import Path
import requests
from .search_config import MAX_REQUESTS_PER_PLATFORM
OUT=Path("memory/INSPIRATION_CRAWLBASE.md")
TARGETS={"instagram":"https://www.instagram.com/explore/tags/motogp/","facebook":"https://www.facebook.com/public/MotoGP","youtube":"https://www.youtube.com/results?search_query=motogp"}
def run()->str:
 token=os.environ.get("CRAWLBASE_TOKEN");lines=["# Inspiration · Crawlbase"]
 if not token:lines.append("\nNicht konfiguriert: CRAWLBASE_TOKEN fehlt.")
 else:
  for platform,url in TARGETS.items():
   try:
    r=requests.get("https://api.crawlbase.com/",headers={"Authorization":f"Bearer {token}"},params={"url":url,"format":"json"},timeout=60)
    lines.append(f"\n## {platform}\n"+(f"Öffentliche Seite geprüft (HTTP {r.status_code})." if r.status_code==200 else f"Übersprungen: HTTP {r.status_code}."))
   except requests.RequestException as e:lines.append(f"\n## {platform}\nÜbersprungen: {type(e).__name__}.")
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text("\n".join(lines)+"\n",encoding="utf-8");return OUT.read_text(encoding="utf-8")
if __name__=="__main__":run()
