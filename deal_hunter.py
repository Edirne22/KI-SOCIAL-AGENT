"""Speichert und formatiert öffentliche Deal-Hunter-Ergebnisse."""

from __future__ import annotations

import argparse
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from llm_router import quick_chat
from search_provider import search

MEMORY_FILE = Path("memory/DEALS_FOUND.md")
LAST_QUERY_FILE = Path("memory/LAST_DEAL_QUERY.md")


def _research_query(product_query: str, criteria: str = "") -> str:
    """Ergänzt gespeicherte Kriterien sichtbar, ohne den Produktnamen zu verändern."""
    criteria = criteria.strip()
    return product_query.strip() if not criteria or criteria == "keine Kriterien" else f"{product_query.strip()} | Kriterien: {criteria}"


def extract_verified_offer(answer: str, live_search: bool, query: str = "") -> dict | None:
    """Übernimmt nur ein ausdrücklich als belegt formatiertes Live-Angebot."""
    if not live_search:
        return None
    match = re.search(
        r"(?ims)^\s*(?:BESTES[_ ]ANGEBOT|Bestes Angebot)\s*:?\s*\n(.*?)(?=^\s*(?:ALTERNATIVEN|Alternativen|HINWEIS|Hinweis|QUELLEN|Quellen)\b|\Z)",
        answer,
    )
    if not match:
        return None
    block = match.group(1)
    if re.search(r"\b(?:handyvertrag|mobilfunk|tarif|vertrag)\b", query, re.IGNORECASE):
        if not re.search(r"\b(?:monatlich|monat|mtl\.?|pro\s+monat)\b", block, re.IGNORECASE):
            return None
    price_match = re.search(r"(?im)^\s*[-*]?\s*(?:Preis|Bester Preis)\s*:\s*([0-9]{1,5}(?:[.,][0-9]{1,2})?)\s*€", block)
    retailer_match = re.search(r"(?im)^\s*[-*]?\s*(?:Händler|Shop)\s*:\s*(.+?)\s*$", block)
    url_match = re.search(r"https?://[^\s)>]+", block)
    proof_match = re.search(r"(?im)^\s*[-*]?\s*Belegt\s*:\s*ja\s*$", block)
    if not (price_match and retailer_match and url_match and proof_match):
        return None
    price = float(price_match.group(1).replace(",", "."))
    retailer = retailer_match.group(1).strip()
    url = url_match.group(0).rstrip(".,")
    if price <= 0 or not retailer or not url.startswith(("http://", "https://")):
        return None
    return {"price": price, "retailer": retailer, "url": url}


def search_deal_with_offer(
    product_query: str,
    criteria: str = "",
    status_callback: Callable[[str], None] | None = None,
) -> dict:
    query = re.sub(r"(?is)^\s*(?:deal|suche)\s*:?\s*", "", product_query).strip()
    if not query:
        raise ValueError("Bitte nenne ein Produkt nach 'deal:' oder 'suche:'.")

    try:
        outcome = search(_research_query(query, criteria), status_callback=status_callback)
    except (RuntimeError, ValueError) as error:
        err_text = str(error)
        print(f"SEARCH-FEHLER abgefangen in deal_hunter: {err_text}")
        answer = f"⚠️ Suche derzeit nicht verfügbar für '{query}'.\nUrsache: {err_text}\nBitte später erneut versuchen."
        provider = "Keiner (Fehler)"
        live_search = False
        offer = None
        save_result(query, provider, live_search, answer, criteria, offer)
        LAST_QUERY_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_QUERY_FILE.write_text(query, encoding="utf-8")

        # Versuche Telegram-Benachrichtigung, falls Token konfiguriert ist
        try:
            from telegram_bot import send_message
            send_message(f"⚠️ Deal-Hunter-Hinweis für '{query}': Suche nicht möglich.\n{err_text}")
        except Exception:
            pass

        return {"answer": answer, "offer": offer, "provider": provider, "live_search": live_search}

    answer = outcome["answer"].strip()
    sources = outcome.get("results") or []
    if sources:
        answer += "\n\nQuellen:\n" + "\n".join(
            f"- {item['title']}: {item['url']}" for item in sources
        )
    if outcome.get("warning") and outcome["warning"] not in answer:
        answer = outcome["warning"] + "\n\n" + answer

    offer = extract_verified_offer(answer, outcome["live_search"], _research_query(query, criteria))
    save_result(query, outcome["provider"], outcome["live_search"], answer, criteria, offer)
    LAST_QUERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_QUERY_FILE.write_text(query, encoding="utf-8")
    return {"answer": answer, "offer": offer, "provider": outcome["provider"], "live_search": outcome["live_search"]}


def search_deal(product_query: str, status_callback: Callable[[str], None] | None = None) -> str:
    """Kompatible Textschnittstelle für Telegram und manuelle Workflow-Aufrufe."""
    return search_deal_with_offer(product_query, status_callback=status_callback)["answer"]


def save_result(
    query: str,
    provider: str,
    live_search: bool,
    result: str,
    criteria: str = "",
    offer: dict | None = None,
) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else "# Gefundene Deals\n"
    offer_lines = ""
    if criteria and criteria != "keine Kriterien":
        offer_lines += f"Kriterien: {criteria}\n"
    if offer:
        offer_lines += (
            "Verifiziertes Angebot: ja\n"
            f"Preis: {offer['price']:.2f} €\n"
            f"Händler: {offer['retailer']}\n"
            f"Quelle: {offer['url']}\n"
        )
    else:
        offer_lines += "Verifiziertes Angebot: nein\n"
    entry = (
        f"\n## Suche vom {timestamp}\nAnfrage: {query}\nProvider: {provider}\n"
        f"Live-Suche: {'ja' if live_search else 'nein'}\n{offer_lines}\n{result}\n"
    )
    MEMORY_FILE.write_text(existing.rstrip() + entry, encoding="utf-8")


def compact_for_telegram(result: str, limit: int = 3500) -> str:
    prefix = "🛒 Deal-Suche\n"
    if len(result) > limit:
        result = result[:limit].rstrip() + "\n\n[Antwort gekürzt]"
    return prefix + result + "\n\n⚠️ Preise vor dem Kauf selbst prüfen."


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help="Produktanfrage")
    args = parser.parse_args()
    try:
        print(search_deal(" ".join(args.query)))
    except (RuntimeError, ValueError) as error:
        # Ein ausfallender Suchanbieter ist ein erwartbarer Betriebszustand,
        # kein Codefehler. search_provider.py hat die Ursache bereits protokolliert.
        print(f"Deal-Recherche derzeit nicht möglich: {error}")
