"""Unit tests for OpenMontage V3 Automatic Scene Planning (Block 3)."""
import pytest
from openmontage_storyboard import build_storyboard, SUPPORTED_DURATIONS, SUPPORTED_FORMATS


def test_storyboard_builder_defaults():
    research = {
        "stories": [
            {
                "story_id": "story_1",
                "title": "Marc Marquez wins Sprint Race",
                "summary": "Marc Marquez dominates at MotorLand Aragon.",
                "series": "MotoGP",
                "riders": ["Marc Marquez"],
                "original_url": "https://motogp.com/1",
            },
            {
                "story_id": "story_2",
                "title": "Jorge Martin takes pole position",
                "summary": "Jorge Martin sets new lap record.",
                "series": "MotoGP",
                "riders": ["Jorge Martin"],
                "original_url": "https://motogp.com/2",
            },
        ]
    }

    storyboard = build_storyboard(
        research,
        target_duration=30,
        aspect_ratio="9:16",
        language="de",
        film_type="news",
    )

    assert storyboard["target_duration_seconds"] == 30
    assert storyboard["aspect_ratio"] == "9:16"
    assert storyboard["language"] == "de"
    assert storyboard["film_type"] == "news"
    assert storyboard["scene_count"] >= 3
    assert len(storyboard["scenes"]) == storyboard["scene_count"]

    # Check last scene has null transition
    scenes = storyboard["scenes"]
    assert scenes[-1]["transition"] is None
    for sc in scenes[:-1]:
        assert sc["transition"] in ("fade", "wipeleft", "circleopen")

    # Verify per-scene max title length (<= 40 chars for creative_renderer)
    for sc in scenes:
        assert len(sc["title"]) <= 40
        assert sc["duration"] >= 1.5 and sc["duration"] <= 15.0


def test_storyboard_turkish_language():
    research = {
        "stories": [
            {
                "story_id": "story_tr",
                "title": "Toprak Razgatlioglu lider basladi",
                "summary": "Toprak haftasonuna hizli basladi.",
                "series": "WorldSBK",
                "riders": ["Toprak Razgatlıoğlu"],
            }
        ]
    }

    sb = build_storyboard(research, target_duration=60, language="tr")
    assert sb["language"] == "tr"
    sc0 = sb["scenes"][0]
    assert sc0["speaker_text"].startswith("Haber 1:")
