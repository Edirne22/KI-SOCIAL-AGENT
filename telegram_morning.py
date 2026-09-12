"""Sendet die drei neuesten Content-Ideen als Telegram-Freigabeanfrage."""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path

from telegram_bot import send_message

CONTENT_PLAN = Path("content/CONTENT_PLAN.md")
SESSION_FILE = Path("memory/TELEGRAM_SESSION.md")


def _field(block: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+)$", block)
    return match.group(1).strip() if match else "–"


def _short_description(block: str) -> str:
    match = re.search(
        r"Instagram-Caption:\s*\n(.+?)(?=\n\n(?:Facebook-Post|TikTok-Skript|Visuelle Idee|Hashtags|Trend-Bezug|---)|\Z)",
        block,
        re.DOTALL,
    )
    text = match.group(1).strip() if match else _field(block, "Thema")
    return re.sub(r"\s+", " ", text)[:280]


def load_latest_posts() -> list[dict[str, str]]:
    if not CONTENT_PLAN.is_file():
        raise FileNotFoundError(f"Content-Plan nicht gefunden: {CONTENT_PLAN}")

    content = CONTENT_PLAN.read_text(encoding="utf-8")
    matches = list(
        re.finditer(
            r"^--- BEITRAG\s+([1-3])\s+---\s*\n(.*?)(?=^--- BEITRAG\s+[1-3]\s+---|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
    )
    if len(matches) < 3:
        raise RuntimeError("Im CONTENT_PLAN.md wurden nicht drei vollständige Beiträge gefunden.")

    latest = matches[-3:]
    posts = []
    for number, match in enumerate(latest, start=1):
        block = match.group(2).strip()
        posts.append(
            {
                "number": str(number),
                "title": _field(block, "Titel"),
                "hook": _field(block, "Hook"),
                "platform": _field(block, "Plattform"),
                "description": _short_description(block),
                "full_text": block,
            }
        )
    return posts


def build_message(posts: list[dict[str, str]]) -> str:
    lines = ["Guten Morgen Bülent – hier sind deine 3 Content-Entwürfe:"]
    for post in posts:
        lines.extend(
            [
                "",
                f"{post['number']}. {post['title']}",
                f"Hook: {post['hook']}",
                f"Plattform: {post['platform']}",
                f"Kurz: {post['description']}",
            ]
        )
    lines.extend(
        [
            "",
            "Antworte mit 1,3 für Beitrag 1 und 3, mit alle oder ✅ für alle,",
            "oder mit nein bzw. ❌ für keine Freigabe.",
            "Eine Freigabe trägt Beiträge nur in PUBLISHED.md ein; veröffentlicht wird nichts automatisch.",
        ]
    )
    return "\n".join(lines)


def save_session(posts: list[dict[str, str]]) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = int(time.time())

    lines = [
        "# Telegram-Freigabe-Sitzung",
        "",
        f"Datum: {now}",
        f"Session-Timestamp: {timestamp}",
        "Status: WARTET AUF ANTWORT",
        "",
    ]
    for post in posts:
        lines.extend(
            [
                f"## Beitrag {post['number']}",
                f"Titel: {post['title']}",
                f"Hook: {post['hook']}",
                f"Plattform: {post['platform']}",
                f"Beschreibung: {post['description']}",
                "",
                "### Vollständiger Entwurf",
                post["full_text"],
                "",
            ]
        )
    SESSION_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Telegram-Sitzung gespeichert: {SESSION_FILE}")


def main() -> None:
    posts = load_latest_posts()
    send_message(build_message(posts))
    save_session(posts)
    print("Telegram-Freigabeanfrage erfolgreich gesendet.")


if __name__ == "__main__":
    main()
