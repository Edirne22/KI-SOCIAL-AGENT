"""Agent 05: bounded live primary-source retrieval for technical explainers.

A retrieved page is evidence to review, not automatic proof of any claim.
No media usage permission is inferred from a manufacturer website.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit
import requests

QUICKSHIFTER_SOURCES = (
    ("KTM Quickshifter+", "https://www.ktm.com/en-dk/tech-guide/quickshifter.html"),
    ("KTM Quickshifter+ DE", "https://www.ktm.com/de-at/tech-guide/quickshifter.html"),
)
MAX_HTML_BYTES = 600_000


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


def fetch_primary_sources(topic: str, *, session=None) -> dict:
    """Retrieve actual manufacturer text for a supported topic; fail closed otherwise."""
    if not any(term in topic.casefold() for term in ("quickshifter", "schaltassistent")):
        return {"topic": topic, "status": "UNSUPPORTED_TOPIC", "evidence": [], "errors": []}
    client = session or requests
    evidence, errors = [], []
    for name, url in QUICKSHIFTER_SOURCES:
        try:
            response = client.get(url, timeout=(5, 12), allow_redirects=False,
                                  headers={"User-Agent": "OpenMontage-Agent05/1.0"})
            response.raise_for_status()
            if response.status_code != 200 or len(response.content) > MAX_HTML_BYTES:
                raise ValueError("unexpected HTTP status or oversized document")
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                raise ValueError("not an HTML source")
            parser = _VisibleText()
            parser.feed(response.content.decode("utf-8", errors="replace"))
            excerpt = " ".join(parser.parts)
            if "quickshifter" not in excerpt.casefold() or len(excerpt) < 100:
                raise ValueError("expected technical source text absent")
            evidence.append({"source_name": name, "url": url,
                             "retrieved_at": datetime.now(timezone.utc).isoformat(),
                             "source_type": "manufacturer", "source_excerpt": excerpt[:6000],
                             "media_candidates": [], "independent_fact_verification": False})
        except (requests.RequestException, ValueError) as exc:
            errors.append({"url": url, "reason": type(exc).__name__})
    return {"topic": topic, "status": "EVIDENCE_COLLECTED" if evidence else "NO_LIVE_EVIDENCE",
            "evidence": evidence, "errors": errors}
