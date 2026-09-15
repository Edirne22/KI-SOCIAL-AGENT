"""Einziger Telegram-Poller/Routing-Einstiegspunkt.

Wichtig: Nur dieser Router darf im Zeitplan getUpdates konsumieren. Dadurch
konkurrieren allgemeine Freigaben und MotoGP-Freigaben nicht mehr um dieselbe
Telegram-Bot-Queue.
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

    # Genau das älteste relevante Update routen. Der jeweilige Receiver arbeitet
    # wie bisher; der nächste 5-Minuten-Lauf nimmt danach das nächste Update.
    for upd in updates:
        uid = upd.get("update_id")
        msg = upd.get("message") or {}
        chat = str((msg.get("chat") or {}).get("id", ""))
        text = msg.get("text")
        if not isinstance(uid, int):
            continue
        if chat != allowed or not isinstance(text, str):
            print(f"ROUTER: Update {uid} ist nicht aus dem erlaubten Text-Chat; bestätigt/übersprungen.")
            _ack(uid)
            return

        normalized = " ".join(text.strip().lower().split())
        if normalized.startswith("motogp ") or normalized in {"motogp", "motogp ✅", "motogp ❌"}:
            print(f"ROUTER: Update {uid} -> MotoGP Approval")
            result = subprocess.run([sys.executable, "-u", "motogp_telegram_receive.py"], check=False)
            if result.returncode != 0:
                raise RuntimeError(f"MotoGP-Receiver fehlgeschlagen (Exit {result.returncode}); Update bleibt zur Wiederholung offen.")
            # Erst nach erfolgreichem MotoGP-Handler konsumieren. So kann der
            # allgemeine Receiver dieselbe Nachricht nicht mehr stehlen.
            _ack(uid)
            return

        print(f"ROUTER: Update {uid} -> allgemeiner Telegram Receiver")
        result = subprocess.run([sys.executable, "-u", "telegram_receive.py"], check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Allgemeiner Telegram-Receiver fehlgeschlagen (Exit {result.returncode}).")
        return

    print("ROUTER: Kein verarbeitbares Update gefunden.")


if __name__ == "__main__":
    main()
