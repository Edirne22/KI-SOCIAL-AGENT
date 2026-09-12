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



TRACK_HELP = (
    "Format: track: <Produkt> [max: X €] [min: Y] [netz: Z]\n"
    "Beispiele:\n• track: Motorradhandschuhe max 50 €\n"
    "• track: Handyvertrag 80GB D1 max 13 €"
)


def _named_command(text: str, names: tuple[str, ...]) -> str | None:
    alternatives = "|".join(re.escape(name) for name in names)
    match = re.match(rf"(?is)^\s*(?:{alternatives})\s*:?\s*(.*)$", text)
    return match.group(1).strip() if match else None


def parse_track_command(text: str) -> tuple[str, str] | None:
    """Erkennt mobilfreundliche Track-Varianten ohne die Produktschreibweise zu verändern."""
    value = _named_command(text, ("track",))
    if value is None:
        return None
    if not value:
        return "", ""

    separator = re.search(r"[|,(]", value)
    product_part = value[:separator.start()] if separator else value
    criteria_part = value[separator.end():].rstrip(")") if separator else ""

    patterns = (
        ("max", re.compile(r"(?i)\b(?:max|bis|unter)\s*:?\s*(\d+(?:[.,]\d+)?)\s*€?")),
        ("min", re.compile(r"(?i)\b(?:min|mindestens)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(GB)?\b")),
        ("netz", re.compile(r"(?i)\bnetz\s*:?\s*(D1|D2|O2)\b")),
        ("netz", re.compile(r"(?i)\b(D1|D2|O2)\s+netz\b")),
    )
    matches = []
    for label, pattern in patterns:
        for match in pattern.finditer(value):
            matches.append((match.start(), match.end(), label, match.group(1), match.group(0)))

    if matches and not separator:
        first_criterion = min(start for start, *_ in matches)
        product_part = value[:first_criterion]
        criteria_part = value[first_criterion:]

    product_name = product_part.strip(" \t,|()")
    if not product_name:
        return "", ""

    criteria = []
    seen = set()
    criteria_scope = criteria_part or value[len(product_part):]
    for _, _, label, raw_value, raw_text in matches:
        if raw_text not in criteria_scope and not separator:
            continue
        if label == "max":
            item = f"max: {raw_value.replace(',', '.')} €"
        elif label == "min":
            unit = " GB" if "gb" in raw_text.lower() else ""
            item = f"min: {raw_value.replace(',', '.')}{unit}"
        else:
            item = f"Netz: {raw_value.upper()}"
        if item not in seen:
            criteria.append(item)
            seen.add(item)
    return product_name, " | ".join(criteria)



def parse_deal_command(text: str) -> tuple[str, str] | None:
    deal_test = _named_command(text, ("deal-test",))
    if deal_test is not None:
        return "test", deal_test
    query = _named_command(text, ("deal", "suche"))
    return ("search", query) if query is not None else None


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
        track_command = parse_track_command(message_text)
        if track_command is not None:
            name, criteria = track_command
            if not name:
                from deal_hunter import LAST_QUERY_FILE
                if LAST_QUERY_FILE.exists() and lowered_command == "track":
                    send_message(track_product(LAST_QUERY_FILE.read_text(encoding="utf-8").strip()))
                else:
                    send_message(TRACK_HELP)
            else:
                send_message(track_product(name, criteria))
            acknowledge_through(update_id)
            return
        for names, completed in ((("stop", "beenden"), False), (("erledigt", "gekauft"), True)):
            product = _named_command(message_text, names)
            if product is not None:
                if not product:
                    send_message("Bitte nenne ein Produkt, zum Beispiel: stop: Motorradhandschuhe")
                else:
                    send_message(stop_tracking(product, completed))
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
