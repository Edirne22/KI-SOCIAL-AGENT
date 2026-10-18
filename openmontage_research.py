"""Shared Research Adapter for OpenMontage V3.

Converts natural film prompts into structured news items (research.json)
using existing motorsport scouts, rosters, and source registries.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Dict, List, Optional

import content_factory_discovery as cfd
import motogp_quality_manager as gq
import turkish_rider_names as trn
from turkish_riders_scout_adapter import racing_editorial_scout, turkish_web_scout


def _calculate_story_id(url: str, title: str) -> str:
    raw = f"{url.strip().casefold()}|{title.strip().casefold()}"
    return f"story_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def _calculate_dedup_hash(title: str, summary: str) -> str:
    norm_title = re.sub(r"[^a-z0-9]", "", trn.fold(title))
    norm_summary = re.sub(r"[^a-z0-9]", "", trn.fold(summary))
    return hashlib.md5(f"{norm_title[:40]}:{norm_summary[:80]}".encode("utf-8")).hexdigest()[:16]


def _detect_series(text: str, default_series: str = "") -> str:
    low = text.casefold()
    if "motogp" in low or "moto gp" in low:
        return "MotoGP"
    if "worldsbk" in low or "superbike" in low or "wsbk" in low:
        return "WorldSBK"
    if "worldssp" in low or "supersport" in low:
        return "WorldSSP"
    if "moto2" in low:
        return "Moto2"
    if "moto3" in low:
        return "Moto3"
    return default_series or "Motorsport"


def _detect_source_status(source_name: str, text: str) -> str:
    low_src = source_name.casefold()
    low_text = text.casefold()

    if any(official in low_src for official in ["motogp.com", "worldsbk.com", "tmf.org.tr"]):
        return "official"

    rumor_words = ["gerücht", "rumor", "spekulation", "angeblich", "soll angeblich", "köpfe rollen", "gerüchten zufolge"]
    if any(w in low_text for w in rumor_words):
        return "rumor"

    return "journalistic"


def build_research(prompt: str, mock_items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Generates structured research payload (research.json representation) from prompt."""
    now_iso = datetime.now(timezone.utc).isoformat()
    prompt_low = prompt.casefold()

    filter_series = None
    for series_name in ["MotoGP", "WorldSBK", "WorldSSP", "Moto2", "Moto3"]:
        if series_name.casefold() in prompt_low:
            filter_series = series_name
            break

    candidates = []
    if mock_items is not None:
        raw_items = mock_items
    else:
        raw_items = []
        # Query editorial scout
        try:
            editorial_rows = racing_editorial_scout(limit_per_source=30)
            for title, url, series, source_name in editorial_rows:
                raw_items.append({
                    "title": title,
                    "url": url,
                    "series": series,
                    "source": source_name,
                    "summary": title,
                })
        except Exception:
            pass

        # Query Turkish scout
        try:
            turkish_rows = turkish_web_scout(limit_per_source=30)
            for title, url, rider, series in turkish_rows:
                raw_items.append({
                    "title": title,
                    "url": url,
                    "series": series,
                    "source": "TurkishWebScout",
                    "summary": f"{title} ({rider})",
                })
        except Exception:
            pass

    seen_dedup = set()
    stories = []

    for item in raw_items:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or item.get("original_url") or "").strip()
        summary = (item.get("summary") or title).strip()
        source_name = (item.get("source") or item.get("source_name") or "MotorsportSource").strip()

        if not title or not url:
            continue

        series = _detect_series(f"{title} {summary}", item.get("series", ""))
        if filter_series and series != filter_series and series != "Motorsport":
            continue

        dedup_hash = _calculate_dedup_hash(title, summary)
        if dedup_hash in seen_dedup:
            continue
        seen_dedup.add(dedup_hash)

        matched_riders = gq.rider_matches(f"{title} {summary}")
        turkish_rider = trn.canonical_rider(f"{title} {summary}")
        if turkish_rider and turkish_rider not in matched_riders:
            matched_riders.append(turkish_rider)

        status = _detect_source_status(source_name, f"{title} {summary}")

        confirmed_facts = []
        unconfirmed_statements = []
        if status == "rumor":
            unconfirmed_statements.append(title)
        else:
            confirmed_facts.append(title)

        story_id = item.get("story_id") or _calculate_story_id(url, title)

        stories.append({
            "story_id": story_id,
            "title": title,
            "summary": summary,
            "original_url": url,
            "source_name": source_name,
            "published_at": item.get("published_at") or now_iso,
            "retrieved_at": now_iso,
            "series": series,
            "riders": matched_riders,
            "teams": item.get("teams", []),
            "event": item.get("event", ""),
            "source_status": status,
            "confirmed_facts": confirmed_facts,
            "unconfirmed_statements": unconfirmed_statements,
            "media_hints": [f"Visuals for {r}" for r in matched_riders] or ["Motorsport action shot"],
            "dedup_hash": dedup_hash,
        })

    return {
        "prompt": prompt,
        "created_at": now_iso,
        "item_count": len(stories),
        "stories": stories,
    }
