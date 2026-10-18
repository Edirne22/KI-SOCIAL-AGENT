"""Automatic Media Sourcing & Rights Verification for OpenMontage V3 (Block 4).

Generates structured media_manifest.json payloads with strict license/rights verification
and non-infringing visual fallbacks.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import media_policy

TRUSTED_SOURCES_PATH = Path("config/TRUSTED_MEDIA_SOURCES.json")


def load_trusted_sources() -> List[str]:
    defaults = ["motogp.com", "worldsbk.com", "tmf.org.tr", "motoetkinlik.com", "motoetkinlik"]
    if TRUSTED_SOURCES_PATH.is_file():
        try:
            data = json.loads(TRUSTED_SOURCES_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return list(data.keys()) + defaults
            elif isinstance(data, list):
                return data + defaults
        except Exception:
            pass
    return defaults


def evaluate_media_item(
    scene_number: int,
    media_req: str,
    media_url: Optional[str] = None,
    media_source: Optional[str] = None,
    riders: Optional[List[str]] = None,
    series: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluates media rights and assigns safe visual fallback if rights are unconfirmed."""
    trusted_sources = load_trusted_sources()
    riders = riders or []

    origin = media_source or "OpenMontage-Synthetic"
    url = media_url or ""

    url_low = url.casefold()
    source_low = origin.casefold()

    is_trusted = any(domain.casefold() in url_low or domain.casefold() in source_low for domain in trusted_sources)

    # Check if external URL is provided
    if url and is_trusted:
        license_status = "trusted_official"
        allowed_usage = "editorial_reference"
        rights_ok = True
        verification = "PASS: Official trusted source metadata reference"
        selected_format = "external_reference"
    elif url:
        license_status = "unverified_third_party"
        allowed_usage = "restricted"
        rights_ok = False
        verification = "FAIL: Third-party race video without explicit licensing; trigger fallback"
        selected_format = "synthetic_fallback"
    else:
        license_status = "synthetic_generated"
        allowed_usage = "unrestricted"
        rights_ok = True
        verification = "PASS: Non-infringing synthetic graphics fallback"
        selected_format = "synthetic_graphic"

    # Select fallback asset if unverified
    if not rights_ok or selected_format == "synthetic_graphic":
        if riders:
            asset_type = "driver_info_card"
            fallback_details = f"Synthetic Driver Card for {', '.join(riders)}"
        elif series:
            asset_type = "series_calendar_graphic"
            fallback_details = f"Synthetic Calendar/Table Graphic for {series}"
        else:
            asset_type = "animated_text_scene"
            fallback_details = "Synthetic Animated Text & Dynamic Geometric Poster"
    else:
        asset_type = media_req
        fallback_details = "None (Original media approved)"

    return {
        "scene_number": scene_number,
        "media_request": media_req,
        "media_url": url,
        "media_source": origin,
        "license_status": license_status,
        "allowed_usage": allowed_usage,
        "rights_verified": rights_ok,
        "verification_result": verification,
        "selected_asset_type": asset_type,
        "fallback_details": fallback_details,
    }


def build_media_manifest(storyboard_data: Dict[str, Any]) -> Dict[str, Any]:
    """Builds a media_manifest.json structure from a storyboard."""
    scenes = storyboard_data.get("scenes", [])
    manifest_items = []

    for sc in scenes:
        item = evaluate_media_item(
            scene_number=sc.get("scene_number", 1),
            media_req=sc.get("media_request", "synthetic_graphic"),
            media_url=sc.get("media_url"),
            media_source=sc.get("media_source"),
            riders=sc.get("riders"),
            series=sc.get("series"),
        )
        manifest_items.append(item)

    all_rights_ok = all(m["rights_verified"] for m in manifest_items)

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_scenes": len(manifest_items),
        "all_rights_verified": all_rights_ok,
        "manifest": manifest_items,
    }
