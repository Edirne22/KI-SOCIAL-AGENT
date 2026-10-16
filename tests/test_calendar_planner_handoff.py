"""Calendar-to-planner contract, no network or model calls."""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch
import pytest
import weekly_plan as wp
from race import race_calendar as rc

def calendar(events=None, age=0):
    return json.dumps({"updated_at": (datetime.now(ZoneInfo("Europe/Berlin"))-timedelta(days=age)).isoformat(),
                       "events": events or []})

def test_canonical_calendar_excludes_bike_story_and_static_file():
    today=datetime.now(ZoneInfo("Europe/Berlin")).date()
    item={"date_start":today.isoformat(),"date_end":today.isoformat(),"series":"WorldSBK",
          "track":"Fixture track","source":"https://www.worldsbk.com/en/calendar",
          "source_excerpt":"fixture evidence","sessions":[],"bike_of_weekend":{"story":"UNVERIFIED"}}
    with patch.object(wp,"read",return_value=calendar([item])) as read:
        result=wp.calendar_context(today)
    read.assert_called_once_with("memory/RACE_CALENDAR.json",100000)
    assert "WorldSBK" in result and "UNVERIFIED" not in result
    assert "bedeuten nicht rennfrei" in result

@pytest.mark.parametrize("raw",["","{}",'{"events":null}',calendar(age=9)])
def test_missing_or_stale_calendar_fails(raw):
    with patch.object(wp,"read",return_value=raw), pytest.raises(RuntimeError):
        wp.calendar_context(datetime.now().date())

def test_partial_plan_not_accepted():
    with patch.object(wp,"calendar_context",return_value='{"events": []}'), patch.object(wp,"read",return_value="## Seriöse Clubs & Gruppen\n### Turkbirler"), \
         patch.object(wp,"get_context",return_value=""), patch.object(wp,"global_professional_context",return_value=""), \
         patch.object(wp,"quick_chat",return_value='["community_0"]') as chat:
        with pytest.raises(RuntimeError,match="unvollständig"):
            wp.generate_weekly_plan()
    chat.assert_called_once()

def test_running_weekend_is_included(tmp_path):
    today=datetime.now(ZoneInfo("Europe/Berlin")).date()
    path=tmp_path/"calendar.json"
    path.write_text(calendar([{"date_start":(today-timedelta(days=1)).isoformat(),
                              "date_end":(today+timedelta(days=1)).isoformat(),
                              "series":"WorldSBK","track":"Fixture","source":"https://www.worldsbk.com/en/calendar",
                              "source_excerpt":"Fixture official schedule"}]))
    with patch.object(rc,"CALENDAR_FILE",path):
        result=rc.confirmed_weekend()
    assert result[0]=="WorldSBK"

def test_missing_calendar_does_not_exit_successfully(tmp_path):
    with patch.object(rc,"CALENDAR_FILE",tmp_path/"missing"),pytest.raises(RuntimeError):
        rc.confirmed_weekend()

def test_followups_depend_on_calendar_success():
    from pathlib import Path
    for file in ("weekly-plan.yml","race-calendar.yml"):
        content=Path(".github/workflows",file).read_text()
        assert 'workflows: ["Update Race Calendar"]' in content
        assert "github.event.workflow_run.conclusion == 'success'" in content
