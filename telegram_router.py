"""Einziger Telegram-Poller/Routing-Einstiegspunkt.

Nur dieser Router konsumiert getUpdates im Zeitplan. MotoGP erhält exakt das
bereits gelesene Update als Argumente. Unbekannte Nachrichten werden still
bestätigt, damit der alte allgemeine Receiver keine irreführende Freigabe-Hilfe
mehr auf beliebige Nachrichten sendet.
"""
from __future__ import annotations

import re
import subprocess
import sys
from telegram_bot import get_chat_id, get_updates, send_message


def _ack(update_id: int) -> None:
    get_updates(offset=update_id + 1)


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
        if chat != allowed or not isinstance(text, str):
            print(f"ROUTER: Update {uid} nicht aus erlaubtem Text-Chat; bestätigt/übersprungen.")
            _ack(uid)
            return

        normalized = " ".join(text.strip().lower().split())
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
