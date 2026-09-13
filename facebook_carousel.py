"""Veröffentlicht freigegebene Facebook-Karussells über die Graph API."""
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests

from asset_paths import asset_url

GRAPH_BASE = "https://graph.facebook.com/v24.0"
PUBLISHED_PATH = Path("content/PUBLISHED.md")
REPO_RAW = os.getenv("REPO_RAW", "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/")


def notify(message):
    try:
        from telegram_bot import send_message
        send_message(message)
    except Exception as exc:
        print(f"Telegram-Hinweis nicht gesendet: {exc}")


def request_with_retry(method, url, **kwargs):
    for attempt in range(3):
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            if response.status_code not in (429, 500, 502, 503, 504):
                response.raise_for_status()
                return response
            print(f"Temporärer Graph-API-Fehler {response.status_code}, Versuch {attempt + 1}/3")
        except requests.RequestException as exc:
            if attempt == 2:
                raise
            print(f"Temporärer Graph-API-Fehler: {exc}")
        if attempt < 2:
            time.sleep(5 * (attempt + 1))
    response.raise_for_status()
    return response


def parse_blocks(content):
    pattern = re.compile(r"(^## Facebook Karussell(?: \[GEPOSTET [^\]]+\])?\n.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(content):
        block = match.group(1)
        if "[GEPOSTET " in block or not re.search(r"^Status:\s*FREIGEGEBEN\s*$", block, re.MULTILINE | re.IGNORECASE):
            continue
        claim_token = os.environ.get("PUBLICATION_CLAIM_TOKEN", "")
        if not claim_token or f"Publication-Claim: IN_BEARBEITUNG {claim_token}" not in block:
            continue
        text_match = re.search(r"^Text:\s*(.*?)(?=^Bilder:|\Z)", block, re.MULTILINE | re.DOTALL)
        images_match = re.search(r"^Bilder:\s*\n((?:\s*-\s*[^\n]+\n?)+)", block, re.MULTILINE)
        images = [line.strip()[1:].strip() for line in images_match.group(1).splitlines()] if images_match else []
        yield match, block, (text_match.group(1).strip() if text_match else ""), images


def publish_carousel(caption, images, page_id, token):
    media = []
    for image in images:
        response = request_with_retry("POST", f"{GRAPH_BASE}/{page_id}/photos", data={
            "url": asset_url(image, REPO_RAW),
            "published": "false",
            "access_token": token,
        }).json()
        media.append({"media_fbid": response["id"]})
    result = request_with_retry("POST", f"{GRAPH_BASE}/{page_id}/feed", data={
        "message": caption,
        "attached_media": json.dumps(media),
        "access_token": token,
    }).json()
    return result["id"]


def main():
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    token = os.getenv("FACEBOOK_PAGE_TOKEN")
    if not page_id or not token:
        raise RuntimeError("FACEBOOK_PAGE_ID oder FACEBOOK_PAGE_TOKEN fehlt.")
    if not PUBLISHED_PATH.exists():
        print("PUBLISHED.md nicht gefunden.")
        return

    content = PUBLISHED_PATH.read_text(encoding="utf-8")
    changed = False
    for match, block, caption, images in list(parse_blocks(content)):
        if len(images) < 2:
            notify("⚠️ Facebook-Karussell nicht veröffentlicht: mindestens 2 Bilder erforderlich.")
            print("Karussell übersprungen: weniger als 2 Bilder.")
            continue
        if len(images) > 10:
            notify("⚠️ Facebook-Karussell: mehr als 10 Bilder – nur die ersten 10 werden verwendet.")
            images = images[:10]
        try:
            post_id = publish_carousel(caption, images, page_id, token)
        except Exception as exc:
            notify("⚠️ Facebook-Karussell konnte nicht veröffentlicht werden. Bitte Workflow-Log prüfen.")
            print(f"Karussell-Fehler: {exc}")
            continue
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        updated = re.sub(r"^## Facebook Karussell", f"## Facebook Karussell [GEPOSTET {stamp} | ID: {post_id}]", block, count=1)
        content = content.replace(block, updated, 1)
        changed = True
        print(f"Facebook-Karussell veröffentlicht: {post_id}")

    if changed:
        PUBLISHED_PATH.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
