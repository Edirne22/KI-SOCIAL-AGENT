"""Discovery Adapters for the Edirne 22 Content Factory.

Encapsulates external sources (Racing, Turkish Riders, RSS, YouTube, Apify, Telegram)
behind standard DiscoveryAdapter interfaces. All ingested text is treated as untrusted.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import os
import re
import hashlib
import html
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from content_factory_discovery import (
    DiscoveryAdapter, DiscoveryItem, DiscoverySource, SourceType,
    sanitize_untrusted_text, utc_now
)
from turkish_rider_names import canonical_rider, CANONICAL_ALIASES


class RacingDiscoveryAdapter:
    """Wraps existing racing discovery infrastructure (turkish_riders_scout_adapter, race_sources)."""

    name: str = "racing-editorial-scout"
    source_type: SourceType = SourceType.RACING

    def __init__(self, limit_per_source: int = 50) -> None:
        self.limit_per_source = limit_per_source

    def fetch_items(self, limit: int = 50) -> List[DiscoveryItem]:
        items: List[DiscoveryItem] = []
        try:
            from turkish_riders_scout_adapter import racing_editorial_scout
            scouted = racing_editorial_scout(limit_per_source=min(limit, self.limit_per_source))
            for idx, (title, url, series, source_name) in enumerate(scouted):
                if not title or not url:
                    continue
                item_id = f"racing-{hashlib.sha256(f'{url}|{title}'.encode('utf-8')).hexdigest()[:12]}"
                items.append(
                    DiscoveryItem(
                        item_id=item_id,
                        source_id=source_name or "RacingScout",
                        url=url,
                        title=title,
                        series=series or "Racing",
                        source_type=self.source_type.value,
                        provenance=f"racing:{source_name or 'scout'}",
                    )
                )
        except Exception as exc:
            print(f"[DISCOVERY] Racing adapter error: {exc}")
        return items[:limit]


class TurkishRiderDiscoveryAdapter:
    """Wraps dedicated Turkish Rider scout and alias logic."""

    name: str = "turkish-rider-scout"
    source_type: SourceType = SourceType.TURKISH_RIDER

    def __init__(self, limit_per_source: int = 50) -> None:
        self.limit_per_source = limit_per_source

    def fetch_items(self, limit: int = 50) -> List[DiscoveryItem]:
        items: List[DiscoveryItem] = []
        try:
            from turkish_riders_scout_adapter import turkish_web_scout
            scouted = turkish_web_scout(limit_per_source=min(limit, self.limit_per_source))
            for idx, (title, url, rider, series) in enumerate(scouted):
                if not title or not url:
                    continue
                item_id = f"trider-{hashlib.sha256(f'{url}|{title}'.encode('utf-8')).hexdigest()[:12]}"
                items.append(
                    DiscoveryItem(
                        item_id=item_id,
                        source_id="TurkishRiderScout",
                        url=url,
                        title=title,
                        series=series or "",
                        entities=[rider] if rider else [],
                        source_type=self.source_type.value,
                        provenance="turkish_rider:web_scout",
                        relevance=85,
                    )
                )
        except Exception as exc:
            print(f"[DISCOVERY] TurkishRider adapter error: {exc}")
        return items[:limit]


class RSSFeedDiscoveryAdapter:
    """Generic RSS/Atom ingestion using a real XML parser, not regex."""

    name: str = "rss-feed-adapter"
    source_type: SourceType = SourceType.RSS

    def __init__(self, feed_urls: Optional[List[str]] = None) -> None:
        self.feed_urls = feed_urls or [
            "https://www.motogp.com/en/news/rss",
            "https://www.worldsbk.com/en/news/rss",
        ]

    @staticmethod
    def _local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    @staticmethod
    def _text(element) -> str:
        return "".join(element.itertext()).strip() if element is not None else ""

    def _parse(self, raw: str, feed_url: str, limit: int) -> List[DiscoveryItem]:
        root = ET.fromstring(raw)
        entries = [e for e in root.iter() if self._local(e.tag) in ("item", "entry")]
        items: List[DiscoveryItem] = []
        for entry in entries[:limit]:
            children = list(entry)
            title_el = next((x for x in children if self._local(x.tag) == "title"), None)
            desc_el = next((x for x in children if self._local(x.tag) in ("description", "summary", "content")), None)
            link_el = next((x for x in children if self._local(x.tag) == "link"), None)
            title = html.unescape(self._text(title_el)).strip()
            desc = html.unescape(re.sub(r"<[^>]+>", "", self._text(desc_el))).strip()
            link = ""
            if link_el is not None:
                link = (link_el.attrib.get("href") or self._text(link_el)).strip()
            if not title or not link.startswith(("http://", "https://")):
                continue
            item_id = f"rss-{hashlib.sha256(f'{link}|{title}'.encode('utf-8')).hexdigest()[:12]}"
            items.append(DiscoveryItem(
                item_id=item_id,
                source_id=f"rss-{hashlib.sha256(feed_url.encode('utf-8')).hexdigest()[:8]}",
                url=link, title=title, text=desc[:1000],
                source_type=self.source_type.value, provenance=f"rss:{feed_url}",
            ))
        return items

    def fetch_items(self, limit: int = 50) -> List[DiscoveryItem]:
        items: List[DiscoveryItem] = []
        for feed_url in self.feed_urls:
            try:
                import requests
                resp = requests.get(feed_url, timeout=10, headers={"User-Agent": "KI-SOCIAL-AGENT/1.0"})
                if not resp.ok:
                    continue
                items.extend(self._parse(resp.text, feed_url, max(0, limit - len(items))))
            except (ET.ParseError, Exception) as exc:
                print(f"[DISCOVERY] RSS adapter error ({feed_url}): {exc}")
            if len(items) >= limit:
                break
        return items[:limit]


class YouTubeDiscoveryAdapter:
    """YouTube topic/source discovery adapter (strictly source discovery, no video piracy)."""

    name: str = "youtube-discovery-adapter"
    source_type: SourceType = SourceType.YOUTUBE

    def __init__(self, channel_urls: Optional[List[str]] = None) -> None:
        self.channel_urls = channel_urls or []

    def fetch_items(self, limit: int = 50) -> List[DiscoveryItem]:
        items: List[DiscoveryItem] = []
        # Checks if Apify or local YouTube search results exist in memory/INSPIRATION_YOUTUBE_APIFY.md
        memo_file = "memory/INSPIRATION_YOUTUBE_APIFY.md"
        if os.path.exists(memo_file):
            try:
                with open(memo_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # Parse title & URL lines from markdown
                raw_entries = re.findall(r"- Titel:\s*(.*?)\n\s*- URL:\s*(.*?)\n", content)
                for title, url in raw_entries[:limit]:
                    item_id = f"yt-{hashlib.sha256(f'{url}|{title}'.encode('utf-8')).hexdigest()[:12]}"
                    items.append(
                        DiscoveryItem(
                            item_id=item_id,
                            source_id="youtube-inspiration",
                            url=url.strip(),
                            title=title.strip(),
                            text="YouTube topic discovery candidate",
                            source_type=self.source_type.value,
                            provenance="youtube:inspiration",
                            raw_metadata={"usage": "topic_discovery_only", "no_piracy": True},
                        )
                    )
            except Exception as exc:
                print(f"[DISCOVERY] YouTube adapter memory parse error: {exc}")
        return items[:limit]


class ApifyDiscoveryAdapter:
    """Apify social media topic discovery adapter."""

    name: str = "apify-social-discovery"
    source_type: SourceType = SourceType.APIFY

    def fetch_items(self, limit: int = 50) -> List[DiscoveryItem]:
        items: List[DiscoveryItem] = []
        memo_file = "memory/INSPIRATION_APIFY.md"
        if os.path.exists(memo_file):
            try:
                with open(memo_file, "r", encoding="utf-8") as f:
                    content = f.read()
                raw_entries = re.findall(r"### Datensatz \d+\n- Titel:\s*(.*?)\n- Datum:\s*(.*?)\n- URL:\s*(.*?)\n", content)
                for title, date_str, url in raw_entries[:limit]:
                    if not url or url == "nicht verfügbar":
                        continue
                    item_id = f"apify-{hashlib.sha256(f'{url}|{title}'.encode('utf-8')).hexdigest()[:12]}"
                    items.append(
                        DiscoveryItem(
                            item_id=item_id,
                            source_id="apify-social",
                            url=url.strip(),
                            title=title.strip()[:150],
                            text=title.strip(),
                            source_type=self.source_type.value,
                            provenance="apify:social_inspiration",
                        )
                    )
            except Exception as exc:
                print(f"[DISCOVERY] Apify adapter error: {exc}")
        return items[:limit]


class TelegramDiscoveryAdapter:
    """Turns raw incoming Telegram commands/messages into structured DiscoveryItems."""

    name: str = "telegram-intake-adapter"
    source_type: SourceType = SourceType.TELEGRAM

    def create_item_from_message(self, message_text: str, update_id: str, sender: str = "telegram_user") -> DiscoveryItem:
        title = message_text.split("\n")[0][:100]
        item_id = f"tg-{hashlib.sha256(f'{update_id}|{message_text}'.encode('utf-8')).hexdigest()[:12]}"

        # Search for URLs inside message
        urls = re.findall(r"https?://\S+", message_text)
        url = urls[0] if urls else f"telegram://update/{update_id}"

        return DiscoveryItem(
            item_id=item_id,
            source_id="telegram-channel",
            url=url,
            title=title,
            text=message_text,
            source_type=self.source_type.value,
            provenance=f"telegram:{sender}:{update_id}",
            relevance=70,
        )
