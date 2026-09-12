"""Öffentliche, quellenbasierte Produktrecherche mit Gemini Search Grounding."""

from __future__ import annotations

import argparse
import os
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import requests

MEMORY_FILE = Path("memory/DEALS_FOUND.md")
LAST_QUERY_FILE = Path("memory/LAST_DEAL_QUERY.md")
PROVIDER_LOG = Path("memory/SEARCH_PROVIDER_LOG.md")
MODEL = "gemini-3.8-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
RETRY_DELAYS = (30, 60, 120)


def log_provider(query: str, provider: str, detail: str = "") -> None:
    """Hält technische Suchwege getrennt von redaktionellen Erkenntnissen fest."""
    PROVIDER_LOG.parent.mkdir(parents=True, exist_ok=True)
    existing = PROVIDER_LOG.read_text(encoding="utf-8") if PROVIDER_LOG.exists() else "# Suchanbieter-Protokoll\n"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {timestamp}\n- Anfrage: {query[:160]}\n- Provider: {provider}\n"
    if detail:
        entry += f"- Hinweis: {detail}\n"
    PROVIDER_LOG.write_text(existing.rstrip() + entry, encoding="utf-8")


def _answer_from_response(response: requests.Response) -> tuple[str, list[str]]:
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
    return answer, list(dict.fromkeys(sources))


def _request(api_key: str, prompt: str, grounded: bool) -> requests.Response:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if grounded:
        payload["tools"] = [{"google_search": {}}]
    return requests.post(
        API_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
        json=payload,
        timeout=120,
    )


def _knowledge_fallback(query: str, api_key: str) -> str | None:
    """Letzter Fallback: nie als aktuelle Preis- oder Deal-Recherche ausgeben."""
    prompt = f"""Die Live-Websuche für diese Anfrage ist derzeit nicht verfügbar: {query}

Nenne ausschließlich allgemeine, zeitunabhängige Hinweise zu möglichen Händlerarten,
Produktfamilien oder Auswahlkriterien. Nenne keine aktuellen Preise, Rabattcodes,
Verfügbarkeiten oder Links als Tatsachen. Beginne mit: 'Keine Live-Websuche verfügbar.'"""
    try:
        response = _request(api_key, prompt, grounded=False)
        if response.status_code != 200:
            log_provider(query, "Gemini-Fallback", f"HTTP {response.status_code}")
            return None
        answer, _ = _answer_from_response(response)
        log_provider(query, "Gemini-Fallback", "Keine Live-Websuche; Antwort als Wissenshinweis markiert")
        return (
            f"⚠️ Keine Live-Websuche verfügbar (Rate-Limit).\n\n{answer}\n\n"
            "Bitte prüfe Preise selbst – bitte in 10 Minuten erneut versuchen."
        )
    except (requests.RequestException, ValueError, RuntimeError) as error:
        log_provider(query, "Gemini-Fallback", f"Fallback nicht verfügbar: {type(error).__name__}")
        return None


def search_deal(product_query: str, status_callback: Callable[[str], None] | None = None) -> str:
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

    response = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            response = _request(api_key, prompt, grounded=True)
        except requests.RequestException as error:
            log_provider(query, "Gemini-Grounded", f"Netzwerkfehler: {type(error).__name__}")
            break

        if response.status_code == 200:
            answer, sources = _answer_from_response(response)
            result = answer + (
                "\n\nQuellen aus Search Grounding:\n" + "\n".join(sources)
                if sources else "\n\nQuellen: nicht verfügbar"
            )
            log_provider(query, "Gemini-Grounded", "Live-Websuche erfolgreich")
            save_result(query, result)
            LAST_QUERY_FILE.parent.mkdir(parents=True, exist_ok=True)
            LAST_QUERY_FILE.write_text(query, encoding="utf-8")
            return result

        if response.status_code != 429:
            log_provider(query, "Gemini-Grounded", f"HTTP {response.status_code}")
            break

        log_provider(query, "Gemini-Grounded", f"Rate-Limit HTTP 429, Versuch {attempt + 1}")
        if attempt < len(RETRY_DELAYS):
            delay = RETRY_DELAYS[attempt]
            if status_callback:
                status_callback(f"⏳ Warte kurz – Rate-Limit erreicht. Nächster Versuch in {delay} Sekunden.")
            time.sleep(delay)

    fallback = _knowledge_fallback(query, api_key)
    if fallback:
        save_result(query, fallback)
        LAST_QUERY_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_QUERY_FILE.write_text(query, encoding="utf-8")
        return fallback

    log_provider(query, "Keine Suche", "Grounding und Wissens-Fallback nicht verfügbar")
    raise RuntimeError("⏳ Suche derzeit nicht möglich – bitte in 10 Minuten erneut versuchen.")


def save_result(query: str, result: str) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else "# Gefundene Deals\n"
    entry = f"\n## Suche vom {timestamp}\nAnfrage: {query}\n\n{result}\n"
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
