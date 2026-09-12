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

def active_products():
    content = WATCHLIST.read_text(encoding="utf-8") if WATCHLIST.exists() else "# Watchlist\n\n## Aktiv\n"
    section = content.split("## Erledigt / Beendet", 1)[0]
    return [(m.group(1).strip(), m.group(2).strip()) for m in re.finditer(r"^- \[ \] (.+?)(?: \| (.*))?$", section, re.MULTILINE)]

def track_product(product_name, criteria=""):
    products = active_products()
    if any(name.lower() == product_name.lower() for name, _ in products):
        return "Wird bereits beobachtet."
    if len(products) >= MAX_ACTIVE:
        return "Watchlist-Limit von 15 aktiven Produkten erreicht."
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
        if old is not None and old != price:
            direction = "📉 Preis gefallen" if price < old else "📈 Preis gestiegen"
            send_message(f"{direction}: {product}\n{old:.2f} € → {price:.2f} €\nBitte vor Kauf prüfen.")
    HISTORY.write_text(existing, encoding="utf-8")
