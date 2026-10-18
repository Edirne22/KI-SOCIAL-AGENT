"""Automatic Media Sourcing & Rights Verification for OpenMontage V3 (Block 4 / P0-C).

Generates structured media_manifest.json payloads with strict license/rights verification
and non-infringing visual fallbacks.

Key Requirement (P0-C): Trusted domain whitelists (e.g. motogp.com, worldsbk.com) are news
sources and NEVER constitute media publishing licenses. Third-party videos/images without explicit
rights are always rejected and replaced with non-infringing synthetic graphics.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import media_policy

logger = logging.getLogger(__name__)


def evaluate_media_item(
    scene_number: int,
    media_req: str,
    media_url: Optional[str] = None,
    media_source: Optional[str] = None,
    media_license: Optional[str] = None,
    riders: Optional[List[str]] = None,
    series: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluates media rights strictly based on explicit license verification."""
    riders = riders or []
    origin = media_source or "OpenMontage-Synthetic"
    url = media_url or ""
    lic = (media_license or "").casefold().strip()

    # P0-C: A domain whitelist is NEVER automatically a media license.
    # Only explicitly confirmed owned assets or verified public/creative-commons licenses qualify.
    is_explicitly_licensed = lic in ("owned_content", "cc0", "public_domain", "explicit_permission_granted")

    if url and is_explicitly_licensed:
        license_status = "explicitly_licensed"
        allowed_usage = "unrestricted"
        rights_ok = True
        verification = f"PASS: Verified explicit license ({lic})"
        selected_format = "licensed_external_media"
    elif url:
        license_status = "unverified_third_party"
        allowed_usage = "restricted"
        # The external URL is rejected, but the replacement is an internally
        # generated synthetic scene with no third-party media usage.
        rights_ok = False
        verification = "MEDIA_RESEARCH_INCOMPLETE: third-party media not approved for rendering."
        selected_format = "synthetic_fallback"
    else:
        license_status = "synthetic_generated"
        allowed_usage = "unrestricted"
        rights_ok = False
        verification = "MEDIA_RESEARCH_INCOMPLETE: no real media provided for scene"
        selected_format = "synthetic_graphic"

    # Select non-infringing visual fallback asset if unverified
    if selected_format in ("synthetic_fallback", "synthetic_graphic"):
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
        # Never pass a rejected URL to a downloader or renderer.
        "media_url": url if selected_format == "licensed_external_media" else "",
        "rejected_media_url": url if selected_format == "synthetic_fallback" else "",
        "media_source": origin,
        "media_license": media_license or "none",
        "license_status": license_status,
        "allowed_usage": allowed_usage,
        "rights_verified": rights_ok,
        "external_media_accepted": selected_format == "licensed_external_media",
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
            media_license=sc.get("media_license"),
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
