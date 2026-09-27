"""Deterministic MotoEtkinlik source adapter.

Separates editorial discovery from structured reference pages.  The adapter never
promotes a page to truth by itself; every emitted record keeps source lineage so
the existing Racing/Truth/QM gates can decide how it may be used.
"""
import html
import re
from urllib.parse import urljoin, urlsplit

import requests

BASE = "https://motoetkinlik.com/"
UA = {"User-Agent": "Mozilla/5.0 KI-SOCIAL-AGENT Motorcycle Racing Agency"}

NEWS_ENDPOINTS = {
    "MotoGP": urljoin(BASE, "kategori/motogp/"),
    "Moto2": urljoin(BASE, "kategori/moto2/"),
    "Moto3": urljoin(BASE, "kategori/moto3/"),
    "WorldSBK": urljoin(BASE, "kategori/wsbk/"),
    "WorldSSP": urljoin(BASE, "kategori/worldssp/"),
    "Racing": urljoin(BASE, "kategori/yaris/"),
    "Video": urljoin(BASE, "kategori/youtube/"),
}
REFERENCE_ENDPOINTS = {
    "results": urljoin(BASE, "motogp-yaris-sonuclari/"),
    "standings": urljoin(BASE, "motogp-puan-durumu/"),
    "riders": urljoin(BASE, "motogp-suruculeri/"),
    "calendar": urljoin(BASE, "motogp-yaris-takvimi/"),
}
KNOWN_ENDPOINTS = frozenset(
    urlsplit(u).path.rstrip("/") for u in (*NEWS_ENDPOINTS.values(), *REFERENCE_ENDPOINTS.values())
)


def _clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def endpoint_kind(url):
    path = urlsplit(url).path.rstrip("/")
    for kind, endpoint in REFERENCE_ENDPOINTS.items():
        if path == urlsplit(endpoint).path.rstrip("/"):
            return kind
    for series, endpoint in NEWS_ENDPOINTS.items():
        if path == urlsplit(endpoint).path.rstrip("/"):
            return "video" if series == "Video" else "news"
    return "article"


def _get(url, timeout=30):
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.text


def discover_news(fetch=_get, limit_per_endpoint=80):
    """Return same-site article links from verified category endpoints.

    Records are discovery hints only. Structured/reference endpoints, category
    navigation and assets are deliberately excluded from article candidates.
    """
    rows = []
    seen = set()
    for series, endpoint in NEWS_ENDPOINTS.items():
        try:
            page = fetch(endpoint)
        except Exception as exc:
            print(f"MOTOETKINLIK {series} FAIL: {type(exc).__name__}: {str(exc)[:100]}")
            continue
        count = 0
        for href, title in re.findall(r'href=["\\\']([^"\\\']+)["\\\'][^>]*>(.*?)</a>', page, re.I | re.S):
            url = urljoin(endpoint, html.unescape(href))
            parsed = urlsplit(url)
            text = _clean(title)
            path = parsed.path.rstrip("/")
            if (parsed.hostname or "").lower().removeprefix("www.") != "motoetkinlik.com":
                continue
            if parsed.scheme not in ("http", "https") or len(text) < 12:
                continue
            if path in KNOWN_ENDPOINTS or endpoint_kind(url) != "article":
                continue
            if path.startswith("/wp-content/") or path.startswith("/author/") or path.startswith("/tag/"):
                continue
            # MotoEtkinlik editorial articles are top-level slugs. This avoids
            # accidentally treating navigation, login/forum or race hubs as news.
            if not re.fullmatch(r"/[^/]+", path):
                continue
            if path in ("/giris-yap", "/kayit-ol", "/forum", "/iletisim") or url in seen:
                continue
            seen.add(url)
            rows.append({
                "kind": "video" if series == "Video" else "news",
                "series": "" if series in ("Racing", "Video") else series,
                "title": text,
                "url": url,
                "source_endpoint": endpoint,
                "source": "MotoEtkinlik",
            })
            count += 1
            if count >= limit_per_endpoint:
                break
        print(f"MOTOETKINLIK {series}: {count} article candidates")
    return rows


def reference_snapshots(fetch=_get):
    """Fetch deterministic reference pages with explicit lineage.

    Raw normalized text is intentionally returned rather than LLM-interpreted
    facts. Consumers can extract only the claim they need and retain the URL.
    """
    out = {}
    for kind, url in REFERENCE_ENDPOINTS.items():
        try:
            page = fetch(url)
        except Exception as exc:
            print(f"MOTOETKINLIK REFERENCE {kind} FAIL: {type(exc).__name__}: {str(exc)[:100]}")
            continue
        text = _clean(page)
        out[kind] = {
            "kind": kind,
            "url": url,
            "source": "MotoEtkinlik",
            "text": text,
        }
    return out


def source_map():
    """Stable endpoint registry for diagnostics/tests and downstream lineage."""
    return {"news": dict(NEWS_ENDPOINTS), "reference": dict(REFERENCE_ENDPOINTS)}
