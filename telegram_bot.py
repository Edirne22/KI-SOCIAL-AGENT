"""Kleine, sichere Telegram-Bot-Hilfe für die Content-Freigabe."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests

TELEGRAM_API = "https://api.telegram.org"


def _get_bot_token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN fehlt. Hinterlege den Bot-Token als GitHub Secret, nicht in einer Datei."
        )
    return token


def get_chat_id() -> str:
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat_id:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID fehlt. Hinterlege die freigegebene Bülent-Chat-ID als GitHub Secret."
        )
    return chat_id


def _request(method: str, data: dict[str, Any] | None = None, files: Any = None) -> dict[str, Any]:
    token = _get_bot_token()
    try:
        response = requests.post(
            f"{TELEGRAM_API}/bot{token}/{method}",
            data=data,
            files=files,
            timeout=30,
        )
    except requests.RequestException as error:
        raise RuntimeError(f"Telegram-Anfrage fehlgeschlagen: {error}") from error

    if not response.ok:
        raise RuntimeError(f"Telegram-Anfrage fehlgeschlagen (HTTP {response.status_code}).")

    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API meldet einen Fehler bei {method}.")
    return payload


def send_message(text: str) -> dict[str, Any]:
    """Sendet eine Textnachricht in den freigegebenen Telegram-Chat."""
    return _request(
        "sendMessage",
        {"chat_id": get_chat_id(), "text": text},
    )


def send_photo(image_path: str | Path, caption: str = "") -> dict[str, Any]:
    """Sendet ein lokales Bild mit optionaler Beschriftung."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Bilddatei nicht gefunden: {path}")

    with path.open("rb") as photo:
        return _request(
            "sendPhoto",
            {"chat_id": get_chat_id(), "caption": caption},
            {"photo": photo},
        )


def get_updates(offset: int | None = None) -> list[dict[str, Any]]:
    """Holt neue Bot-Nachrichten. Mit Offset werden ältere Updates bestätigt."""
    data: dict[str, Any] = {"timeout": 0}
    if offset is not None:
        data["offset"] = offset

    payload = _request("getUpdates", data)
    return payload.get("result", [])
