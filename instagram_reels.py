"""Veröffentlicht ausschließlich freigegebene Instagram-Reels aus PUBLISHED.md."""

from __future__ import annotations

import os
import re
import time
from datetime import datetime

import requests

REPO_RAW = "https://raw.githubusercontent.com/Edirne22/KI-SOCIAL-AGENT/main/"
GRAPH_API = "https://graph.instagram.com/v23.0"
TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
MAX_RETRIES = 3


def request_with_retry(method: str, url: str, **kwargs) -> requests.Response | None:
    """Wiederholt nur vorübergehende Netzwerk- und API-Fehler."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(method, url, timeout=60, **kwargs)
        except requests.RequestException as error:
            if attempt == MAX_RETRIES:
                print(f"Instagram-Anfrage fehlgeschlagen: {error}")
                return None
            print(f"Temporärer Netzwerkfehler, Wiederholung {attempt}/{MAX_RETRIES}...")
            time.sleep(5 * attempt)
            continue

        if response.status_code == 200:
            return response
        if response.status_code in TRANSIENT_STATUS_CODES and attempt < MAX_RETRIES:
            print(f"Temporärer API-Fehler {response.status_code}, Wiederholung {attempt}/{MAX_RETRIES}...")
            time.sleep(5 * attempt)
            continue

        print(f"Instagram API-Fehler ({response.status_code}): {response.text[:300]}")
        return None
    return None


def find_reel_block(content: str) -> tuple[str | None, str | None, str | None]:
    """Findet den ersten ausdrücklich freigegebenen Reel-Block mit fertigem Video."""
    pattern = r"^## (?:Instagram Reel|Reel)(?:\s+\[[^\]]+\])?\s*\n(.*?)(?=^## |\Z)"
    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        block = match.group(0)
        body = match.group(1)
        if "[GEPOSTET" in block or not re.search(r"(?m)^Status:\s*FREIGEGEBEN\s*$", body):
            continue

        video_match = re.search(r"(?m)^Video:\s*(\S+)", body)
        text_match = re.search(r"(?ms)^Text:\s*(.+?)(?=^Video:|\Z)", body)
        if not video_match or not text_match:
            continue

        video_file = video_match.group(1).strip()
        if video_file.lower() == "auto":
            print("Reel wartet noch auf Video-Generierung.")
            continue
        return text_match.group(1).strip(), video_file, block
    return None, None, None


def create_reel_container(ig_user_id: str, token: str, video_url: str, caption: str) -> str | None:
    response = request_with_retry(
        "POST",
        f"{GRAPH_API}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        },
    )
    return response.json().get("id") if response else None


def wait_for_container(creation_id: str, token: str, max_wait: int = 300) -> bool:
    """Wartet, bis Instagram die Videoverarbeitung abgeschlossen hat."""
    url = f"{GRAPH_API}/{creation_id}"
    for _ in range(max_wait // 5):
        response = request_with_retry(
            "GET",
            url,
            params={"fields": "status_code", "access_token": token},
        )
        if response:
            status = response.json().get("status_code")
            if status == "FINISHED":
                return True
            if status in {"ERROR", "EXPIRED"}:
                print(f"Reel-Container nicht verarbeitbar: {status}")
                return False
        time.sleep(5)
    print("Zeitlimit bei der Reel-Verarbeitung erreicht.")
    return False


def publish_reel(ig_user_id: str, token: str, creation_id: str) -> str | None:
    response = request_with_retry(
        "POST",
        f"{GRAPH_API}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
    )
    return response.json().get("id") if response else None


def mark_block(content: str, block: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    updated_block = re.sub(
        r"^## (Instagram Reel|Reel)(?:\s+\[[^\]]+\])?",
        lambda match: f"## {match.group(1)} [GEPOSTET {timestamp}]",
        block,
        count=1,
        flags=re.MULTILINE,
    )
    return content.replace(block, updated_block, 1)


def main() -> None:
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    if not ig_user_id or not token:
        raise RuntimeError("INSTAGRAM_USER_ID oder INSTAGRAM_ACCESS_TOKEN fehlt als GitHub Secret.")

    with open("content/PUBLISHED.md", "r", encoding="utf-8") as handle:
        content = handle.read()

    caption, video_file, block = find_reel_block(content)
    if not block:
        print("Kein freigegebenes Instagram Reel mit fertigem Video gefunden.")
        return

    video_url = REPO_RAW + video_file
    print(f"Freigegebenes Reel gefunden: {video_file}")
    creation_id = create_reel_container(ig_user_id, token, video_url, caption)
    if not creation_id:
        raise RuntimeError("Reel-Container konnte nicht erstellt werden.")

    print(f"Reel-Container {creation_id} erstellt. Warte auf Verarbeitung...")
    if not wait_for_container(creation_id, token):
        raise RuntimeError("Reel-Container wurde nicht fertig verarbeitet.")

    post_id = publish_reel(ig_user_id, token, creation_id)
    if not post_id:
        raise RuntimeError("Instagram hat das Reel nicht veröffentlicht.")

    with open("content/PUBLISHED.md", "w", encoding="utf-8") as handle:
        handle.write(mark_block(content, block))
    print(f"Instagram Reel veröffentlicht: {post_id}")


if __name__ == "__main__":
    main()
