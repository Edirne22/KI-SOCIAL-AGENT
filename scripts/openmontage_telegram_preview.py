"""Send a private R2 preview to the configured Telegram owner; never publish.

Approval commands acknowledge editorial review only; no social API is called.
"""
from __future__ import annotations
import os
import re
import requests


def preview_message(preview: dict, social_copy: dict | None = None) -> str:
    url = preview["download_url"]
    seconds = preview["expires_seconds"]
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("HTTPS preview link required")
    if not isinstance(seconds, int) or seconds < 60:
        raise ValueError("Invalid link lifetime")
    message = (
        "🎬 OpenMontage – PRIVATE VORSCHAU\n"
        f"Video herunterladen (Link {seconds // 60} Minuten gültig):\n{url}\n\n"
        "Nur Sichtung, keine Veröffentlichung.\n"
        f"Neuen Link: /montage link neu {preview['media_id']}\n"
        "Keine Veröffentlichung."
    )
    if social_copy is not None:
        if social_copy.get("publication_authorized") is not False:
            raise ValueError("Captions must remain review-only")
        for platform in ("instagram", "facebook"):
            caption = social_copy.get(platform, {}).get("caption", "")
            if not isinstance(caption, str) or not caption.strip():
                raise ValueError("Missing social caption")
            message += f"\n\n{platform.upper()} – TEXTENTWURF:\n{caption}"
    return message


def send_owner_preview(preview: dict, *, token: str | None = None,
                       chat_id: str | None = None, post=None, social_copy: dict | None = None) -> None:
    token = token if token is not None else os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id if chat_id is not None else os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not re.fullmatch(r"-?[0-9]{1,20}", str(chat_id)):
        raise ValueError("Telegram owner configuration missing")
    sender = post or requests.post
    response = sender(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": str(chat_id), "text": preview_message(preview, social_copy=social_copy),
              "disable_web_page_preview": True},
        timeout=20,
    )
    response.raise_for_status()
    if not response.json().get("ok"):
        raise RuntimeError("Telegram rejected private preview")
