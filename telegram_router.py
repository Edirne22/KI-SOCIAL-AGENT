"""Einziger Telegram-Poller/Routing-Einstiegspunkt.

Nur dieser Router konsumiert getUpdates im Zeitplan. MotoGP erhält exakt das
bereits gelesene Update als Argumente. Unbekannte Nachrichten werden mit einer
freundlichen Hilfe-Antwort quittiert.
"""
from __future__ import annotations

import re
import subprocess
import sys
from telegram_bot import get_chat_id, get_updates, send_message


HELP_TEXT = (
    "🤖 Kommando nicht erkannt.\n\n"
    "Verfügbare Kommandos (Beispiel):\n"
    "• motogp 2,4  – MotoGP-Freigabe\n"
    "• motogp ✅ / motogp ❌\n"
    "• alle, liste, watchlist\n"
    "• 1,2  – Auswahl"
)


def _ack(update_id: int) -> None:
    get_updates(offset=update_id + 1)


def _send(chat_id: str, text: str) -> None:
    """Telegram-Antwort senden, Fehler nur loggen – nie crashen."""
    try:
        send_message(chat_id, text)
    except TypeError:
        # Fallback, falls send_message(text) die Signatur ist
        try:
            send_message(text)
        except Exception as e:
            print(f"ROUTER: Antwort senden fehlgeschlagen: {e}")
    except Exception as e:
        print(f"ROUTER: Antwort senden fehlgeschlagen: {e}")


def _normalize_motogp_args(text: str) -> str:
    """FIX 1: Komma-/Leerzeichen-Varianten vereinheitlichen.

    'motogp 2, 4'  -> 'motogp 2,4'
    'motogp 2 ,4'  -> 'motogp 2,4'
    'motogp 2 4'   -> 'motogp 2 4'  (unverändert)
    """
    cleaned = re.sub(r"\s*,\s*", ",", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


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

        # FIX 2: Case-Insensitive für Routing-Vergleich
        normalized = " ".join(text.strip().lower().split())
        if normalized.startswith("motogp ") or normalized in {"motogp", "motogp ✅", "motogp ❌"}:
            # FIX 1: Komma-Varianten vor Weitergabe vereinheitlichen
            forward_text = _normalize_motogp_args(text)
            print(f"ROUTER: Update {uid} -> MotoGP Approval (atomare Übergabe)")
            result = subprocess.run(
                [sys.executable, "-u", "motogp_telegram_receive.py", str(uid), chat, forward_text],
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"MotoGP-Receiver fehlgeschlagen (Exit {result.returncode}); Update bleibt offen.")
            _ack(uid)
            print(f"ROUTER: MotoGP Update {uid} erfolgreich verarbeitet und bestätigt.")
            return

        if _is_general_command(text):
            print(f"ROUTER: Update {uid} -> allgemeiner Telegram Receiver")
            result = subprocess.run([sys.executable, "-u", "telegram_receive.py"], check=False)
            if result.returncode != 0:
                raise RuntimeError(f"Allgemeiner Telegram-Receiver fehlgeschlagen (Exit {result.returncode}).")
            return

        # FIX 3: Freundliche Antwort statt stiller Bestätigung
        print(f"ROUTER: Update {uid} unbekannt; sende freundliche Hilfe.")
        _send(chat, HELP_TEXT)
        _ack(uid)
        return

    print("ROUTER: Kein verarbeitbares Update gefunden.")


if __name__ == "__main__":
    main()
