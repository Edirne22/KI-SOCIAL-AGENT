"""Einziger Telegram-Poller/Routing-Einstiegspunkt.

Nur dieser Router konsumiert getUpdates im Zeitplan. MotoGP erhält exakt das
bereits gelesene Update als Argumente; kein zweiter Poll, keine Race-Condition.
"""
from __future__ import annotations

import subprocess
import sys
from telegram_bot import get_chat_id, get_updates


def _ack(update_id: int) -> None:
    get_updates(offset=update_id + 1)


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
            if result.returncode != 0:
                raise RuntimeError(f"MotoGP-Receiver fehlgeschlagen (Exit {result.returncode}); Update bleibt offen.")
            _ack(uid)
            print(f"ROUTER: MotoGP Update {uid} erfolgreich verarbeitet und bestätigt.")
            return

        print(f"ROUTER: Update {uid} -> allgemeiner Telegram Receiver")
        result = subprocess.run([sys.executable, "-u", "telegram_receive.py"], check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Allgemeiner Telegram-Receiver fehlgeschlagen (Exit {result.returncode}).")
        return

    print("ROUTER: Kein verarbeitbares Update gefunden.")


if __name__ == "__main__":
    main()
