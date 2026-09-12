"""Liest veröffentlichte Posts und speichert verfügbare Instagram- und Facebook-Insights."""

from __future__ import annotations

import os
import re
import time
from datetime import date
from pathlib import Path

import requests

PUBLISHED_FILE = Path("content/PUBLISHED.md")
PERFORMANCE_FILE = Path("memory/PERFORMANCE.md")
IG_API = "https://graph.instagram.com/v23.0"
FB_API = "https://graph.facebook.com/v26.0"
IG_METRICS = "likes,comments,shares,saved,reach,impressions"
FB_METRICS = "post_impressions,post_reactions_by_type_total,post_clicks"


def number(value) -> int:
    if isinstance(value, dict):
        return sum(number(item) for item in value.values())
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_published_posts(content: str) -> list[dict[str, str]]:
    pattern = r"^## (.+?) \[GEPOSTET ([^|\]]+?) \| ID: ([^\]]+)\]\s*\n(.*?)(?=^## |\Z)"
    posts = []
    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        platform, published_at, media_id, body = (part.strip() for part in match.groups())
        normalized = "Facebook" if platform.lower().startswith("facebook") else "Instagram"
        title_match = re.search(r"(?m)^Titel:\s*(.+)$", body)
        text_match = re.search(r"(?ms)^Text:\s*(.+?)(?=^(?:Bild|Video|Status|Freigabe|Telegram-Update-ID):|\Z)", body)
        title = (title_match.group(1) if title_match else (text_match.group(1).splitlines()[0] if text_match else platform)).strip()
        posts.append({"platform": normalized, "id": media_id, "published_at": published_at, "title": re.sub(r"\s+", " ", title)[:120]})
    return posts[-7:]


def fetch_insights(platform: str, media_id: str) -> dict[str, int] | None:
    token_name = "FACEBOOK_PAGE_TOKEN" if platform == "Facebook" else "INSTAGRAM_ACCESS_TOKEN"
    token = os.environ.get(token_name)
    if not token:
        print(f"{token_name} fehlt – {platform}-Insights werden übersprungen.")
        return None

    base = FB_API if platform == "Facebook" else IG_API
    metrics = FB_METRICS if platform == "Facebook" else IG_METRICS
    try:
        response = requests.get(
            f"{base}/{media_id}/insights",
            params={"metric": metrics, "access_token": token},
            timeout=30,
        )
    except requests.RequestException as error:
        print(f"{platform}-Insights für {media_id} übersprungen: {error}")
        return None
    if response.status_code != 200:
        print(f"{platform}-Insights für {media_id} noch nicht verfügbar (HTTP {response.status_code}).")
        return None

    values = {}
    for item in response.json().get("data", []):
        metric_values = item.get("values") or []
        values[item.get("name", "")] = number(metric_values[-1].get("value")) if metric_values else 0

    if not values:
        print(f"{platform}-Insights für {media_id} enthalten noch keine Werte.")
        return None
    if platform == "Instagram":
        return {"likes": values.get("likes", 0), "comments": values.get("comments", 0), "shares": values.get("shares", 0), "saved": values.get("saved", 0), "reach": values.get("reach", 0), "impressions": values.get("impressions", 0), "clicks": 0}
    return {"likes": values.get("post_reactions_by_type_total", 0), "comments": 0, "shares": 0, "saved": 0, "reach": values.get("post_impressions", 0), "impressions": values.get("post_impressions", 0), "clicks": values.get("post_clicks", 0)}


def append_snapshot(post: dict[str, str], metrics: dict[str, int]) -> None:
    PERFORMANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = PERFORMANCE_FILE.read_text(encoding="utf-8") if PERFORMANCE_FILE.exists() else "# Performance-Memory\n"
    today = date.today().isoformat()
    key = f"Datum: {today}\nID: {post['id']}"
    if key in existing:
        return
    entry = f"""\n## Beitrag vom {today} - Plattform: {post['platform']} - Titel: {post['title']}
Datum: {today}
ID: {post['id']}
Veröffentlicht: {post['published_at']}
Likes: {metrics['likes']}
Kommentare: {metrics['comments']}
Shares: {metrics['shares']}
Gespeichert: {metrics['saved']}
Reichweite: {metrics['reach']}
Impressionen: {metrics['impressions']}
Klicks: {metrics['clicks']}
Viral-Rate: {((metrics['likes'] + metrics['comments'] + metrics['shares'] + metrics['saved']) / metrics['reach'] * 100) if metrics['reach'] else 0:.2f}%
"""
    PERFORMANCE_FILE.write_text(existing.rstrip() + entry + "\n", encoding="utf-8")


def main() -> None:
    if not PUBLISHED_FILE.exists():
        print("PUBLISHED.md fehlt – keine Analytics verfügbar.")
        return
    posts = parse_published_posts(PUBLISHED_FILE.read_text(encoding="utf-8"))
    if not posts:
        print("Keine veröffentlichten Beiträge mit gespeicherter Media-ID gefunden.")
        return
    for post in posts:
        metrics = fetch_insights(post["platform"], post["id"])
        if metrics:
            append_snapshot(post, metrics)
        time.sleep(1)
    print("Analytics-Abruf beendet.")


if __name__ == "__main__":
    main()
