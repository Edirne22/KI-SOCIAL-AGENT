"""Temporäres Meta-Engagement-Polling bis zum VPS/Webhook.

Liest ausschließlich öffentliche Kommentare über die vorhandenen Meta-Zugänge,
übergibt neue Events an Agent 17/18 und informiert Bülent per Telegram.
Keine Antworten, Likes, Follows oder Publisher-Aufrufe.
"""
from __future__ import annotations

import os
import requests

import instagram_engagement
import facebook_engagement
from telegram_bot import send_message

IG_API = "https://graph.instagram.com/v23.0"
FB_API = "https://graph.facebook.com/v26.0"


def _get(url: str, token: str, **params):
    params["access_token"] = token
    r = requests.get(url, params=params, timeout=45)
    if r.status_code != 200:
        raise RuntimeError(f"Meta API {r.status_code}: {r.text[:500]}")
    return r.json()


def poll_instagram() -> tuple[int, list[str]]:
    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not user_id or not token:
        return 0, ["Instagram: Secrets fehlen – übersprungen."]

    created = 0
    notes: list[str] = []
    media = _get(f"{IG_API}/{user_id}/media", token, fields="id,timestamp", limit=50).get("data", [])
    for item in media:
        media_id = str(item.get("id") or "")
        if not media_id:
            continue
        try:
            comments = _get(
                f"{IG_API}/{media_id}/comments",
                token,
                fields="id,text,username,timestamp",
                limit=100,
            ).get("data", [])
        except RuntimeError as exc:
            notes.append(f"Instagram Media {media_id}: {exc}")
            continue
        for c in comments:
            event = instagram_engagement.ingest({
                "event_id": c.get("id"),
                "event_type": "comment",
                "username": c.get("username"),
                "media_id": media_id,
                "text": c.get("text"),
                "timestamp": c.get("timestamp"),
            })
            if event.get("status") == "DUPLICATE":
                continue
            created += 1
            send_message(
                f"📩 Instagram {event['ticket_id']} | {event['category']}\n"
                f"@{event.get('username') or 'unbekannt'}: {event.get('text','')[:500]}\n\n"
                f"Kommandos: info {event['ticket_id']} · ändern {event['ticket_id']} <Text> · ignorieren {event['ticket_id']}"
            )
    return created, notes


def poll_facebook() -> tuple[int, list[str]]:
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "").strip()
    token = os.environ.get("FACEBOOK_PAGE_TOKEN", "").strip()
    if not page_id or not token:
        return 0, ["Facebook: Secrets fehlen – übersprungen."]

    created = 0
    notes: list[str] = []
    posts = _get(f"{FB_API}/{page_id}/feed", token, fields="id,created_time", limit=50).get("data", [])
    for post in posts:
        post_id = str(post.get("id") or "")
        if not post_id:
            continue
        try:
            comments = _get(
                f"{FB_API}/{post_id}/comments",
                token,
                fields="id,message,from,created_time",
                limit=100,
            ).get("data", [])
        except RuntimeError as exc:
            notes.append(f"Facebook Post {post_id}: {exc}")
            continue
        for c in comments:
            actor = c.get("from") or {}
            event = facebook_engagement.ingest({
                "event_id": c.get("id"),
                "event_type": "comment",
                "actor_name": actor.get("name"),
                "post_id": post_id,
                "text": c.get("message"),
                "timestamp": c.get("created_time"),
            })
            if event.get("status") == "DUPLICATE":
                continue
            created += 1
            send_message(
                f"📩 Facebook {event['ticket_id']} | {event['category']}\n"
                f"{event.get('actor_name') or 'unbekannt'}: {event.get('text','')[:500]}\n\n"
                f"Kommandos: info {event['ticket_id']} · ändern {event['ticket_id']} <Text> · ignorieren {event['ticket_id']}"
            )
    return created, notes


def main() -> int:
    failures = []
    total = 0
    for name, fn in (("Instagram", poll_instagram), ("Facebook", poll_facebook)):
        try:
            count, notes = fn()
            total += count
            print(f"{name}: {count} neue Interaktionen.")
            for note in notes:
                print("WARNUNG:", note)
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            print("FEHLER:", failures[-1])

    print(f"Engagement-Polling abgeschlossen: {total} neue Interaktionen.")
    if failures:
        send_message("⚠️ Engagement-Polling teilweise fehlgeschlagen:\n" + "\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
