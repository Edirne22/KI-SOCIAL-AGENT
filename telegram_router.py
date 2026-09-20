"""Einziger Telegram-Poller/Routing-Einstiegspunkt.

Nur dieser Router konsumiert getUpdates im Zeitplan. MotoGP erhält exakt das
bereits gelesene Update als Argumente. Unbekannte Nachrichten werden still
bestätigt, damit der alte allgemeine Receiver keine irreführende Freigabe-Hilfe
mehr auf beliebige Nachrichten sendet.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import requests

from telegram_bot import get_chat_id, get_updates, send_message
from vision_router import VisionRouter


def _ack(update_id: int) -> None:
    get_updates(offset=update_id + 1)


def _is_photo_message(update: dict) -> bool:
    msg = update.get("message") or {}
    photo = msg.get("photo")
    document = msg.get("document") or {}
    return (
        (isinstance(photo, list) and bool(photo))
        or (
            isinstance(document, dict)
            and str(document.get("mime_type", "")).startswith("image/")
        )
    )


def _download_telegram_photo(photo_list: list, document: dict | None = None) -> bytes | None:
    document = document or {}
    if photo_list:
        file_id = photo_list[-1].get("file_id")
    else:
        file_id = document.get("file_id")
    if not file_id:
        return None
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ROUTER: TELEGRAM_BOT_TOKEN fehlt.")
        return None
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getFile",
            params={"file_id": file_id},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        file_path = (data.get("result") or {}).get("file_path")
        if not data.get("ok") or not file_path:
            return None
        image_response = requests.get(
            f"https://api.telegram.org/file/bot{token}/{file_path}",
            timeout=60,
        )
        image_response.raise_for_status()
        return image_response.content or None
    except (requests.RequestException, ValueError, TypeError) as e:
        print(f"ROUTER: Telegram-Bilddownload fehlgeschlagen: {e}")
        return None


def _handle_photo(update: dict, chat: str) -> bool:
    msg = update.get("message") or {}
    photo = msg.get("photo") or []
    document = msg.get("document") or {}
    caption = msg.get("caption")
    normalized = " ".join(caption.strip().lower().split()) if isinstance(caption, str) else ""

    if normalized == "/ocr":
        mode = "ocr"
    elif normalized == "/omni":
        mode = "omni"
    else:
        mode = "general"

    image_bytes = _download_telegram_photo(photo, document)
    if not image_bytes:
        send_message("❌ Vision-Fehler: Bild konnte nicht von Telegram geladen werden.")
        return False

    try:
        result = VisionRouter().analyze(image_bytes, mode=mode)
    except Exception as e:
        send_message(f"❌ Vision-Fehler: {e}")
        return False

    if result.get("error"):
        send_message(f"❌ Vision-Fehler: {result['error']}")
        return False

    description = result.get("description")
    if not isinstance(description, str):
        # OCR liefert laut bestehendem vision_router.py text/tables statt description.
        description = result.get("text", "")
        tables = result.get("tables")
        if tables:
            description += f"\n\nTabellen: {tables}"

    send_message(
        f"🔍 Vision-Analyse:\n\n{description}\n\n"
        f"Model: {result.get('model_used', 'unbekannt')}"
    )
    return True


def _is_general_command(text: str) -> bool:
    n = " ".join(text.strip().lower().split())
    if n in {"alle", "✅", "nein", "❌", "watchlist", "liste", "track", "experiment", "funnel", "growth", "competitors", "wettbewerber", "inspiration", "race", "viral", "follow-analyse", "go"}:
        return True
    if re.fullmatch(r"[1-3](?:\s*,\s*[1-3])*", n):
        return True
    prefixes = (
        "auto-track:", "autotrack:", "auto track:", "karussell:", "karussell ",
        "experiment:", "trend:", "trend ", "track:", "track ", "deal:", "deal ",
        "deal-test:", "suche:", "suche ", "stop:", "stop ", "beenden:", "beenden ",
        "erledigt:", "erledigt ", "gekauft:", "gekauft ", "verify:", "verify "
    )
    return n.startswith(prefixes)


def main() -> None:
    allowed = str(get_chat_id())
    updates = sorted(get_updates(), key=lambda x: x.get("update_id", 0))
    if not updates:
        print("ROUTER: Keine neuen Telegram-Updates.")
        return

    for upd in updates:
        uid = upd.get("update_id")
        msg = upd.get("message") or {}
        chat = str((msg.get("chat") or {}).get("id", ""))
        text = msg.get("text")
        if not isinstance(uid, int):
            continue
        if _is_photo_message(upd):
            if chat != allowed:
                _ack(uid)
                return
            _handle_photo(upd, chat)
            _ack(uid)
            return
        if chat != allowed or not isinstance(text, str):
            print(f"ROUTER: Update {uid} nicht aus erlaubtem Text-Chat; bestätigt/übersprungen.")
            _ack(uid)
            return

        normalized = " ".join(text.strip().lower().split())
        if normalized in {"/help", "/hilfe", "hilfe"}:
            send_message(
                "🤖 Verfügbare Kommandos:\n\n"
                "BILDER:\n"
                "/vision – Bild analysieren (Standard)\n"
                "/ocr – Text aus Bild extrahieren\n"
                "/omni – Multimodale Analyse\n"
                "(Bild einfach mit Caption senden)\n\n"
                "MOTOGP:\n"
                "motogp 2,4 – Rennen 2 und 4 freigeben\n"
                "motogp ✅ – alle freigeben\n"
                "motogp ❌ – alle ablehnen\n\n"
                "ALLGEMEIN:\n"
                "alle – alle Freigaben\n"
                "liste – offene Aufgaben\n"
                "watchlist – Watchlist anzeigen\n"
                "follow-analyse – Follower-Analyse\n"
                "race – Race-Kalender\n"
                "inspiration – Inspiration-Posts\n\n"
                "SYSTEM:\n"
                "/help – Diese Hilfe"
            )
            _ack(uid)
            return
        if normalized in {"/vision", "/ocr", "/omni"}:
            send_message("Bitte sende ein Bild mit dem Befehl /vision, /ocr oder /omni.")
            _ack(uid)
            return
        if normalized.startswith("motogp ") or normalized in {"motogp", "motogp ✅", "motogp ❌"}:
            print(f"ROUTER: Update {uid} -> MotoGP Approval (atomare Übergabe)")
            result = subprocess.run(
                [sys.executable, "-u", "motogp_telegram_receive.py", str(uid), chat, text],
                check=False,
            )
            if result.returncode == 2:
                # Receiver hatte nichts zu tun (bereits verarbeitet oder Kommando unbekannt).
                # Update trotzdem quittieren, damit es nicht in der Queue klebt.
                print(f"ROUTER: MotoGP-Update {uid} unverarbeitet (Exit 2); quittiert.")
                _ack(uid)
                return
            if result.returncode != 0:
                raise RuntimeError(f"MotoGP-Receiver fehlgeschlagen (Exit {result.returncode}); Update bleibt offen.")
            _ack(uid)
            print(f"ROUTER: MotoGP Update {uid} erfolgreich verarbeitet und bestätigt.")
            return

        if _is_general_command(text):
            print(f"ROUTER: Update {uid} -> allgemeiner Telegram Receiver")
            result = subprocess.run(
                [sys.executable, "-u", "telegram_receive.py", str(uid), chat, text],
                check=False,
            )
            if result.returncode == 2:
                print(f"ROUTER: Allgemeines Update {uid} unverarbeitet (Exit 2); quittiert.")
                _ack(uid)
                return
            if result.returncode != 0:
                raise RuntimeError(f"Allgemeiner Telegram-Receiver fehlgeschlagen (Exit {result.returncode}).")
            _ack(uid)
            print(f"ROUTER: Allgemeines Update {uid} erfolgreich verarbeitet und bestätigt.")
            return

        # FIX 3: freundliche Antwort statt stille Bestätigung
        print(f"ROUTER: Update {uid} unbekannt; sende freundliche Hilfe.")
        try:
            send_message(
                f"🤖 Kommando nicht erkannt: {text[:40]!r}\n"
                "Beispiele: motogp 2,4 · motogp ✅ · motogp ❌ · alle · liste"
            )
        except Exception as e:
            print(f"ROUTER: Hilfe senden fehlgeschlagen: {e}")
        _ack(uid)
        return

    print("ROUTER: Kein verarbeitbares Update gefunden.")


if __name__ == "__main__":
    main()
