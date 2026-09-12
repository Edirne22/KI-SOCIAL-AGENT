"""Öffentliche, quellenbasierte Produktrecherche mit Gemini Search Grounding."""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

import requests

MEMORY_FILE = Path("memory/DEALS_FOUND.md")
LAST_QUERY_FILE = Path("memory/LAST_DEAL_QUERY.md")
MODEL = "gemini-3.8-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def search_deal(product_query: str) -> str:
    query = product_query.strip()
    if not query:
        raise ValueError("Bitte nenne ein Produkt nach 'deal:' oder 'suche:'.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY fehlt als GitHub Secret.")

    prompt = f"""Recherchiere dieses Produkt: {query}

Suche bevorzugt bei eBay, Amazon, AliExpress, Polo Motorrad, Louis, Reifen.com, Idealo, Geizhals und Google Shopping.
Liefere kompakt:
1. Produktname und Hersteller
2. Bestes bestätigtes Angebot: Variante, Preis, Währung, Händler, Link, Versandkosten-Hinweis und Verfügbarkeit
3. Drei Alternativen mit Preis, Händler und Link
4. UVP und Ersparnis nur falls belegt
5. Öffentlich bekannte Rabattcodes nur mit Quelle
6. Einen Hinweis für jeden unbestätigten Wert

Nutze ausschließlich Fakten aus der Websuche. Erfinde keine Preise, Rabattcodes oder Links.
Preise können sich ändern; nenne den Recherchezeitpunkt."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
    }
    response = requests.post(
        API_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
        json=payload,
        timeout=120,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Deal-Recherche fehlgeschlagen (HTTP {response.status_code}).")

    data = response.json()
    candidate = (data.get("candidates") or [{}])[0]
    parts = ((candidate.get("content") or {}).get("parts") or [])
    answer = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
    if not answer:
        raise RuntimeError("Gemini hat keine verwertbare Rechercheantwort geliefert.")

    sources = []
    for chunk in (candidate.get("groundingMetadata") or {}).get("groundingChunks", []):
        web = chunk.get("web") or {}
        url = web.get("uri")
        if url:
            sources.append(f"- {web.get('title') or url}: {url}")
    result = answer + ("\n\nQuellen aus Search Grounding:\n" + "\n".join(dict.fromkeys(sources)) if sources else "\n\nQuellen: nicht verfügbar")
    save_result(query, result)
    LAST_QUERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_QUERY_FILE.write_text(query, encoding="utf-8")
    return result


def save_result(query: str, result: str) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else "# Gefundene Deals\n"
    entry = f"\n## Suche vom {timestamp}\nAnfrage: {query}\n\n{result}\n"
    MEMORY_FILE.write_text(existing.rstrip() + entry, encoding="utf-8")


def compact_for_telegram(result: str, limit: int = 3500) -> str:
    prefix = "🛒 Deal-Suche\n"
    return prefix + (result[:limit].rstrip() + "\n\n⚠️ Preise vor dem Kauf selbst prüfen." if len(result) > limit else result + "\n\n⚠️ Preise vor dem Kauf selbst prüfen.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help="Produktanfrage")
    args = parser.parse_args()
    print(search_deal(" ".join(args.query)))
