"""Speichert und formatiert öffentliche Deal-Hunter-Ergebnisse."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from search_provider import search

MEMORY_FILE = Path("memory/DEALS_FOUND.md")
LAST_QUERY_FILE = Path("memory/LAST_DEAL_QUERY.md")


def search_deal(product_query: str, status_callback: Callable[[str], None] | None = None) -> str:
    query = product_query.strip()
    if not query:
        raise ValueError("Bitte nenne ein Produkt nach 'deal:' oder 'suche:'.")

    outcome = search(query, status_callback=status_callback)
    answer = outcome["answer"].strip()
    sources = outcome.get("results") or []
    if sources:
        answer += "\n\nQuellen:\n" + "\n".join(
            f"- {item['title']}: {item['url']}" for item in sources
        )
    if outcome.get("warning") and outcome["warning"] not in answer:
        answer = outcome["warning"] + "\n\n" + answer

    save_result(query, outcome["provider"], outcome["live_search"], answer)
    LAST_QUERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_QUERY_FILE.write_text(query, encoding="utf-8")
    return answer


def save_result(query: str, provider: str, live_search: bool, result: str) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else "# Gefundene Deals\n"
    entry = (
        f"\n## Suche vom {timestamp}\nAnfrage: {query}\nProvider: {provider}\n"
        f"Live-Suche: {'ja' if live_search else 'nein'}\n\n{result}\n"
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
    print(search_deal(" ".join(args.query)))
