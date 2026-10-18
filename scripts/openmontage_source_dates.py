"""Conservative publication-date extraction from explicitly supplied HTML."""
from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
import json


class _Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates = []
        self.jsonld = False
        self.jsonld_parts = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "meta":
            name = (data.get("property") or data.get("name") or "").casefold()
            if name in ("article:published_time", "datepublished", "datepublishediso",
                        "pubdate", "date", "dc.date.issued"):
                if data.get("content"):
                    self.dates.append(data["content"])
        if tag == "script" and data.get("type", "").casefold() == "application/ld+json":
            self.jsonld = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.jsonld = False

    def handle_data(self, data):
        if self.jsonld:
            self.jsonld_parts.append(data)


def extract_publication_date(html: str) -> str:
    """Return explicit ISO8601 publication metadata; never infer crawl date."""
    parser = _Metadata()
    parser.feed(html)
    for raw in parser.jsonld_parts:
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            continue
        def visit(node):
            if isinstance(node, dict):
                value = node.get("datePublished")
                if isinstance(value, str):
                    parser.dates.append(value)
                for child in node.values():
                    visit(child)
            elif isinstance(node, list):
                for child in node:
                    visit(child)
        visit(payload)
    for value in parser.dates:
        try:
            datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            return value.strip()
        except (ValueError, TypeError):
            continue
    return ""
