"""Unit tests for OpenMontage V3 Shared Research Adapter (Block 1 / P0-A)."""
import pytest
from openmontage_research import build_research, _calculate_dedup_hash, _detect_series, _detect_source_status


def test_research_adapter_source_and_date_handling():
    mock_raw = [
        {
            "title": "Marc Marquez wins thrilling MotoGP Sprint",
            "url": "https://www.motogp.com/en/news/marquez-sprint",
            "summary": "Marc Marquez takes victory for Ducati Lenovo Team.",
            "source": "motogp.com",
            "series": "MotoGP",
            "published_at": "2026-10-12T10:00:00Z",
        },
        {
            "title": "Gerücht: Spekulationen um Teamwechsel 2027",
            "url": "https://www.speedweek.com/rumors-2027",
            "summary": "Gerüchten zufolge wechselt der Fahrer.",
            "source": "Official MotoGP Source Fake Name",  # Spoofed name!
            "series": "MotoGP",
        },
        {
            "title": "Journalistic Report on Lap Times",
            "url": "https://www.motorsport-magazin.com/lap-times",
            "summary": "Unconfirmed testing observations.",
            "source": "Motorsport Magazin",
            "series": "MotoGP",
        },
    ]

    research = build_research("Erstelle einen Film über MotoGP News", mock_items=mock_raw)

    assert research["item_count"] == 3
    s0 = research["stories"][0]
    assert s0["published_at"] == "2026-10-12T10:00:00Z"
    assert s0["source_status"] == "official"
    assert len(s0["confirmed_facts"]) > 0

    # Spoofed source name with non-official URL must NOT be treated as official
    s1 = research["stories"][1]
    assert s1["source_status"] == "rumor"
    assert s1["published_at"] == ""  # P0-A: missing published_at remains empty string

    # Journalistic source must NOT automatically put headlines in confirmed_facts
    s2 = research["stories"][2]
    assert s2["source_status"] == "journalistic"
    assert len(s2["confirmed_facts"]) == 0
    assert len(s2["unconfirmed_statements"]) > 0


def test_series_and_status_helpers():
    assert _detect_series("Grand Prix of Qatar MotoGP") == "MotoGP"
    assert _detect_series("Superbike race result WorldSBK") == "WorldSBK"
    assert _detect_source_status("https://www.motogp.com/en/news/1", "Official report") == "official"
    assert _detect_source_status("https://www.motogp.com/en/news/1", "Großes Gerücht in der Box") == "rumor"
    assert _detect_source_status("https://www.speedweek.com/1", "Official report") == "journalistic"
