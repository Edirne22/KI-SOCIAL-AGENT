"""Unit tests for OpenMontage V3 Fact & Recency Verification (Block 2)."""
from datetime import datetime, timedelta, timezone
import pytest
from openmontage_fact_checker import check_recency, verify_story_facts, verify_research_payload


def test_recency_checker():
    now = datetime.now(timezone.utc)
    recent_iso = now.isoformat()
    old_iso = (now - timedelta(days=10)).isoformat()

    ok, msg = check_recency(recent_iso, max_days=7)
    assert ok is True

    ok_old, msg_old = check_recency(old_iso, max_days=7)
    assert ok_old is False
    assert "10.0 days old" in msg_old


test_story_valid = {
    "title": "Marc Marquez dominates Grand Prix session",
    "summary": "Marc Marquez posts top time in Ducati Lenovo Team debut.",
    "series": "MotoGP",
    "published_at": datetime.now(timezone.utc).isoformat(),
    "source_status": "official",
}

test_story_promo = {
    "title": "Behind the scenes vlog from ticket shop giveaway",
    "summary": "Catch up on tickets vlog episode.",
    "series": "MotoGP",
    "published_at": datetime.now(timezone.utc).isoformat(),
    "source_status": "official",
}

test_story_series_mismatch = {
    "title": "Toprak Razgatlioglu leads WorldSBK test in Jerez",
    "summary": "Toprak Razgatlioglu in WorldSBK action.",
    "series": "MotoGP",  # Mismatch!
    "published_at": datetime.now(timezone.utc).isoformat(),
    "source_status": "journalistic",
}


def test_verify_story_facts():
    checked_valid = verify_story_facts(test_story_valid)
    assert checked_valid["fact_check_passed"] is True
    assert checked_valid["expected_series"] == "MotoGP"
    assert "Marc Marquez" in checked_valid["detected_riders"]

    checked_promo = verify_story_facts(test_story_promo)
    assert checked_promo["fact_check_passed"] is False
    assert any("Promo/Vlog" in err for err in checked_promo["fact_errors"])

    checked_mismatch = verify_story_facts(test_story_series_mismatch)
    assert checked_mismatch["fact_check_passed"] is False
    assert any("Series mismatch" in err for err in checked_mismatch["fact_errors"])


def test_verify_research_payload():
    research = {
        "prompt": "Test",
        "stories": [test_story_valid, test_story_promo]
    }
    verified = verify_research_payload(research)
    assert verified["verified_item_count"] == 1
    assert verified["rejected_item_count"] == 1
    assert verified["stories"][0]["title"] == test_story_valid["title"]
