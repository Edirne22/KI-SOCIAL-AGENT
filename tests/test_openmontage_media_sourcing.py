"""Unit tests for OpenMontage V3 Media Sourcing (Block 4 / P0-C)."""
import pytest
from openmontage_media_sourcing import evaluate_media_item, build_media_manifest


def test_trusted_domain_without_explicit_license_triggers_fallback():
    # P0-C: motogp.com / worldsbk.com URL without explicit license must fail rights_verified and trigger fallback!
    item = evaluate_media_item(
        scene_number=1,
        media_req="race_highlight",
        media_url="https://www.motogp.com/en/news/2026/highlight.mp4",
        media_source="motogp.com",
        media_license=None,  # No explicit license
        riders=["Marc Marquez"],
    )
    assert item["rights_verified"] is False
    assert item["license_status"] == "unverified_third_party"
    assert item["selected_asset_type"] == "driver_info_card"
    assert "Marc Marquez" in item["fallback_details"]


def test_explicitly_licensed_media_approved():
    item = evaluate_media_item(
        scene_number=1,
        media_req="race_highlight",
        media_url="https://assets.mybrand.com/video1.mp4",
        media_source="Owned Archive",
        media_license="owned_content",
    )
    assert item["rights_verified"] is True
    assert item["license_status"] == "explicitly_licensed"


def test_build_media_manifest_synthetic_graphics():
    storyboard = {
        "scenes": [
            {
                "scene_number": 1,
                "media_request": "driver_info_card",
                "riders": ["Toprak Razgatlıoğlu"],
                "series": "WorldSBK",
            },
            {
                "scene_number": 2,
                "media_request": "animated_text",
                "series": "WorldSBK",
            },
        ]
    }

    manifest = build_media_manifest(storyboard)
    assert manifest["total_scenes"] == 2
    assert manifest["all_rights_verified"] is True
    m1 = manifest["manifest"][0]
    assert m1["selected_asset_type"] == "driver_info_card"
