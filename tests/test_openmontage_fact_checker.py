"""Unit tests for OpenMontage V3 Fact & Recency Verification (Block 2 / P0-B)."""
from datetime import datetime, timedelta, timezone
import pytest
from openmontage_fact_checker import check_recency, verify_story_facts, verify_research_payload


def test_recency_checker_fail_closed():
    now = datetime.now(timezone.utc)
    recent_iso = now.isoformat()
    old_iso = (now - timedelta(days=10)).isoformat()
    future_iso = (now + timedelta(days=2)).isoformat()

    # Recent date -> OK
    ok, msg = check_recency(recent_iso, max_days=7)
    assert ok is True

    # Missing date -> Fail-closed
    ok_missing, msg_missing = check_recency("", max_days=7)
    assert ok_missing is False
    assert "Missing publication date" in msg_missing

    # Future date -> Fail-closed
    ok_future, msg_future = check_recency(future_iso, max_days=7)
    assert ok_future is False
    assert "in the future" in msg_future

    # Old date -> Fail-closed
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

test_story_no_date = {
    "title": "Marc Marquez dominates Grand Prix session",
    "summary": "Marc Marquez posts top time.",
    "series": "MotoGP",
    "published_at": "",  # Missing!
    "source_status": "official",
}


def test_verify_story_facts():
    checked_valid = verify_story_facts(test_story_valid)
    assert checked_valid["fact_check_passed"] is True
    assert checked_valid["expected_series"] == "MotoGP"

    checked_no_date = verify_story_facts(test_story_no_date)
    assert checked_no_date["fact_check_passed"] is False
    assert any("Missing publication date" in err for err in checked_no_date["fact_errors"])


def test_verify_research_payload():
    research = {
        "prompt": "Test",
        "stories": [test_story_valid, test_story_no_date]
    }
    verified = verify_research_payload(research)
    assert verified["verified_item_count"] == 1
    assert verified["rejected_item_count"] == 1
    assert verified["stories"][0]["title"] == test_story_valid["title"]
