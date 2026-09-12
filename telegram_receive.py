"""Verarbeitet Telegram-Freigaben und schreibt nur freigegebene Entwürfe nach PUBLISHED.md."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from deal_hunter import compact_for_telegram, search_deal
from deal_hunter_browser import test_coupon
from price_tracking import (
    WATCHLIST,
    get_auto_track,
    set_auto_track,
    stop_tracking,
    track_product,
    trend_message,
)
from telegram_bot import get_chat_id, get_updates, send_message

SESSION_FILE = Path("memory/TELEGRAM_SESSION.md")
PUBLISHED_FILE = Path("content/PUBLISHED.md")


def load_session() -> tuple[int, dict[int, dict[str, str]]]:
    if not SESSION_FILE.is_file():
        raise FileNotFoundError(
            "Keine Telegram-Sitzung gefunden. Zuerst muss telegram_morning.py erfolgreich laufen."
        )

    content = SESSION_FILE.read_text(encoding="utf-8")
    timestamp_match = re.search(r"(?m)^Session-Timestamp:\s*(\d+)\s*$", content)
    if not timestamp_match:
        raise RuntimeError("Telegram-Sitzung enthält keinen gültigen Session-Timestamp.")

    posts: dict[int, dict[str, str]] = {}
    matches = list(
        re.finditer(
            r"^## Beitrag\s+([1-3])\s*\n(.*?)(?=^## Beitrag\s+[1-3]\s*$|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
    )
    for match in matches:
        number = int(match.group(1))
        section = match.group(2).strip()
        full_match = re.search(r"^### Vollständiger Entwurf\s*\n(.*)$", section, re.MULTILINE | re.DOTALL)
        if not full_match:
            continue
        full_text = full_match.group(1).strip()
        posts[number] = {
            "title": _field(section, "Titel"),
            "hook": _field(section, "Hook"),
            "platform": _field(section, "Plattform"),
            "full_text": full_text,
        }

    if len(posts) != 3:
        raise RuntimeError("Telegram-Sitzung enthält nicht drei lesbare Beiträge.")
    return int(timestamp_match.group(1)), posts


def _field(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+)$", text)
    return match.group(1).strip() if match else "–"


def parse_approval(text: str) -> list[int] | None:
    normalized = text.strip().lower()
    if normalized in {"alle", "✅"}:
        return [1, 2, 3]
    if normalized in {"nein", "❌"}:
        return []

    compact = re.sub(r"\s+", "", normalized)
    if re.fullmatch(r"[1-3](,[1-3])*", compact):
        return sorted({int(number) for number in compact.split(",")})
    return None


def _instagram_caption(draft: str) -> str:
    """Holt nur die Instagram-Caption aus einem vollständigen Content-Entwurf."""
    match = re.search(
        r"^Instagram-Caption:\s*\n(.+?)(?=^\s*(?:Facebook-Post|TikTok-Skript|Visuelle Idee|Hashtags Instagram|Hashtags TikTok|Trend-Bezug):|\Z)",
        draft,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else draft.strip()


def _published_header(platform: str) -> str:
    """Ordnet Reel-Entwürfe dem eindeutigen Reel-Publisher zu."""
    return "Instagram Reel" if "reel" in platform.lower() else platform.strip()


def append_approved_posts(posts: dict[int, dict[str, str]], selected: list[int], update_id: int) -> None:
    PUBLISHED_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = PUBLISHED_FILE.read_text(encoding="utf-8") if PUBLISHED_FILE.exists() else "# Freigegebene Beiträge\n"
    marker = f"Telegram-Update-ID: {update_id}"
    if marker in existing:
        print(f"Telegram-Update {update_id} wurde bereits verarbeitet.")
        return

    entries = []
    for number in selected:
        post = posts[number]
        header = _published_header(post["platform"])
        entries.extend(
            [
                f"## {header}",
                "Status: FREIGEGEBEN",
                "Freigabe: Telegram",
                marker,
                "Text:",
                _instagram_caption(post["full_text"]),
                "Video: auto" if header == "Instagram Reel" else "",
                "",
            ]
        )
    PUBLISHED_FILE.write_text(existing.rstrip() + "\n\n" + "\n".join(entries).rstrip() + "\n", encoding="utf-8")
    print(f"{len(selected)} freigegebene Beiträge nach {PUBLISHED_FILE} geschrieben.")


def acknowledge_through(update_id: int) -> None:
    # Telegram verwirft Updates mit kleinerer ID nach diesem Aufruf.
    get_updates(offset=update_id + 1)


def parse_deal_command(text: str) -> tuple[str, str] | None:
    lowered = text.strip().lower()
    for prefix in ("deal:", "suche:"):
        if lowered.startswith(prefix):
            return "search", text.strip()[len(prefix):].strip()
    if lowered.startswith("deal-test:"):
        return "test", text.strip()[len("deal-test:"):].strip()
    return None


def main() -> None:
    allowed_chat_id = get_chat_id()
    updates = get_updates()

    for update in sorted(updates, key=lambda item: item.get("update_id", 0)):
        update_id = update.get("update_id")
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        message_text = message.get("text")

        if not isinstance(update_id, int):
            continue
        if str(chat.get("id", "")) != str(allowed_chat_id):
            acknowledge_through(update_id)
            continue
        if not isinstance(message_text, str):
            acknowledge_through(update_id)
            continue

        lowered_command = message_text.strip().lower()
        if lowered_command.startswith("auto-track:"):
            value = message_text.split(":", 1)[1].strip().lower()
            if value not in {"on", "off"}:
                send_message("Bitte nutze: auto-track: on oder auto-track: off")
            else:
                enabled = value == "on"
                set_auto_track(enabled)
                send_message(
                    "✅ Auto-Track aktiv. Alle zukünftigen deal:-Suchen werden automatisch beobachtet."
                    if enabled
                    else "⏸️ Auto-Track aus. Bei deal:-Suche frage ich wieder nach."
                )
            acknowledge_through(update_id)
            return
        if lowered_command.startswith("trend:"):
            product = message_text.split(":", 1)[1].strip()
            send_message(trend_message(product) if product else "Bitte nutze: trend: <Produkt>")
            acknowledge_through(update_id)
            return
        if lowered_command == "watchlist":
            active = WATCHLIST.read_text(encoding="utf-8") if WATCHLIST.exists() else "Keine Watchlist vorhanden."
            send_message("📋 Watchlist\n" + active[:3000])
            acknowledge_through(update_id)
            return
        if lowered_command.startswith("track:"):
            value = message_text.split(":", 1)[1].strip()
            name, _, criteria = value.partition("|")
            send_message(track_product(name, criteria))
            acknowledge_through(update_id)
            return
        if lowered_command == "track":
            from deal_hunter import LAST_QUERY_FILE
            if LAST_QUERY_FILE.exists():
                send_message(track_product(LAST_QUERY_FILE.read_text(encoding="utf-8").strip()))
            else:
                send_message("Bitte suche zuerst mit deal: <Produkt> oder nutze track: <Produkt> | max: X €.")
            acknowledge_through(update_id)
            return
        for prefix, completed in (("stop:", False), ("erledigt:", True)):
            if lowered_command.startswith(prefix):
                send_message(stop_tracking(message_text.split(":", 1)[1].strip(), completed))
                acknowledge_through(update_id)
                return

        deal_command = parse_deal_command(message_text)
        if deal_command:
            command, value = deal_command
            if command == "search":
                if not value:
                    send_message("Bitte nutze: deal: <Produkt> oder suche: <Produkt>")
                else:
                    send_message("Ich recherchiere – das kann ein bis zwei Minuten dauern.")
                    try:
                        answer = compact_for_telegram(search_deal(value, status_callback=send_message))
                        if get_auto_track():
                            answer += "\n\n✅ Wird automatisch beobachtet.\n" + track_product(value)
                        else:
                            answer += "\n\n💡 Soll ich das beobachten? Antworte mit track."
                        send_message(answer)
                    except (RuntimeError, ValueError) as error:
                        send_message(f"Deal-Recherche nicht möglich: {error}")
            else:
                parts = value.split(maxsplit=1)
                if len(parts) != 2:
                    send_message("Bitte nutze: deal-test: <HTTPS-URL> <CODE>")
                else:
                    result = test_coupon(parts[0], parts[1])
                    send_message(f"Code-Test: {result['status']} – {result['reason']}")
            acknowledge_through(update_id)
            return

        session_timestamp, posts = load_session()
        message_timestamp = message.get("date", 0)
        if message_timestamp < session_timestamp:
            acknowledge_through(update_id)
            continue

        selected = parse_approval(message_text)
        if selected is None:
            send_message("Danke! Bitte antworte mit 1,3, alle, ✅, nein oder ❌; für Recherche: deal: <Produkt>.")
            acknowledge_through(update_id)
            return

        if not selected:
            send_message("Keine Beiträge freigegeben. In PUBLISHED.md wurde nichts eingetragen.")
            acknowledge_through(update_id)
            return

        append_approved_posts(posts, selected, update_id)
        selected_text = "+".join(str(number) for number in selected)
        send_message(
            f"Beitrag {selected_text} freigegeben – für 12:00 vorgemerkt. "
            "Die Veröffentlichung bleibt manuell."
        )
        acknowledge_through(update_id)
        return

    print("Keine neue Telegram-Antwort für die aktuelle Sitzung.")


if __name__ == "__main__":
    main()
