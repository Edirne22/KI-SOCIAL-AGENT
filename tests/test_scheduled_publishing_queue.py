from datetime import datetime
from zoneinfo import ZoneInfo
import publication_claim as pc
import racing_archive_query as aq

def test_future_schedule_is_not_publishable_and_due_is_publishable():
    future="""## Facebook
Status: FREIGEGEBEN
Geplant-fuer: 2026-09-28T20:00:00+02:00
Text:
Test
Quelle: https://example.com/story
Link-Preview: offiziell
"""
    before=datetime(2026,9,28,19,59,tzinfo=ZoneInfo("Europe/Berlin"))
    due=datetime(2026,9,28,20,0,tzinfo=ZoneInfo("Europe/Berlin"))
    assert not pc._is_publishable(future,"facebook",before)
    assert pc._is_publishable(future,"facebook",due)

def test_invalid_schedule_fails_closed():
    block="""## Facebook
Status: FREIGEGEBEN
Geplant-fuer: irgendwann spaeter
Text:
Test
Quelle: https://example.com/story
Link-Preview: offiziell
"""
    assert not pc._is_publishable(block,"facebook")

def test_unscheduled_remains_backward_compatible():
    block="""## Facebook
Status: FREIGEGEBEN
Text:
Test
Quelle: https://example.com/story
Link-Preview: offiziell
"""
    assert pc._is_publishable(block,"facebook")

def test_natural_hourly_schedule_uses_berlin_time():
    req=aq.parse_schedule_request("Nimm Nummer 2, 4 und 7 und poste sie ab 18 Uhr jede Stunde")
    assert req["selections"]==[2,4,7]
    assert req["interval_minutes"]==60
    assert req["timezone"]=="Europe/Berlin"
    assert req["start"][11:16]=="18:00"
