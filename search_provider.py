"""Zentrale, sichere Such-Abstraktion für Deal-Hunter und spätere Agenten."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

PROVIDER_LOG = Path("memory/SEARCH_PROVIDER_LOG.md")
MODEL = "gemini-3.8-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
RETRY_DELAYS = (30, 60, 120)
APIFY_API_ROOT = "https://api.apify.com/v2/acts"
APIFY_DEAL_ACTOR = "datascraperes~google-serp-scraper"
APIFY_DEAL_MAX_CHARGE_USD = 0.01


def log_provider(query: str, provider: str, detail: str = "", live_search: bool | None = None) -> None:
    """Protokolliert nur technische Metadaten, nie Secrets oder private URLs."""
    PROVIDER_LOG.parent.mkdir(parents=True, exist_ok=True)
    existing = PROVIDER_LOG.read_text(encoding="utf-8") if PROVIDER_LOG.exists() else "# Suchanbieter-Protokoll\n"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {timestamp}\n- Anfrage: {query[:160]}\n- Provider: {provider}\n"
    if live_search is not None:
        entry += f"- Live-Suche: {'ja' if live_search else 'nein'}\n"
    if detail:
        entry += f"- Hinweis: {detail}\n"
    PROVIDER_LOG.write_text(existing.rstrip() + entry, encoding="utf-8")


def _result(provider: str, live_search: bool, results: list[dict], warning: str | None, answer: str) -> dict:
    return {
        "provider": provider,
        "live_search": live_search,
        "results": results,
        "warning": warning,
        "answer": answer,
    }


def _apify_charge_limit() -> float:
    """Erlaubt eine kleinere Grenze per Variable, nie mehr als einen US-Cent."""
    try:
        configured = float(os.environ.get("APIFY_DEAL_MAX_CHARGE_USD", APIFY_DEAL_MAX_CHARGE_USD))
    except ValueError:
        configured = APIFY_DEAL_MAX_CHARGE_USD
    return min(max(configured, 0.001), APIFY_DEAL_MAX_CHARGE_USD)


def _price_from_snippet(value: str) -> float | None:
    prices = [
        float(match.group(1).replace(".", "").replace(",", "."))
        for match in re.finditer(r"(?<![0-9])([0-9]{1,5}(?:[.,][0-9]{1,2})?)\s*(?:€|EUR)\b", value, re.IGNORECASE)
    ]
    return min(prices) if prices else None


def _search_apify(query: str, token: str, num_results: int) -> dict:
    """Sucht öffentliche Google-Treffer über Apify, ohne Shop-Login oder Kauf."""
    actor = os.environ.get("APIFY_DEAL_ACTOR", APIFY_DEAL_ACTOR).strip() or APIFY_DEAL_ACTOR
    limit = min(max(num_results, 1), 10)
    payload = {
        "queries": [query],
        "startPage": 1,
        "endPage": 1,
        "language": "de",
        "country": "de",
    }
    try:
        response = requests.post(
            f"{APIFY_API_ROOT}/{actor}/run-sync-get-dataset-items",
            params={"maxTotalChargeUsd": f"{_apify_charge_limit():.3f}"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
    except requests.RequestException as error:
        raise RuntimeError(f"Netzwerkfehler: {type(error).__name__}") from error
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code}")
    try:
        rows = response.json()
    except ValueError as error:
        raise RuntimeError("Actor lieferte kein JSON") from error
    if not isinstance(rows, list):
        raise RuntimeError("Actor lieferte kein Ergebnis-Array")

    results: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or row.get("link") or "").strip()
        if not url.startswith(("https://", "http://")):
            continue
        title = str(row.get("title") or url).strip()
        snippet = str(row.get("description") or row.get("snippet") or "").strip()
        results.append({"title": title, "url": url, "snippet": snippet})
        if len(results) >= limit:
            break
    if not results:
        raise RuntimeError("Keine verwertbaren öffentlichen Suchtreffer")

    offers = []
    for item in results:
        price = _price_from_snippet(f"{item['title']} {item['snippet']}")
        if price is not None:
            domain = urlparse(item["url"]).netloc.removeprefix("www.")
            offers.append((price, domain or "unbekannter Händler", item["url"]))
    lines = ["Live-Suche über Apify (öffentliche Google-Treffer):"]
    if offers:
        price, retailer, url = min(offers, key=lambda offer: offer[0])
        lines.extend(
            [
                "",
                "BESTES_ANGEBOT:",
                f"Preis: {price:.2f} €",
                f"Händler: {retailer}",
                f"URL: {url}",
                "Belegt: ja",
                "Hinweis: Preis stammt aus einem aktuellen Suchtreffer; bitte auf den Link tippen und im Shop prüfen.",
            ]
        )
    else:
        lines.append("Kein verifizierbarer Preis im Suchtreffer-Snippet gefunden – Links bitte direkt prüfen.")
    lines.append("")
    lines.append("Direkte Treffer (antippbar):")
    for index, item in enumerate(results, 1):
        snippet = f" – {item['snippet']}" if item["snippet"] else ""
        lines.append(f"{index}. {item['title']}\n   {item['url']}{snippet}")
    return _result("Apify-Google-Suche", True, results, None, "\n".join(lines))


def _valid_searxng_url(value: str) -> str | None:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    return value.rstrip("/")


def _search_searxng(query: str, base_url: str, num_results: int) -> dict:
    response = requests.get(
        f"{base_url}/search",
        params={"q": query, "format": "json", "categories": "general"},
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")
    data = response.json()
    raw_results = data.get("results")
    if not isinstance(raw_results, list) or not raw_results:
        raise ValueError("Keine verwertbaren Ergebnisse")
    results = []
    for item in raw_results[:num_results]:
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            continue
        results.append(
            {
                "title": str(item.get("title") or url).strip(),
                "url": url,
                "snippet": str(item.get("content") or item.get("snippet") or "").strip(),
            }
        )
    if not results:
        raise ValueError("Keine gültigen Ergebnislinks")
    lines = ["Live-Ergebnisse aus SearXNG – Preise und Verfügbarkeit bitte direkt beim Händler prüfen:"]
    for index, item in enumerate(results, 1):
        snippet = f" – {item['snippet']}" if item["snippet"] else ""
        lines.append(f"{index}. {item['title']}: {item['url']}{snippet}")
    return _result("SearXNG", True, results, None, "\n".join(lines))


def _gemini_request(api_key: str, prompt: str, grounded: bool) -> requests.Response:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if grounded:
        payload["tools"] = [{"google_search": {}}]
    return requests.post(
        API_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
        json=payload,
        timeout=120,
    )


def _gemini_answer(response: requests.Response) -> tuple[str, list[dict]]:
    data = response.json()
    candidate = (data.get("candidates") or [{}])[0]
    parts = ((candidate.get("content") or {}).get("parts") or [])
    answer = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
    if not answer:
        raise ValueError("Gemini hat keine verwertbare Antwort geliefert.")
    sources = []
    for chunk in (candidate.get("groundingMetadata") or {}).get("groundingChunks", []):
        web = chunk.get("web") or {}
        url = web.get("uri")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            sources.append({"title": web.get("title") or url, "url": url, "snippet": ""})
    return answer, list({item["url"]: item for item in sources}.values())


def _gemini_grounded(query: str, api_key: str, status_callback: Callable[[str], None] | None) -> dict | None:
    prompt = f"""Recherchiere dieses Produkt mit allen genannten Kriterien: {query}

Suche bevorzugt bei eBay, Amazon, AliExpress, Polo Motorrad, Louis, Reifen.com, Idealo, Geizhals und Google Shopping.
Erfinde keine Preise, Rabattcodes oder Links. Nenne nur aktuelle, durch die Websuche belegte Daten.

Wenn ein eindeutiges, verifizierbares Angebot mit Preis, Händler und direktem Link vorliegt, beginne exakt mit diesem Block:
BESTES_ANGEBOT:
Preis: 123,45 €
Händler: Name des Händlers
URL: https://direkter-link-zum-angebot
Belegt: ja

Danach folgen Alternativen, Versand, Verfügbarkeit, UVP/Ersparnis und öffentliche Rabattcodes jeweils mit Quelle.
Wenn kein Angebot vollständig belegbar ist, schreibe ausdrücklich: Kein verifiziertes Live-Angebot gefunden.
Ein Preis ohne Händler, Direktlink und Belegt: ja darf niemals als bestes Angebot formatiert werden."""
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            response = _gemini_request(api_key, prompt, grounded=True)
        except requests.RequestException as error:
            log_provider(query, "Gemini-Grounded", f"Netzwerkfehler: {type(error).__name__}", True)
            return None
        if response.status_code == 200:
            try:
                answer, sources = _gemini_answer(response)
            except ValueError:
                log_provider(query, "Gemini-Grounded", "Antwort ohne verwertbaren Inhalt", True)
                return None
            log_provider(query, "Gemini-Grounded", "Live-Websuche erfolgreich", True)
            return _result("Gemini-Grounded", True, sources, None, answer)
        if response.status_code != 429:
            log_provider(query, "Gemini-Grounded", f"HTTP {response.status_code}", True)
            return None
        log_provider(query, "Gemini-Grounded", f"Rate-Limit HTTP 429, Versuch {attempt + 1}", True)
        if attempt < len(RETRY_DELAYS):
            delay = RETRY_DELAYS[attempt]
            if status_callback:
                status_callback(f"⏳ Warte kurz – Rate-Limit erreicht. Nächster Versuch in {delay} Sekunden.")
            time.sleep(delay)
    return None


def _gemini_knowledge_fallback(query: str, api_key: str) -> dict | None:
    prompt = f"""Die Live-Websuche für diese Anfrage ist derzeit nicht verfügbar: {query}

Nenne nur allgemeine, zeitunabhängige Hinweise zu möglichen Händlerarten, Produktfamilien oder Auswahlkriterien.
Nenne keine aktuellen Preise, Rabattcodes, Verfügbarkeiten oder Links als Tatsachen.
Beginne eindeutig mit: Keine Live-Websuche verfügbar."""
    try:
        response = _gemini_request(api_key, prompt, grounded=False)
        if response.status_code != 200:
            log_provider(query, "Gemini-Fallback", f"HTTP {response.status_code}", False)
            return None
        answer, _ = _gemini_answer(response)
    except (requests.RequestException, ValueError):
        log_provider(query, "Gemini-Fallback", "Fallback nicht verfügbar", False)
        return None
    warning = "⚠️ Keine Live-Websuche verfügbar. Preise, Codes und Verfügbarkeit bitte selbst prüfen."
    log_provider(query, "Gemini-Fallback", "Wissens-Fallback ohne Live-Websuche", False)
    return _result("Gemini-Fallback", False, [], warning, f"{warning}\n\n{answer}\n\nBitte in 10 Minuten erneut versuchen.")


def search(query: str, num_results: int = 10, status_callback: Callable[[str], None] | None = None) -> dict:
    """Sucht Apify → SearXNG → Gemini Grounding → Gemini-Wissens-Fallback."""
    query = query.strip()
    if not query:
        raise ValueError("Bitte nenne ein Produkt.")

    apify_token = os.environ.get("APIFY_API_TOKEN", "").strip()
    if apify_token:
        try:
            result = _search_apify(query, apify_token, num_results)
            log_provider(query, "Apify-Google-Suche", f"${len(result['results'])} öffentliche Treffer; Kostenlimit ${_apify_charge_limit():.3f}", True)
            return result
        except RuntimeError as error:
            log_provider(query, "Apify-Google-Suche", f"Fallback: {error}", True)
    else:
        log_provider(query, "Apify-Google-Suche", "Nicht konfiguriert", None)

    configured_url = os.environ.get("SEARXNG_URL", "")
    if configured_url:
        base_url = _valid_searxng_url(configured_url)
        if not base_url:
            log_provider(query, "SearXNG", "Ungültige oder nicht sichere URL übersprungen", True)
        else:
            try:
                result = _search_searxng(query, base_url, num_results)
                log_provider(query, "SearXNG", f"{len(result['results'])} Ergebnisse", True)
                return result
            except (requests.RequestException, ValueError, RuntimeError) as error:
                log_provider(query, "SearXNG", f"Fallback: {type(error).__name__}", True)
    else:
        log_provider(query, "SearXNG", "Nicht konfiguriert", None)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Keine Live-Suche verfügbar: GEMINI_API_KEY fehlt und SearXNG ist nicht erreichbar.")
    grounded = _gemini_grounded(query, api_key, status_callback)
    if grounded:
        return grounded
    fallback = _gemini_knowledge_fallback(query, api_key)
    if fallback:
        return fallback
    log_provider(query, "Keine Suche", "Alle Suchanbieter nicht verfügbar", False)
    raise RuntimeError("⏳ Suche derzeit nicht möglich – bitte in 10 Minuten erneut versuchen.")
