"""YouTube-Apify-Fallback für den Inspiration-Agenten.

Nutzt ausschließlich öffentliche Suchergebnisse, keinen Google-API-Key und höchstens
drei Suchbegriffe sowie zehn detaillierte Videos pro Lauf.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import requests

from .search_config import YOUTUBE_MAX_ITEMS, YOUTUBE_SEARCH_QUERIES

OUT = Path("memory/INSPIRATION_YOUTUBE_APIFY.md")
DEBUG = Path("memory/INSPIRATION_YOUTUBE_APIFY_DEBUG.md")
ACTOR = "trysmartapi~youtube-scraper"
API = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items"


def _debug(status: str, operation: str, detail: str, rows: int = 0) -> None:
    """Protokolliert Diagnose-Metadaten, niemals Token oder vollständige Rohdaten."""
    DEBUG.parent.mkdir(parents=True, exist_ok=True)
    old = DEBUG.read_text(encoding="utf-8") if DEBUG.exists() else "# YouTube-Apify-Debug\n"
    entry = (
        f"\n## YouTube Apify ({datetime.now():%Y-%m-%d %H:%M})\n"
        f"- Actor: {ACTOR}\n"
        f"- Operation: {operation}\n"
        f"- HTTP-Status: {status}\n"
        f"- Ergebniszeilen: {rows}\n"
        f"- Details: {detail[:300] or 'keine'}\n"
    )
    DEBUG.write_text(old.rstrip() + entry, encoding="utf-8")


def _call(token: str, payload: dict) -> list[dict]:
    try:
        response = requests.post(
            API,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json=payload,
            timeout=300,
        )
    except requests.RequestException as error:
        _debug(type(error).__name__, str(payload.get("operation", "unbekannt")), "Netzwerkfehler")
        return []
    if not response.ok:
        _debug(str(response.status_code), str(payload.get("operation", "unbekannt")), "Actor-Aufruf fehlgeschlagen")
        return []
    try:
        data = response.json()
    except ValueError:
        _debug(str(response.status_code), str(payload.get("operation", "unbekannt")), "Ungültige JSON-Antwort")
        return []
    rows = [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []
    _debug(str(response.status_code), str(payload.get("operation", "unbekannt")), "erfolgreich", len(rows))
    return rows


def _value(item: dict, key: str) -> str:
    value = item.get(key)
    return str(value) if value not in (None, "", [], {}) else "nicht verfügbar"


def run() -> str:
    token = os.environ.get("APIFY_API_TOKEN", "")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not token:
        text = "# Inspiration · YouTube Apify\n\nNicht konfiguriert: APIFY_API_TOKEN fehlt.\n"
        OUT.write_text(text, encoding="utf-8")
        _debug("–", "–", "APIFY_API_TOKEN fehlt")
        return text

    published_after = (datetime.utcnow() - timedelta(days=7)).date().isoformat()
    search_rows = _call(token, {
        "operation": "search_videos",
        "queries": list(YOUTUBE_SEARCH_QUERIES[:3]),
        "order": "date",
        "publishedAfter": published_after,
        "maxItems": YOUTUBE_MAX_ITEMS,
    })
    urls: list[str] = []
    for item in search_rows:
        url = str(item.get("url", "")).strip()
        if url.startswith("http") and url not in urls:
            urls.append(url)
        if len(urls) >= YOUTUBE_MAX_ITEMS:
            break
    if not urls:
        text = "# Inspiration · YouTube Apify\n\nKeine öffentlichen YouTube-Treffer im Zeitraum.\n"
        OUT.write_text(text, encoding="utf-8")
        return text

    detail_rows = _call(token, {"operation": "video_details", "videos": urls})
    details_by_url = {str(item.get("url", "")): item for item in detail_rows if item.get("url")}
    merged = []
    for search in search_rows:
        url = str(search.get("url", ""))
        if url in urls and url not in {row["url"] for row in merged}:
            merged.append({**search, **details_by_url.get(url, {})})

    lines = ["# Inspiration · YouTube Apify", "", f"Suchzeitraum ab: {published_after}", f"Suchbegriffe: {', '.join(YOUTUBE_SEARCH_QUERIES[:3])}", f"Videos: {len(merged)}", ""]
    for index, item in enumerate(merged, 1):
        lines += [
            f"### Datensatz {index}",
            f"- Titel: {_value(item, 'title')[:300]}",
            f"- Kanal: {_value(item, 'channelTitle')[:200]}",
            f"- Datum: {_value(item, 'publishedAt')}",
            f"- URL: {_value(item, 'url')}",
            f"- Views: {_value(item, 'viewCount')}",
            f"- Likes: {_value(item, 'likeCount')}",
            f"- Kommentare: {_value(item, 'commentCount')}",
        ]
    text = "\n".join(lines) + "\n"
    OUT.write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    run()
