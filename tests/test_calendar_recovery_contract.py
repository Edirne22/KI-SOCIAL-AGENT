"""Offline regressions for interrupted scans and unsafe calendar inputs."""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch

import pytest
import weekly_plan as wp
from race import race_calendar as rc
from scripts import update_race_calendar as updater


def event():
    today = datetime.now(ZoneInfo("Europe/Berlin")).date()
    return {"series": "WorldSBK", "track": "Fixture",
            "date_start": (today - timedelta(days=1)).isoformat(),
            "date_end": (today + timedelta(days=1)).isoformat(),
            "source": "https://www.worldsbk.com/en/calendar",
            "source_excerpt": "Fixture official schedule", "sessions": []}


def payload(events=None, age=0):
    return {"updated_at": (datetime.now(ZoneInfo("Europe/Berlin")) - timedelta(days=age)).isoformat(),
            "events": [event()] if events is None else events}


@pytest.mark.parametrize("data", [None, [], {}, payload(age=9), payload(age=-1),
                                  {"updated_at": "2026-01-01", "events": [event()]}])
def test_poster_rejects_invalid_or_stale_calendar(tmp_path, data):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps(data))
    with patch.object(rc, "CALENDAR_FILE", path), pytest.raises(RuntimeError):
        rc.confirmed_weekend()


@pytest.mark.parametrize("change", [{"source": "https://example.org/calendar"},
                                    {"source_excerpt": ""}, {"series": "Formula1"},
                                    {"track": ""}, {"source": "https://www.motogp.com/en/calendar"}])
def test_poster_skips_unconfirmed_events(tmp_path, change):
    item = event() | change
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps(payload([item])))
    with patch.object(rc, "CALENDAR_FILE", path):
        assert rc.confirmed_weekend() is None


def test_poster_skips_broken_entry_and_keeps_valid_running_event(tmp_path):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps(payload([None, [], event()])))
    with patch.object(rc, "CALENDAR_FILE", path):
        assert rc.confirmed_weekend()[0] == "WorldSBK"


@pytest.mark.parametrize("data", [None, [], {"updated_at": None, "events": []}])
def test_weekly_invalid_envelope_is_controlled_failure(data):
    with patch.object(wp, "read", return_value=json.dumps(data)), pytest.raises(RuntimeError):
        wp.calendar_context(datetime.now().date())


def test_weekly_skips_malformed_entry():
    with patch.object(wp, "read", return_value=json.dumps(payload([None, event()]))):
        assert "WorldSBK" in wp.calendar_context(datetime.now(ZoneInfo("Europe/Berlin")).date())


@pytest.mark.parametrize("answer", [None, [], {}, 42])
def test_invalid_weekly_model_response_is_controlled_failure(answer):
    with patch.object(wp, "calendar_context", return_value="{}"), \
         patch.object(wp, "read", return_value=""), patch.object(wp, "get_context", return_value=""), \
         patch.object(wp, "global_professional_context", return_value=""), \
         patch.object(wp, "quick_chat", return_value=answer), pytest.raises(RuntimeError):
        wp.generate_weekly_plan()


def test_scanner_preserves_running_weekend_and_drops_finished_event(tmp_path, monkeypatch):
    monkeypatch.setenv("AGNES_API_KEY", "synthetic-only")
    current = event()
    finished = current | {"date_start": "2020-01-01", "date_end": "2020-01-03"}
    scanned = {series: [{"url": url, "role": "official", "text": current["source_excerpt"],
                         "event_pages": []}]
               for series, url in [("MotoGP", "https://www.motogp.com/en/calendar"),
                                   ("WorldSBK", current["source"]) ]}
    path = tmp_path / "calendar.json"
    with patch.object(updater, "CALENDAR_FILE", path), \
         patch.object(updater, "scan_calendar_sources", return_value=scanned), \
         patch.object(updater, "call_agnes_json", return_value={"events": [finished, current]}), \
         patch.object(updater, "fetch_bike_of_weekend", return_value=None):
        updater.update_calendar()
    assert json.loads(path.read_text())["events"] == [current | {"crosscheck_sources": []}]
    # Continue the actual scanner output through both consumers, without a live
    # model/image call or any publication. Repeating must not duplicate drafts.
    published = tmp_path / "published.md"
    with patch.object(rc, "CALENDAR_FILE", path), patch.object(rc, "OUT", tmp_path / "weekend.md"), \
         patch.object(rc, "EVENT_OVERRIDE", tmp_path / "absent-override.json"), \
         patch.object(rc, "PUBLISHED", published), patch.object(rc, "collect", return_value={}), \
         patch.object(rc, "create_poster", return_value=[tmp_path / f"{i}.jpg" for i in range(3)]):
        rc.main()
        rc.main()
    draft = published.read_text()
    assert draft.count("Status: ENTWURF") == 3
    assert "Status: FREIGEGEBEN" not in draft and "Status: GEPOSTET" not in draft
    assert "WorldSBK" in draft and current["source"] in draft
    with patch.object(wp, "read", return_value=path.read_text()):
        context = json.loads(wp.calendar_context(datetime.now(ZoneInfo("Europe/Berlin")).date()))
    assert context["events"][0]["source_excerpt"] == current["source_excerpt"]


def test_scanner_failure_retains_previous_calendar(tmp_path, monkeypatch):
    monkeypatch.setenv("AGNES_API_KEY", "synthetic-only")
    path = tmp_path / "calendar.json"
    previous = json.dumps(payload())
    path.write_text(previous)
    scanned = {s: [{"role": "official", "url": f"https://{s}.invalid", "text": "", "event_pages": []}]
               for s in ("MotoGP", "WorldSBK")}
    with patch.object(updater, "CALENDAR_FILE", path), \
         patch.object(updater, "scan_calendar_sources", return_value=scanned), \
         patch.object(updater, "call_agnes_json", return_value={"events": []}), pytest.raises(RuntimeError):
        updater.update_calendar()
    assert path.read_text() == previous
