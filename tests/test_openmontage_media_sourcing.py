"""Unit tests for OpenMontage V3 Media Sourcing (Block 4)."""
import pytest
from openmontage_media_sourcing import evaluate_media_item, build_media_manifest


def test_evaluate_trusted_official_media():
    item = evaluate_media_item(
        scene_number=1,
        media_req="race_highlight",
        media_url="https://www.motogp.com/en/news/2026/highlight.mp4",
        media_source="motogp.com",
    )
    assert item["rights_verified"] is True
    assert item["license_status"] == "trusted_official"


def test_evaluate_unverified_third_party_triggers_fallback():
    item = evaluate_media_item(
        scene_number=2,
        media_req="race_highlight",
        media_url="https://www.youtube.com/watch?v=unauthorized_race_video",
        media_source="random_yt_channel",
        riders=["Marc Marquez"],
    )
    assert item["rights_verified"] is False
    assert item["selected_asset_type"] == "driver_info_card"
    assert "Marc Marquez" in item["fallback_details"]


def test_build_media_manifest():
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
