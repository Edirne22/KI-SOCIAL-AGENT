"""Erstellt einen ehrlichen wöchentlichen Growth-Report aus gespeicherten Performance-Daten."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from telegram_bot import send_message
from viral.pattern_detector import _entries

LOG = Path("memory/GROWTH_LOG.md")


def _period(days_back: int, days_forward: int = 0):
    today = date.today()
    return [row for row in _entries() if today - timedelta(days=days_back) <= date.fromisoformat(str(row["date"])) <= today - timedelta(days=days_forward)]


def _summary(rows):
    reach = sum(int(row.get("reach", 0)) for row in rows)
    engagement = sum(sum(int(row.get(key, 0)) for key in ("likes", "comments", "shares", "saved")) for row in rows)
    rate = engagement / reach * 100 if reach else None
    best = max(rows, key=lambda row: (sum(int(row.get(key, 0)) for key in ("likes", "comments", "shares", "saved")) / max(int(row.get("reach", 0)), 1)), default=None)
    return reach, engagement, rate, best


def main() -> None:
    current = _period(6)
    previous = _period(13, 7)
    reach, engagement, rate, best = _summary(current)
    _, _, previous_rate, _ = _summary(previous)
    week = date.today().isocalendar()
    best_text = str(best.get("title")) if best else "nicht verfügbar"
    change = "nicht verfügbar" if rate is None or previous_rate is None else f"{(rate - previous_rate):+.2f} Prozentpunkte"
    entry = f"""## Woche {week.week}/{week.year}
- Reichweite: {reach:,}
- Engagement: {engagement:,}
- Viral-Rate: {f"{rate:.2f} %" if rate is not None else "nicht verfügbar"} (Vorwoche: {f"{previous_rate:.2f} %" if previous_rate is not None else "nicht verfügbar"}; Veränderung: {change})
- Follower: nicht verfügbar (keine verlässliche Follower-Quelle verbunden)
- Bester Beitrag: {best_text}
- Learning: Nur aus echten Insights ableiten; getestete Hooks und Formate dokumentieren.

"""
    old = LOG.read_text(encoding="utf-8") if LOG.exists() else "# Growth-Log\n\n"
    marker = f"## Woche {week.week}/{week.year}"
    if marker in old:
        import re
        old = re.sub(rf"(?ms)^{re.escape(marker)}.*?(?=^## Woche |\Z)", "", old).rstrip() + "\n\n"
    LOG.write_text(old.rstrip() + "\n\n" + entry, encoding="utf-8")
    message = (
        f"📈 Growth-Report Woche {week.week}\n"
        f"Reichweite: {reach:,}\n"
        f"Engagement-Rate: {f'{rate:.2f} %' if rate is not None else 'nicht verfügbar'}\n"
        f"Bester Beitrag: {best_text}\n"
        "Follower/Profilbesuche: nicht verfügbar – es werden keine Werte geschätzt."
    )
    send_message(message)
    print("Growth-Report erstellt und per Telegram gesendet.")


if __name__ == "__main__":
    main()
