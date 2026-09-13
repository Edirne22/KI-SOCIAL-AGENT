"""Veröffentlicht freigegebene Instagram-Karussells über die Graph API."""
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
    pattern = re.compile(r"(^## Instagram Karussell(?: \[GEPOSTET [^\]]+\])?\n.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(content):
        block = match.group(1)
        if "[GEPOSTET " in block or not re.search(r"^Status:\s*FREIGEGEBEN\s*$", block, re.MULTILINE | re.IGNORECASE):
            continue
        claim_token = os.environ.get("PUBLICATION_CLAIM_TOKEN", "")
        if not claim_token or f"Publication-Claim: IN_BEARBEITUNG {claim_token}" not in block:
            continue
        text_match = re.search(r"^Text:\s*(.*?)(?=^(?:Bilder|Quelle|Medienstatus|Nutzungsrecht):|\Z)", block, re.MULTILINE | re.DOTALL)
        images_match = re.search(r"^Bilder:\s*\n((?:\s*-\s*[^\n]+\n?)+)", block, re.MULTILINE)
        images = [line.strip()[1:].strip() for line in images_match.group(1).splitlines()] if images_match else []
        yield match, block, (text_match.group(1).strip() if text_match else ""), images


def wait_for_container(container_id, token):
    url = f"{GRAPH_BASE}/{container_id}"
    for _ in range(24):
        data = request_with_retry("GET", url, params={"fields": "status_code", "access_token": token}).json()
        status = data.get("status_code", "")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Karussell-Container fehlgeschlagen: {status}")
        time.sleep(5)
    raise TimeoutError("Karussell-Container wurde nicht rechtzeitig fertig.")


def publish_carousel(caption, images, user_id, token):
    child_ids = []
    for image in images:
        payload = {
            "image_url": asset_url(image, REPO_RAW),
            "is_carousel_item": "true",
            "access_token": token,
        }
        data = request_with_retry("POST", f"{GRAPH_BASE}/{user_id}/media", data=payload).json()
        child_ids.append(data["id"])

    parent = request_with_retry("POST", f"{GRAPH_BASE}/{user_id}/media", data={
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "caption": caption,
        "access_token": token,
    }).json()
    container_id = parent["id"]
    wait_for_container(container_id, token)
    result = request_with_retry("POST", f"{GRAPH_BASE}/{user_id}/media_publish", data={
        "creation_id": container_id,
        "access_token": token,
    }).json()
    return result["id"]


def main():
    user_id = os.getenv("INSTAGRAM_USER_ID")
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not user_id or not token:
        raise RuntimeError("INSTAGRAM_USER_ID oder INSTAGRAM_ACCESS_TOKEN fehlt.")
    if not PUBLISHED_PATH.exists():
        print("PUBLISHED.md nicht gefunden.")
        return

    content = PUBLISHED_PATH.read_text(encoding="utf-8")
    changed = False
    for match, block, caption, images in list(parse_blocks(content)):
        if len(images) < 2:
            notify("⚠️ Instagram-Karussell nicht veröffentlicht: mindestens 2 Bilder erforderlich.")
            print("Karussell übersprungen: weniger als 2 Bilder.")
            continue
        if len(images) > 10:
            notify("⚠️ Instagram-Karussell: mehr als 10 Bilder – nur die ersten 10 werden verwendet.")
            images = images[:10]
        try:
            media_id = publish_carousel(caption, images, user_id, token)
        except Exception as exc:
            notify("⚠️ Instagram-Karussell konnte nicht veröffentlicht werden. Bitte Workflow-Log prüfen.")
            print(f"Karussell-Fehler: {exc}")
            continue
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        updated = re.sub(r"^## Instagram Karussell", f"## Instagram Karussell [GEPOSTET {stamp} | ID: {media_id}]", block, count=1)
        content = content.replace(block, updated, 1)
        changed = True
        print(f"Instagram-Karussell veröffentlicht: {media_id}")

    if changed:
        PUBLISHED_PATH.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
