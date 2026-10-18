"""Unit tests for OpenMontage V3 Shared Research Adapter (Block 1)."""
import pytest
from openmontage_research import build_research, _calculate_dedup_hash, _detect_series, _detect_source_status


def test_research_adapter_mock_data():
    mock_raw = [
        {
            "title": "Marc Marquez wins thrilling MotoGP Sprint",
            "url": "https://www.motogp.com/en/news/marquez-sprint",
            "summary": "Marc Marquez takes victory for Ducati Lenovo Team.",
            "source": "motogp.com",
            "series": "MotoGP",
        },
        {
            "title": "Toprak Razgatlioglu tests WorldSBK BMW in Jerez",
            "url": "https://www.motoetkinlik.com/toprak-jerez-test",
            "summary": "Toprak Razgatlıoğlu delivers strong lap times.",
            "source": "MotoEtkinlik",
            "series": "WorldSBK",
        },
        {
            "title": "Gerücht: Spekulationen um Teamwechsel 2027",
            "url": "https://www.speedweek.com/rumors-2027",
            "summary": "Gerüchten zufolge wechselt der Fahrer.",
            "source": "Speedweek",
            "series": "MotoGP",
        },
        # Duplicate test
        {
            "title": "Marc Marquez wins thrilling MotoGP Sprint",
            "url": "https://www.motogp.com/en/news/marquez-sprint-dup",
            "summary": "Marc Marquez takes victory for Ducati Lenovo Team.",
            "source": "motogp.com",
            "series": "MotoGP",
        },
    ]

    research = build_research("Erstelle einen Film über MotoGP News", mock_items=mock_raw)

    assert research["prompt"] == "Erstelle einen Film über MotoGP News"
    assert "stories" in research
    # Duplicate item should be excluded
    assert research["item_count"] == 2  # Only MotoGP items, WorldSBK filtered out by prompt filter!

    story0 = research["stories"][0]
    assert story0["title"] == "Marc Marquez wins thrilling MotoGP Sprint"
    assert "Marc Marquez" in story0["riders"]
    assert story0["source_status"] == "official"
    assert story0["series"] == "MotoGP"

    # Check rumor handling
    research_all = build_research("Motorsport News", mock_items=mock_raw)
    assert research_all["item_count"] == 3
    rumor_story = [s for s in research_all["stories"] if "Gerücht" in s["title"]][0]
    assert rumor_story["source_status"] == "rumor"
    assert len(rumor_story["unconfirmed_statements"]) > 0


def test_turkish_rider_tagging():
    mock_raw = [
        {
            "title": "Toprak Razgatlioglu leads test session",
            "url": "https://www.worldsbk.com/toprak-lead",
            "summary": "Toprak Razgatlıoğlu in front.",
            "source": "worldsbk.com",
        }
    ]
    res = build_research("WorldSBK", mock_items=mock_raw)
    assert res["item_count"] == 1
    story = res["stories"][0]
    assert "Toprak Razgatlıoğlu" in story["riders"]


def test_series_and_status_helpers():
    assert _detect_series("Grand Prix of Qatar MotoGP") == "MotoGP"
    assert _detect_series("Superbike race result WorldSBK") == "WorldSBK"
    assert _detect_source_status("motogp.com", "Official report") == "official"
    assert _detect_source_status("speedweek.com", "Großes Gerücht in der Box") == "rumor"
