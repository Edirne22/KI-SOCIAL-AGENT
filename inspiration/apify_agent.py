"""Apify-Adapter: nur öffentliche Suchanfragen, keine Logins."""
from __future__ import annotations
import os
from pathlib import Path
import requests
from .search_config import APIFY_ACTORS, MAX_REQUESTS_PER_PLATFORM, PLATFORMS, SEARCH_PRIORITIES
OUT = Path("memory/INSPIRATION_APIFY.md")
def run() -> str:
    token = os.environ.get("APIFY_API_TOKEN")
    lines = ["# Inspiration · Apify"]
    if not token:
        lines.append("\nNicht konfiguriert: APIFY_API_TOKEN fehlt.")
    else:
        query = SEARCH_PRIORITIES[0][1][0]
        for platform in PLATFORMS:
            actor = APIFY_ACTORS[platform]
            try:
                response = requests.post(f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items", params={"token": token}, json={"search": query, "maxItems": MAX_REQUESTS_PER_PLATFORM}, timeout=90)
                if response.status_code != 200:
                    lines.append(f"\n## {platform}\nÜbersprungen: HTTP {response.status_code}.")
                    continue
                items = response.json()[:MAX_REQUESTS_PER_PLATFORM]
                lines.append(f"\n## {platform}\n" + "\n".join(f"- {str(item)[:500]}" for item in items) if items else f"\n## {platform}\nKeine öffentlichen Treffer.")
            except requests.RequestException as error:
                lines.append(f"\n## {platform}\nÜbersprungen: {type(error).__name__}.")
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text("\n".join(lines)+"\n", encoding="utf-8"); return OUT.read_text(encoding="utf-8")
if __name__ == "__main__": run()
