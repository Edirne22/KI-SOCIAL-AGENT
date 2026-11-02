"""Isolated public-source Toprak weekend probe; not Hermes/Agent Reach runtime."""
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

TOPIC = "Toprak Razgatlioglu 17 18 October 2026 MotoGP news"
FEEDS = [
    "https://news.google.com/rss/search?q=" + urllib.parse.quote(TOPIC) + "&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=" + urllib.parse.quote("Toprak Razgatlioglu Ekim 2026") + "&hl=tr&gl=TR&ceid=TR:tr",
]

def main():
    from xml.etree import ElementTree as ET
    items = []
    errors = []
    for feed in FEEDS:
        try:
            request = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                root = ET.fromstring(response.read(400000))
            for node in root.findall("./channel/item")[:15]:
                title = node.findtext("title") or ""
                link = node.findtext("link") or ""
                pubdate = node.findtext("pubDate") or ""
                if not re.search(r"toprak|razgatl", title, re.I):
                    continue
                if link and not any(x["url"] == link for x in items):
                    items.append({"title": title, "url": link, "published": pubdate, "verified": False})
        except Exception as exc:
            errors.append(type(exc).__name__ + ": " + str(exc)[:150])
    result = {
        "topic": TOPIC, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "research_method": "public Google News RSS only (NOT Hermes or Agent Reach)",
        "articles": items, "errors": errors, "verified_claims": [],
        "status": "DISCOVERY_ONLY_UNVERIFIED" if items else "NO_RESULTS",
        "production_started": False, "publication_authorized": False,
    }
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/hermes-toprak-research.json", "w", encoding="utf-8") as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
    print(json.dumps({"status": result["status"], "articles": len(items), "errors": errors}))
if __name__ == "__main__":
    main()
