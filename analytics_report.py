"""Erstellt einen Telegram-Tagesreport aus dem Performance-Memory."""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

from telegram_bot import send_message

PERFORMANCE_FILE = Path("memory/PERFORMANCE.md")
REPORTS_DIR = Path("memory/REPORTS")


def field(text: str, name: str) -> int:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(\d+)\s*$", text)
    return int(match.group(1)) if match else 0


def load_records() -> list[dict]:
    if not PERFORMANCE_FILE.exists():
        return []
    content = PERFORMANCE_FILE.read_text(encoding="utf-8")
    pattern = r"^## Beitrag vom (\d{4}-\d{2}-\d{2}) - Plattform: (.+?) - Titel: (.*?)\n(.*?)(?=^## Beitrag vom |\Z)"
    records = []
    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        day, platform, title, body = match.groups()
        records.append({"date": date.fromisoformat(day), "platform": platform, "title": title, "id": re.search(r"(?m)^ID:\s*(.+)$", body).group(1).strip() if re.search(r"(?m)^ID:\s*(.+)$", body) else "", "likes": field(body, "Likes"), "comments": field(body, "Kommentare"), "reach": field(body, "Reichweite")})
    return records


def totals(records: list[dict]) -> dict[str, int]:
    return {name: sum(record[name] for record in records) for name in ("likes", "comments", "reach")}


def main() -> None:
    today = date.today()
    records = load_records()
    current = [record for record in records if today - timedelta(days=6) <= record["date"] <= today]
    previous = [record for record in records if today - timedelta(days=13) <= record["date"] < today - timedelta(days=6)]
    current_totals, previous_totals = totals(current), totals(previous)
    top = sorted(current, key=lambda record: record["likes"], reverse=True)[:3]

    lines = [f"Analytics-Report {today.isoformat()}", "", "Top 3 der letzten 7 Tage:"]
    if top:
        for index, record in enumerate(top, start=1):
            lines.append(f"{index}. {record['platform']}: {record['title']} – {record['likes']} Likes")
    else:
        lines.append("Noch keine Insights verfügbar.")
    lines.extend(["", f"Gesamt: {current_totals['likes']} Likes · {current_totals['comments']} Kommentare · {current_totals['reach']} Reichweite", f"Vorwoche: {previous_totals['likes']} Likes · {previous_totals['comments']} Kommentare · {previous_totals['reach']} Reichweite"])
    report = "\n".join(lines) + "\n"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{today.isoformat()}.md"
    path.write_text("# " + report, encoding="utf-8")
    send_message(report)
    print(f"Report gespeichert: {path}")


if __name__ == "__main__":
    main()
