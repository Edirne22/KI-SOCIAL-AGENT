"""Dauerhafte, öffentliche Preisbeobachtung ohne Kauf- oder Login-Aktionen."""

from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path
from deal_hunter import search_deal
from telegram_bot import send_message

WATCHLIST = Path("memory/WATCHLIST.md")
HISTORY = Path("memory/PRICE_HISTORY.md")
MAX_ACTIVE = 15
PREFERENCES = Path("memory/USER_PREFERENCES.md")

def get_auto_track() -> bool:
    """Liest den dauerhaften, standardmäßig ausgeschalteten Auto-Track-Zustand."""
    content = PREFERENCES.read_text(encoding="utf-8") if PREFERENCES.exists() else ""
    match = re.search(r"(?mi)^-\\s*Auto-Track:\\s*(on|off)\\s*$", content)
    return bool(match and match.group(1).lower() == "on")

def set_auto_track(enabled: bool) -> None:
    content = PREFERENCES.read_text(encoding="utf-8") if PREFERENCES.exists() else "# Bülents Präferenzen\\n"
    line = f"- Auto-Track: {'on' if enabled else 'off'}"
    if re.search(r"(?mi)^-\\s*Auto-Track:\\s*(on|off)\\s*$", content):
        content = re.sub(r"(?mi)^-\\s*Auto-Track:\\s*(on|off)\\s*$", line, content)
    else:
        content = content.rstrip() + "\\n\\n## Deal-Hunter\\n" + line + "\\n"
    PREFERENCES.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCES.write_text(content, encoding="utf-8")

def active_products():
    content = WATCHLIST.read_text(encoding="utf-8") if WATCHLIST.exists() else "# Watchlist\n\n## Aktiv\n"
    section = content.split("## Erledigt / Beendet", 1)[0]
    return [(m.group(1).strip(), m.group(2).strip()) for m in re.finditer(r"^- \[ \] (.+?)(?: \| (.*))?$", section, re.MULTILINE)]

def track_product(product_name, criteria=""):
    products = active_products()
    if any(name.lower() == product_name.lower() for name, _ in products):
        return "Wird bereits beobachtet."
    if len(products) >= MAX_ACTIVE:
        return f"⚠️ Watchlist voll ({MAX_ACTIVE}/{MAX_ACTIVE}). Erst ein Produkt mit stop: oder erledigt: beenden."
    content = WATCHLIST.read_text(encoding="utf-8") if WATCHLIST.exists() else "# Watchlist\n\n## Aktiv\n\n## Erledigt / Beendet\n"
    line = f"- [ ] {product_name.strip()} | {criteria.strip() or 'keine Kriterien'} | seit {datetime.now():%Y-%m-%d}\n"
    content = content.replace("## Erledigt / Beendet", line + "\n## Erledigt / Beendet", 1)
    WATCHLIST.write_text(content, encoding="utf-8")
    return f"Beobachtung aktiv: {product_name}"

def stop_tracking(product_name, completed=False):
    content = WATCHLIST.read_text(encoding="utf-8") if WATCHLIST.exists() else ""
    pattern = rf"(?m)^- \[ \] ({re.escape(product_name.strip())}.*)$"
    if not re.search(pattern, content, re.IGNORECASE):
        return "Produkt nicht in der aktiven Watchlist gefunden."
    status = "erledigt" if completed else "beendet"
    content = re.sub(pattern, lambda m: f"- [x] {m.group(1)} | {status} {datetime.now():%Y-%m-%d}", content, count=1, flags=re.IGNORECASE)
    WATCHLIST.write_text(content, encoding="utf-8")
    return f"{product_name} wurde {status}."

def price_from_result(text):
    match = re.search(r"(\d{1,5}(?:[.,]\d{2})?)\s*€", text)
    return float(match.group(1).replace(",", ".")) if match else None


def history_for_product(product_name: str) -> list[tuple[datetime, float]]:
    """Liest ausschließlich vorhandene Preiswerte, ohne eine neue Recherche auszulösen."""
    content = HISTORY.read_text(encoding="utf-8") if HISTORY.exists() else ""
    entries: list[tuple[datetime, float]] = []
    for block in re.split(r"(?m)^## ", content)[1:]:
        date_match = re.match(r"(\\d{4}-\\d{2}-\\d{2}(?: \\d{2}:\\d{2})?)", block)
        name_match = re.search(r"(?m)^Produkt:\\s*(.+)$", block)
        price_match = re.search(r"(?m)^Preis:\\s*([0-9]+(?:\\.[0-9]+)?)", block)
        if not (date_match and name_match and price_match):
            continue
        if name_match.group(1).strip().lower() != product_name.strip().lower():
            continue
        try:
            entries.append((datetime.fromisoformat(date_match.group(1)), float(price_match.group(1))))
        except ValueError:
            continue
    return sorted(entries, key=lambda item: item[0])


def trend_message(product_name: str) -> str:
    entries = history_for_product(product_name)
    if not entries:
        return "Kein Tracking aktiv. Nutze track: <Produkt> zum Starten."

    rows = [
        f"📊 Preis-Historie: {product_name}",
        "",
        "| Datum | Preis | Änderung |",
        "|-------|-------|----------|",
    ]
    for index, (timestamp, price) in enumerate(entries[-10:]):
        change = "–"
        if index:
            previous = entries[-10 + index - 1][1] if len(entries) >= 10 else entries[index - 1][1]
            if previous and price != previous:
                delta = ((price - previous) / previous) * 100
                change = f"{'📉' if delta < 0 else '📈'} {delta:+.0f}%"
        rows.append(f"| {timestamp:%d.%m.} | {price:.2f} € | {change} |")

    if len(entries) < 2 or entries[-1][1] == entries[-2][1]:
        advice = "Trend: → Gleichbleibend\\nEmpfehlung: Weiter beobachten."
    elif entries[-1][1] < entries[-2][1]:
        days = max(1, (entries[-1][0].date() - entries[-2][0].date()).days)
        advice = f"Trend: 📉 Fallend seit {days} Tag(en)\\nEmpfehlung: Beobachten – könnte noch günstiger werden."
    else:
        advice = "Trend: 📈 Steigend\\nEmpfehlung: Bei passendem Preis zeitnah prüfen."
    return "\\n".join(rows) + "\\n\\n" + advice + "\\nPreise sind nicht bestätigt – bitte vor Kauf prüfen."


def send_alert_if_changed(product: str, old: float | None, price: float) -> None:
    if old is None or old == price:
        return
    direction = "📉 Preis gefallen" if price < old else "📈 Preis gestiegen"
    change = abs(((price - old) / old) * 100) if old else 0
    send_message(f"{direction}: {product}\\n{old:.2f} € → {price:.2f} € ({change:.0f}%)\\nBitte vor Kauf prüfen.")

def check_prices():
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    existing = HISTORY.read_text(encoding="utf-8") if HISTORY.exists() else "# Preis-Historie\n"
    for product, criteria in active_products():
        result = search_deal(product)
        price = price_from_result(result)
        if price is None:
            continue
        previous = re.findall(rf"(?m)^Produkt: {re.escape(product)}\nPreis: ([0-9.]+)", existing)
        old = float(previous[-1]) if previous else None
        existing += f"\n## {datetime.now():%Y-%m-%d %H:%M}\nProdukt: {product}\nPreis: {price:.2f}\nStatus: nicht bestätigt\nKriterien: {criteria}\n"
        send_alert_if_changed(product, old, price)
    HISTORY.write_text(existing, encoding="utf-8")
