"""Send a private R2 preview to the configured Telegram owner; never publish.

Approval commands acknowledge editorial review only; no social API is called.
"""
from __future__ import annotations
import os
import re
import requests


def preview_message(preview: dict) -> str:
    url = preview["download_url"]
    seconds = preview["expires_seconds"]
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("HTTPS preview link required")
    if not isinstance(seconds, int) or seconds < 60:
        raise ValueError("Invalid link lifetime")
    return (
        "🎬 OpenMontage – PRIVATE VORSCHAU\n"
        f"Video herunterladen (Link {seconds // 60} Minuten gültig):\n{url}\n\n"
        "Nur Sichtung, keine Veröffentlichung.\n"
        f"Neuen Link: /montage link neu {preview['media_id']}\n"
        "Keine Veröffentlichung."
    )


def send_owner_preview(preview: dict, *, token: str | None = None,
                       chat_id: str | None = None, post=None) -> None:
    token = token if token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id if chat_id is not None else os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not re.fullmatch(r"-?[0-9]{1,20}", str(chat_id)):
        raise ValueError("Telegram owner configuration missing")
    sender = post or requests.post
    response = sender(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": str(chat_id), "text": preview_message(preview),
              "disable_web_page_preview": True},
        timeout=20,
    )
    response.raise_for_status()
    if not response.json().get("ok"):
        raise RuntimeError("Telegram rejected private preview")
