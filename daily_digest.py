"""Sendet Bülents kompaktes, rein lesendes Telegram-Morgenbriefing."""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

from telegram_bot import send_message

PUBLISHED_FILE = Path("content/PUBLISHED.md")
CONTENT_PLAN_FILE = Path("content/CONTENT_PLAN.md")


def blocks(content: str) -> list[tuple[str, str]]:
    return [(match.group(1).strip(), match.group(2).strip()) for match in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL)]


def yesterday_posts(content: str) -> list[str]:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    result = []
    for header, body in blocks(content):
        match = re.search(r"\[GEPOSTET " + re.escape(yesterday) + r" (\d{2}:\d{2})(?: \| ID: ([^\]]+))?\]", header)
        if match:
            time, media_id = match.groups()
            platform = header.split("[GEPOSTET", 1)[0].strip()
            suffix = f", ID: {media_id}" if media_id else ", keine ID"
            result.append(f"- {platform} ({time}{suffix})")
    return result


def default_time(platform: str) -> str:
    lowered = platform.lower()
    if "facebook" in lowered:
        return "12:00"
    if "story" in lowered:
        return "12:30"
    if "reel" in lowered:
        return "12:00"
    if "instagram" in lowered:
        return "12:15"
    return "Zeit offen"


def planned_posts(content: str) -> list[str]:
    result = []
    for header, body in blocks(content):
        if not re.search(r"(?m)^Status:\s*FREIGEGEBEN\s*$", body):
            continue
        planned = re.search(r"(?m)^Geplant:\s*(\d{1,2}:\d{2})\s*$", body)
        platform = header.split("[", 1)[0].strip()
        title = re.search(r"(?m)^Titel:\s*(.+)$", body)
        title_text = f" – {title.group(1).strip()[:55]}" if title else ""
        result.append(f"- {planned.group(1) if planned else default_time(platform)} – {platform}{title_text}")
    return result


def latest_ideas(content: str) -> list[str]:
    titles = [match.group(1).strip() for match in re.finditer(r"(?m)^Titel:\s*(.+)$", content)]
    return titles[-3:]


def build_digest() -> str:
    published = PUBLISHED_FILE.read_text(encoding="utf-8") if PUBLISHED_FILE.exists() else ""
    plan = CONTENT_PLAN_FILE.read_text(encoding="utf-8") if CONTENT_PLAN_FILE.exists() else ""
    posted = yesterday_posts(published)
    planned = planned_posts(published)
    ideas = latest_ideas(plan)

    lines = ["🌅 Guten Morgen, Bülent!", "", "📊 Gestern gepostet:"]
    lines.extend(posted or ["- Keine gespeicherten Beiträge von gestern."])
    lines.extend(["", "📅 Heute geplant:"])
    lines.extend(planned or ["- Noch keine freigegebenen Beiträge."])
    lines.extend(["", "💡 Neue Ideen warten auf Freigabe:"])
    lines.extend([f"{index}. {title}" for index, title in enumerate(ideas, start=1)] or ["- Keine neuen Ideen gefunden."])
    lines.extend(["", "Antworten wie gewohnt: 1,3 / alle / nein"])
    return "\n".join(lines)


def main() -> None:
    send_message(build_digest())
    print("Daily Digest an Telegram gesendet.")


if __name__ == "__main__":
    main()
