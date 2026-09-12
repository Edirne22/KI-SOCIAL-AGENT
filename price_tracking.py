"""Dauerhafte, öffentliche Preisbeobachtung ohne Kauf- oder Login-Aktionen."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from deal_hunter import search_deal
from telegram_bot import send_message

WATCHLIST = Path("memory/WATCHLIST.md")
HISTORY = Path("memory/PRICE_HISTORY.md")
PREFERENCES = Path("memory/USER_PREFERENCES.md")
MAX_ACTIVE = 15


def _read_text(path: Path, fallback: str) -> str:
    """Liest UTF-8 und normalisiert versehentlich gespeicherte Text-Zeilenumbrüche."""
    content = path.read_text(encoding="utf-8") if path.exists() else fallback
    return content.replace("\r\n", "\n").replace("\\n", "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")


def get_auto_track() -> bool:
    content = _read_text(PREFERENCES, "")
    match = re.search(r"(?mi)^-\s*Auto-Track:\s*(on|off)\s*$", content)
    return bool(match and match.group(1).lower() == "on")


def set_auto_track(enabled: bool) -> None:
    """Erzeugt genau einen Deal-Hunter-Abschnitt und ersetzt statt anzuhängen."""
    content = _read_text(PREFERENCES, "# Bülents Präferenzen\n")
    content = re.sub(r"(?ms)^## Deal-Hunter\s*\n.*?(?=^## |\Z)", "", content).rstrip()
    state = "on" if enabled else "off"
    content += f"\n\n## Deal-Hunter\n- Auto-Track: {state}\n"
    _write_text(PREFERENCES, content)


def active_products() -> list[tuple[str, str]]:
    content = _read_text(WATCHLIST, "# Watchlist\n\n## Aktiv\n")
    section = content.split("## Erledigt / Beendet", 1)[0]
    return [
        (match.group(1).strip(), match.group(2).strip())
        for match in re.finditer(r"^- \[ \] (.+?)(?: \| (.*))?$", section, re.MULTILINE)
    ]


def track_product(product_name: str, criteria: str = "") -> str:
    product_name = product_name.strip()
    if not product_name:
        return "Bitte nenne ein Produkt für die Beobachtung."
    products = active_products()
    if any(name.lower() == product_name.lower() for name, _ in products):
        return "Wird bereits beobachtet."
    if len(products) >= MAX_ACTIVE:
        return f"⚠️ Watchlist voll ({MAX_ACTIVE}/{MAX_ACTIVE}). Erst ein Produkt mit stop: oder erledigt: beenden."
    content = _read_text(WATCHLIST, "# Watchlist\n\n## Aktiv\n\n## Erledigt / Beendet\n")
    if "## Erledigt / Beendet" not in content:
        content = content.rstrip() + "\n\n## Erledigt / Beendet\n"
    line = f"- [ ] {product_name} | {criteria.strip() or 'keine Kriterien'} | seit {datetime.now():%Y-%m-%d}\n"
    content = content.replace("## Erledigt / Beendet", line + "\n## Erledigt / Beendet", 1)
    _write_text(WATCHLIST, content)
    return f"Beobachtung aktiv: {product_name}"


def stop_tracking(product_name: str, completed: bool = False) -> str:
    content = _read_text(WATCHLIST, "")
    pattern = rf"(?mi)^- \[ \] ({re.escape(product_name.strip())}.*)$"
    if not re.search(pattern, content):
        return "Produkt nicht in der aktiven Watchlist gefunden."
    status = "erledigt" if completed else "beendet"
    content = re.sub(
        pattern,
        lambda match: f"- [x] {match.group(1)} | {status} {datetime.now():%Y-%m-%d}",
        content,
        count=1,
    )
    _write_text(WATCHLIST, content)
    return f"{product_name} wurde {status}."


def price_from_result(text: str) -> float | None:
    match = re.search(r"(\d{1,5}(?:[.,]\d{2})?)\s*€", text)
    return float(match.group(1).replace(",", ".")) if match else None


def history_for_product(product_name: str) -> list[tuple[datetime, float]]:
    content = _read_text(HISTORY, "")
    entries: list[tuple[datetime, float]] = []
    for block in re.split(r"(?m)^## ", content)[1:]:
        date_match = re.match(r"(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?)", block)
        name_match = re.search(r"(?m)^Produkt:\s*(.+)$", block)
        price_match = re.search(r"(?m)^Preis:\s*([0-9]+(?:\.[0-9]+)?)", block)
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
    visible = entries[-10:]
    for index, (timestamp, price) in enumerate(visible):
        change = "–"
        if index:
            previous = visible[index - 1][1]
            if previous and price != previous:
                delta = ((price - previous) / previous) * 100
                change = f"{'📉' if delta < 0 else '📈'} {delta:+.0f}%"
        rows.append(f"| {timestamp:%d.%m.} | {price:.2f} € | {change} |")

    if len(entries) < 2 or entries[-1][1] == entries[-2][1]:
        advice = "Trend: → Gleichbleibend\nEmpfehlung: Weiter beobachten."
    elif entries[-1][1] < entries[-2][1]:
        days = max(1, (entries[-1][0].date() - entries[-2][0].date()).days)
        advice = f"Trend: 📉 Fallend seit {days} Tag(en)\nEmpfehlung: Beobachten – könnte noch günstiger werden."
    else:
        advice = "Trend: 📈 Steigend\nEmpfehlung: Bei passendem Preis zeitnah prüfen."
    return "\n".join(rows) + "\n\n" + advice + "\nPreise sind nicht bestätigt – bitte vor Kauf prüfen."


def send_alert_if_changed(product: str, old: float | None, price: float) -> None:
    if old is None or old == price:
        return
    direction = "📉 Preis gefallen" if price < old else "📈 Preis gestiegen"
    change = abs(((price - old) / old) * 100) if old else 0
    send_message(f"{direction}: {product}\n{old:.2f} € → {price:.2f} € ({change:.0f}%)\nBitte vor Kauf prüfen.")


def check_prices() -> None:
    existing = _read_text(HISTORY, "# Preis-Historie\n")
    for product, criteria in active_products():
        result = search_deal(product)
        price = price_from_result(result)
        if price is None:
            continue
        previous = re.findall(rf"(?m)^Produkt: {re.escape(product)}\nPreis: ([0-9.]+)", existing)
        old = float(previous[-1]) if previous else None
        existing += (
            f"\n## {datetime.now():%Y-%m-%d %H:%M}\nProdukt: {product}\nPreis: {price:.2f}\n"
            f"Status: nicht bestätigt\nKriterien: {criteria}\n"
        )
        send_alert_if_changed(product, old, price)
    _write_text(HISTORY, existing)
