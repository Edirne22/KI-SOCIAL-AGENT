"""Einziger Telegram-Poller/Routing-Einstiegspunkt.

Nur dieser Router konsumiert getUpdates im Zeitplan. MotoGP erhält exakt das
bereits gelesene Update als Argumente. Unbekannte Nachrichten werden still
bestätigt, damit der alte allgemeine Receiver keine irreführende Freigabe-Hilfe
mehr auf beliebige Nachrichten sendet.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from telegram_bot import get_chat_id, get_updates, send_message, send_photo
from vision_router import VisionRouter
import pending_instagram as pi
import instagram_engagement as instagram_engagement
import facebook_engagement as facebook_engagement
from generate_agnes_media import agnes_generate_image, save_bytes
from instagram_publish import process_image_for_instagram, create_container, publish as ig_publish_container, wait as ig_wait
from asset_paths import asset_url, RAW_BASE

TELEGRAM_LAST_UPDATE_FILE = Path("memory/TELEGRAM_LAST_UPDATE_ID")

def _read_last_update_id() -> int | None:
    if not TELEGRAM_LAST_UPDATE_FILE.exists():
        return None
    try:
        return int(TELEGRAM_LAST_UPDATE_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None

def _write_last_update_id(update_id: int) -> None:
    TELEGRAM_LAST_UPDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TELEGRAM_LAST_UPDATE_FILE.write_text(str(update_id) + "\n", encoding="utf-8")


def _ack(update_id: int) -> None:
    get_updates(offset=update_id + 1)
    _write_last_update_id(update_id)


def _append_vision_log(entry: dict) -> None:
    try:
        path = Path("memory/VISION_LOG.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"ROUTER: Vision-Log konnte nicht geschrieben werden: {e}")


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
        error_message = "Bild konnte nicht von Telegram geladen werden."
        _append_vision_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "telegram",
            "mode": mode,
            "model": None,
            "result": None,
            "tables_present": False,
            "error": error_message,
        })
        send_message(f"❌ Vision-Fehler: {error_message}")
        return False

    try:
        result = VisionRouter().analyze(image_bytes, mode=mode)
    except Exception as e:
        error_message = str(e)
        _append_vision_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "telegram",
            "mode": mode,
            "model": None,
            "result": None,
            "tables_present": False,
            "error": error_message,
        })
        send_message(f"❌ Vision-Fehler: {error_message}")
        return False

    if result.get("error"):
        error_message = str(result["error"])
        _append_vision_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "telegram",
            "mode": mode,
            "model": None,
            "result": None,
            "tables_present": False,
            "error": error_message,
        })
        send_message(f"❌ Vision-Fehler: {error_message}")
        return False

    description = result.get("description")
    if not isinstance(description, str):
        # OCR liefert laut bestehendem vision_router.py text/tables statt description.
        description = result.get("text", "")
        tables = result.get("tables")
        if tables:
            description += f"\n\nTabellen: {tables}"

    _append_vision_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "telegram",
        "mode": mode,
        "model": result.get("model_used"),
        "result": result.get("description") or result.get("text", ""),
        "tables_present": bool(result.get("tables")),
        "error": None,
    })

    send_message(
        f"🔍 Vision-Analyse:\n\n{description}\n\n"
        f"Model: {result.get('model_used', 'unbekannt')}"
    )
    return True


def _is_general_command(text: str) -> bool:
    n = " ".join(text.strip().lower().split()).lstrip("/")
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


def _publish_instagram_pending(item: dict) -> bool:
    """Publishes a pending item directly to Instagram and updates PUBLISHED.md status to GEPOSTET."""
    batch_id = item.get("batch_id")
    auswahl = item.get("auswahl")
    titel = item.get("titel", "")
    text = item.get("text", "")
    image_file = item.get("bild_pfad", "")

    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    published_file = Path("content/PUBLISHED.md")
    content = published_file.read_text(encoding="utf-8") if published_file.exists() else ""

    post_id = None
    if ig_user_id and token and image_file and Path(image_file).exists():
        try:
            processed_img = process_image_for_instagram(image_file)
            img_url = asset_url(processed_img, RAW_BASE)
            cid = create_container(ig_user_id, token, img_url, text)
            if cid and ig_wait(cid, token):
                post_id = ig_publish_container(ig_user_id, token, cid)
        except Exception as e:
            print(f"ROUTER: Direct Instagram post failed: {e}")

    if not post_id:
        print(f"ROUTER: Instagram-Veröffentlichung fehlgeschlagen für {titel}; Pending bleibt erhalten.")
        send_message(f"❌ Instagram NICHT gepostet: {titel}\nVeröffentlichung fehlgeschlagen. Freigabe bleibt erhalten.")
        return False

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    pattern = r"(## Instagram\s*\n(.*?)(?=\n## |\Z))"
    updated_content = content
    found = False
    for match in re.finditer(pattern, content, re.DOTALL):
        block = match.group(1)
        body = match.group(2)
        batch_matches = re.search(
            rf"(?mi)^Racing-Batch-ID:\s*{re.escape(str(batch_id))}\s*$",
            body,
        )
        selection_matches = re.search(
            rf"(?mi)^MotoGP-Auswahl:\s*{re.escape(str(auswahl))}\s*$",
            body,
        )
        if batch_matches and selection_matches:
            found = True
            new_block = re.sub(
                r"^## Instagram(?:\s+\[[^\]]+\])?",
                f"## Instagram [GEPOSTET {timestamp} | ID: {post_id}]",
                block,
                count=1,
                flags=re.MULTILINE,
            )
            new_block = re.sub(
                r"(?mi)^Status:\s*(?:BILD_GENERIERT|FREIGEGEBEN)\s*$",
                "Status: GEPOSTET",
                new_block,
            )
            updated_content = updated_content.replace(block, new_block, 1)

    if not found:
        print(
            "ROUTER: Instagram wurde bei Meta veröffentlicht, aber der passende "
            f"PUBLISHED.md-Block fehlt: batch={batch_id} auswahl={auswahl} media_id={post_id}"
        )
        send_message(
            f"⚠️ Instagram bei Meta gepostet (Media-ID: {post_id}), aber lokaler "
            f"Status konnte nicht aktualisiert werden: {titel}"
        )
        return False

    published_file.write_text(updated_content, encoding="utf-8")
    pi.remove_pending(batch_id, auswahl)
    send_message(f"✅ Instagram gepostet: {titel}\nMeta-Media-ID: {post_id}")
    return True


INSTAGRAM_APPROVE_SYNONYMS = {
    "bild ✅",
    "✅",
    "bild posten",
    "posten",
    "ok",
    "freigegeben",
    "freigeben zum posten",
    "freigeben",
    "ja",
}

INSTAGRAM_REJECT_SYNONYMS = {
    "bild ❌",
    "❌",
    "ablehnen",
    "neu",
    "neu generieren",
    "nein",
}


def _get_bild_command_action(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    n = " ".join(text.strip().lower().split()).lstrip("/")
    if n in INSTAGRAM_APPROVE_SYNONYMS:
        return "✅"
    if n in INSTAGRAM_REJECT_SYNONYMS:
        return "❌"
    return None


def _handle_bild_command(text_or_action: str) -> bool:
    action = (
        text_or_action
        if text_or_action in {"✅", "❌"}
        else _get_bild_command_action(text_or_action)
    )
    if not action:
        return False

    pending_item = pi.get_latest_pending()
    if not pending_item:
        send_message("ℹ️ Keine ausstehenden Instagram-Bilder zur Freigabe vorhanden.")
        return True

    batch_id = pending_item.get("batch_id")
    auswahl = pending_item.get("auswahl")
    titel = pending_item.get("titel", "")
    prompt = pending_item.get("prompt_fuer_agnes", "")
    img_path = pending_item.get("bild_pfad", "")

    if action == "✅":
        _publish_instagram_pending(pending_item)
        return True

    # action == "❌" -> Neu generieren
    print(f"ROUTER: Bild-Ablehnung ('❌') empfangen. Regeneriere Bild für {titel}...")
    try:
        new_bytes = agnes_generate_image(prompt)
        if new_bytes:
            save_bytes(new_bytes, img_path)
            print(f"ROUTER: Neues Agnes-Bild gespeichert unter {img_path}")
    except Exception as e:
        print(f"ROUTER: Agnes Neugenerierung Exception: {e}")

    caption = (
        f"🔄 Neues Bild generiert für: {titel}\n"
        "Antworte mit bild ✅ oder bild ❌ (oder ok/neu)"
    )
    try:
        send_photo(img_path, caption=caption)
    except Exception as e:
        print(f"ROUTER: send_photo bei Neugenerierung fehlgeschlagen: {e}")

    return True


def main() -> None:
    allowed = str(get_chat_id())
    last_update_id = _read_last_update_id()
    if last_update_id is None:
        baseline = sorted(get_updates(), key=lambda x: x.get("update_id", 0))
        ids = [x.get("update_id") for x in baseline if isinstance(x.get("update_id"), int)]
        baseline_id = max(ids) if ids else 0
        _write_last_update_id(baseline_id)
        if ids:
            get_updates(offset=baseline_id + 1)
        print("ROUTER: First-Run Telegram-Offset initialisiert; keine Updates verarbeitet.")
        return
    updates = sorted(get_updates(offset=last_update_id + 1), key=lambda x: x.get("update_id", 0))
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
        cmd = normalized.lstrip("/")
        if cmd in {"help", "hilfe"}:
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
                "motogp ❌ – alle ablehnen\n\n"\n                "TURKISH RIDER:\n"\n                "T1 / T2 / T1,T3 – Turkish-Rider-Vorschläge auswählen\n"\n                "turkish 1,3 – ausgeschriebene Variante\n"\n                "T alle / turkish alle – alle T-Vorschläge auswählen\n"\n                "T nein / turkish nein – Turkish-Auswahl ablehnen\n\n"
                "RACING MANUELL:\n"
                "racing top10 / racing top20 – gespeicherten Pool anzeigen\n"
                "racing gestern – gestrigen Pool anzeigen\n"
                "racing suche Bahattin – gespeicherten Pool durchsuchen\n"
                "racing artikel 3 – Nr. 3 der zuletzt angezeigten Liste durch QM schicken\n"
                "racing url <Link> – offiziellen MotoGP-/WorldSBK-Link durch QM schicken\n\n"
                "ALLGEMEIN:\n"
                "alle – alle Freigaben\n"
                "liste – offene Aufgaben\n"
                "watchlist – Watchlist anzeigen\n"
                "follow-analyse – Follower-Analyse\n"
                "race – Race-Kalender\n"
                "inspiration – Inspiration-Posts\n\n"
                "ENGAGEMENT:\n"
                "antwort IG-XXXXXXXX – Antwort freigeben\n"
                "ändern IG-XXXXXXXX Text – Antwort ändern\n"
                "ignorieren IG-XXXXXXXX – nichts senden\n"
                "info IG-XXXXXXXX – Details\n"
                "memory IG-XXXXXXXX – Interaktionshistorie\n"
                "antwort/ändern/ignorieren/info/memory FB-XXXXXXXX – Facebook\n\n"
                "SYSTEM:\n"
                "/help – Diese Hilfe"
            )
            _ack(uid)
            return
        if pi.get_latest_pending():
            action = _get_bild_command_action(cmd)
            if action:
                print(f"ROUTER: Update {uid} -> Instagram Bild-Freigabe ('{action}')")
                _handle_bild_command(action)
                _ack(uid)
                return

        if re.match(r"^(?:antwort|ändern|ignorieren|info|memory)\\s+ig-[a-f0-9]{8}(?:\\s+.*)?$", cmd, re.I):
            print(f"ROUTER: Update {uid} -> Instagram Engagement")
            send_message(instagram_engagement.telegram_command(text, run_id=os.environ.get("GITHUB_RUN_ID", "local")))
            _ack(uid)
            return

        if re.match(r"^(?:antwort|ändern|ignorieren|info|memory)\\s+fb-[a-f0-9]{8}(?:\\s+.*)?$", cmd, re.I):
            print(f"ROUTER: Update {uid} -> Facebook Engagement")
            send_message(facebook_engagement.telegram_command(text))
            _ack(uid)
            return

        if cmd in {"vision", "ocr", "omni"}:
            send_message("Bitte sende ein Bild mit dem Befehl /vision, /ocr oder /omni.")
            _ack(uid)
            return
        if re.match(r"^racing\s+(?:top10|top20|gestern|suche\s+.+|artikel\s+\d+|url\s+https?://\S+)$", cmd, re.I):
            print(f"ROUTER: Update {uid} -> manuelle Racing-Auswahl")
            result = subprocess.run([sys.executable, "-u", "racing_manual_selection.py", text], check=False)
            if result.returncode not in (0, 1):
                raise RuntimeError(f"Manuelle Racing-Auswahl fehlgeschlagen (Exit {result.returncode}).")
            _ack(uid)
            return

        is_turkish_approval = bool(
            re.fullmatch(r"turkish\s+(?:(?:t\s*)?[1-5](?:[\s,]+(?:t\s*)?[1-5])*|alle|nein|✅|❌)", cmd, re.I)
            or re.fullmatch(r"t\s*(?:[1-5](?:[\s,]+(?:t\s*)?[1-5])*|alle|nein|✅|❌)", cmd, re.I)
        )
        if "motogp" in cmd or is_turkish_approval:
            lane = "Turkish Rider" if is_turkish_approval else "MotoGP"
            print(f"ROUTER: Update {uid} -> {lane} Approval (atomare Übergabe)")
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
                "Beispiele: motogp 2,4 · T1 · T1,T3 · T alle · turkish 1,3 · alle · liste"
            )
        except Exception as e:
            print(f"ROUTER: Hilfe senden fehlgeschlagen: {e}")
        _ack(uid)
        return

    print("ROUTER: Kein verarbeitbares Update gefunden.")


if __name__ == "__main__":
    main()
