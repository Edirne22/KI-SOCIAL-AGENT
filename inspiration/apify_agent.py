"""Apify-Hauptquelle für öffentliche Instagram- und Facebook-Inspiration.

Bright Data wird erst als gezielter Fallback verwendet. Es gibt keine Logins,
keine privaten Profile und maximal zehn verwertete Beiträge pro Plattform/Lauf.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

OUT = Path("memory/INSPIRATION_APIFY.md")
DEBUG = Path("memory/INSPIRATION_APIFY_DEBUG.md")
API_ROOT = "https://api.apify.com/v2/acts"
MAX_ITEMS = 10
ACTORS = {
    "instagram": "apify~instagram-profile-scraper",
    # Dieser Actor akzeptiert resultsLimit; die Kostenbremse wirkt damit vor dem Abruf.
    "facebook": "khadinakbar~facebook-posts-scraper",
}


def _write_debug(platform: str, status: str, records: int, detail: str = "") -> None:
    """Schreibt nur technische Metadaten, niemals Token, Header oder Rohdaten."""
    DEBUG.parent.mkdir(parents=True, exist_ok=True)
    old = DEBUG.read_text(encoding="utf-8") if DEBUG.exists() else "# Apify Social Debug\n"
    entry = [
        f"\n## {platform.title()} ({datetime.now():%Y-%m-%d %H:%M})",
        f"- Actor: {ACTORS[platform]}",
        f"- HTTP-Status: {status}",
        f"- Verwertete Beiträge: {records}",
        f"- Hinweis: {detail or 'keine'}",
    ]
    DEBUG.write_text(old.rstrip() + "\n" + "\n".join(entry) + "\n", encoding="utf-8")


def _load_urls(platform: str) -> list[str]:
    """Nutzt optional eigene Apify-Inputs, sonst die bereits vorhandenen öffentlichen Bright-Data-URLs."""
    raw = os.environ.get(f"APIFY_INPUT_{platform.upper()}") or os.environ.get(f"BRIGHTDATA_INPUT_{platform.upper()}", "")
    if not raw:
        return []
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(entries, list):
        return []
    urls: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("url") or entry.get("profile_url") or entry.get("username") or "").strip()
        if value and value not in urls:
            urls.append(value)
    return urls


def _call(actor: str, payload: dict, token: str) -> tuple[list[dict], str, str]:
    try:
        response = requests.post(
            f"{API_ROOT}/{actor}/run-sync-get-dataset-items",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=300,
        )
    except requests.Timeout:
        return [], "Timeout", "Actor antwortete nicht innerhalb von fünf Minuten."
    except requests.RequestException as error:
        return [], type(error).__name__, "Netzwerkfehler beim Actor."
    if not response.ok:
        return [], str(response.status_code), f"Actor lieferte HTTP {response.status_code}."
    try:
        data = response.json()
    except ValueError:
        return [], str(response.status_code), "Actor lieferte kein JSON."
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else [], str(response.status_code), ""


def _handle_from_url(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"https://instagram.com/{value}")
    path = parsed.path.strip("/").split("/")
    return path[0].lstrip("@") if path else value.lstrip("@")


def _as_number(value: object) -> str:
    if isinstance(value, bool) or value in (None, ""):
        return "nicht verfügbar"
    if isinstance(value, (int, float)):
        return str(int(value))
    return str(value)


def _post_url(post: dict) -> str:
    value = post.get("url") or post.get("link") or post.get("permalink") or ""
    if value:
        return str(value)
    shortcode = post.get("shortCode") or post.get("shortcode")
    return f"https://www.instagram.com/p/{shortcode}/" if shortcode else "nicht verfügbar"


def _post_date(post: dict) -> str:
    value = post.get("timestamp") or post.get("takenAtTimestamp") or post.get("date") or post.get("publishedAt") or ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value) if value else "nicht verfügbar"


def _format(platform: str, rows: list[dict]) -> str:
    title = platform.title()
    lines = [f"## {title}"]
    for index, row in enumerate(rows[:MAX_ITEMS], 1):
        if platform == "instagram":
            text = str(row.get("caption") or row.get("text") or row.get("description") or "Instagram-Beitrag")
            url = _post_url(row)
            date = _post_date(row)
            likes = _as_number(row.get("likesCount", row.get("likes", row.get("likeCount"))))
            comments = _as_number(row.get("commentsCount", row.get("comments", row.get("commentCount"))))
            shares = _as_number(row.get("sharesCount", row.get("shareCount")))
        else:
            text = str(row.get("message") or row.get("text") or row.get("content") or "Facebook-Beitrag")
            url = str(row.get("url") or row.get("permalink") or "nicht verfügbar")
            date = str(row.get("timestamp") or row.get("date_posted") or row.get("created_time") or "nicht verfügbar")
            likes = _as_number(row.get("reactions_count", row.get("reactionsCount", row.get("likes"))))
            comments = _as_number(row.get("comments_count", row.get("commentsCount", row.get("comments"))))
            shares = _as_number(row.get("reshare_count", row.get("shares", row.get("shareCount"))))
        lines.extend(
            [
                f"### Datensatz {index}",
                f"- Titel: {text[:500]}",
                f"- Datum: {date}",
                f"- URL: {url}",
                f"- Likes: {likes}",
                f"- Kommentare: {comments}",
                f"- Shares: {shares}",
            ]
        )
    if len(lines) == 1:
        lines.append("- Status: Keine öffentlichen Beiträge verfügbar.")
    return "\n".join(lines)


def _instagram(token: str) -> tuple[list[dict], str]:
    handles = [_handle_from_url(value) for value in _load_urls("instagram")][:MAX_ITEMS]
    if not handles:
        _write_debug("instagram", "nicht konfiguriert", 0, "Keine Profil-URL in APIFY_INPUT_INSTAGRAM oder BRIGHTDATA_INPUT_INSTAGRAM.")
        return [], "Nicht konfiguriert."
    profiles, status, detail = _call(ACTORS["instagram"], {"usernames": handles}, token)
    posts: list[dict] = []
    for profile in profiles:
        recent = profile.get("latestPosts") or profile.get("latest_posts") or []
        if isinstance(recent, list):
            posts.extend(post for post in recent if isinstance(post, dict))
    posts = posts[:MAX_ITEMS]
    _write_debug("instagram", status, len(posts), detail or "Apify ist Hauptquelle; Bright Data wird nur bei fehlenden Datensätzen genutzt.")
    return posts, detail


def _facebook(token: str) -> tuple[list[dict], str]:
    urls = _load_urls("facebook")
    if not urls:
        _write_debug("facebook", "nicht konfiguriert", 0, "Keine Seiten-URL in APIFY_INPUT_FACEBOOK oder BRIGHTDATA_INPUT_FACEBOOK.")
        return [], "Nicht konfiguriert."
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=7)
    payload = {
        # Der Actor begrenzt die abgerufenen Ergebnisse selbst. Das ist wichtiger
        # als ein nachträgliches posts[:MAX_ITEMS], das nur den Bericht begrenzt.
        "startUrls": [{"url": urls[0]}],
        "resultsLimit": MAX_ITEMS,
    }
    posts, status, detail = _call(ACTORS["facebook"], payload, token)
    posts = posts[:MAX_ITEMS]
    _write_debug(
        "facebook",
        status,
        len(posts),
        detail or f"Apify ist Hauptquelle; Actor-Limit: maximal {MAX_ITEMS} Facebook-Beiträge pro Lauf.",
    )
    return posts, detail


def run() -> str:
    token = os.environ.get("APIFY_API_TOKEN", "").strip()
    lines = ["# Inspiration · Apify", "", "- Rolle: Hauptquelle für Instagram und Facebook", "- Limit: maximal 10 Beiträge pro Plattform und Lauf", ""]
    if not token:
        lines.append("APIFY_API_TOKEN fehlt.")
    else:
        for platform, function in (("instagram", _instagram), ("facebook", _facebook)):
            posts, detail = function(token)
            lines.append(_format(platform, posts))
            if detail:
                lines.append(f"- Status: {detail}")
            elif posts:
                lines.append(f"- Status: {len(posts)} öffentliche Beiträge verfügbar.")
            lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return OUT.read_text(encoding="utf-8")


if __name__ == "__main__":
    run()
