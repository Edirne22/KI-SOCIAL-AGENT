"""Tests for direct official race-calendar page scanning."""
from unittest.mock import patch

from scripts import update_race_calendar as updater


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


def test_page_text_strips_executable_markup():
    text = updater._page_text(
        "<html><script>fake date</script><style>.x{}</style>"
        "<body>Australia <b>22 Oct</b></body></html>"
    )
    assert "Australia" in text
    assert "22 Oct" in text
    assert "fake date" not in text
    assert ".x" not in text


def test_page_text_keeps_calendar_json_but_drops_javascript():
    text = updater._page_text(
        '<script id="__NEXT_DATA__" type="application/json">{"session":"FP1 09:00"}</script>'
        '<script>const secret = "noise";</script>'
    )
    assert "FP1 09:00" in text
    assert "secret" not in text


def test_official_calendar_scanner_fetches_event_pages():
    calendar_url = "https://www.motogp.com/en/calendar"
    event_url = "https://www.motogp.com/en/calendar/2026/event/australia/abc"
    calendar = FakeResponse(
        '<html><body>Official Australia race calendar. Upcoming event dates and schedule details. '
        'Australia 22 - 25 Oct 2026 '
        f'<a href="{event_url}">Event schedule</a></body></html>'
    )
    event = FakeResponse("<html><body>FP1 09:00 Sprint 15:00 Race Sunday 14:00</body></html>")

    with patch.object(updater.requests, "get", side_effect=[calendar, event]) as get:
        result = updater._scan_source(calendar_url, "official")

    assert "Australia" in result["text"]
    assert result["event_pages"] == [{
        "url": event_url,
        "text": "FP1 09:00 Sprint 15:00 Race Sunday 14:00",
    }]
    assert get.call_count == 2
    assert get.call_args_list[1].args[0] == event_url


def test_secondary_source_is_scanned_without_crawling_event_links():
    url = "https://trf1.net/motor-sporlari/motogp/"
    page = FakeResponse(
        '<html><body>Upcoming MotoGP news from the official racing information pages. '
        'Confirmed calendar updates and event news. '
        '<a href="https://www.motogp.com/en/calendar/2026/event/australia/abc">event</a>'
        '</body></html>'
    )
    with patch.object(updater.requests, "get", return_value=page) as get:
        result = updater._scan_source(url, "secondary")

    assert "Upcoming MotoGP news" in result["text"]
    assert result["event_pages"] == []
    assert get.call_count == 1


def test_late_season_event_pages_are_included_with_bounded_deduplication():
    base = "https://www.worldsbk.com"
    links = [f"/en/calendar/event/2026-{i:02}" for i in range(30)]
    markup = "Official calendar source " * 6 + "".join(f'<a href="{p}">Round</a>' for p in links)
    markup += f'<a href="{links[0]}">Duplicate</a><a href="https://evil.invalid/calendar/event/x">Bad</a>'
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return FakeResponse(markup if url == base + "/en/calendar" else "Official schedule")
    with patch.object(updater.requests, "get", side_effect=get):
        result = updater._scan_source(base + "/en/calendar", "official")
    assert base + links[11] in [p["url"] for p in result["event_pages"]]
    assert len(result["event_pages"]) == 24
    assert len(calls) == 25 and len(set(calls)) == 25


def test_shared_calendar_is_fetched_once_and_reused_for_each_series():
    url = "https://www.worldsbk.com/en/calendar"
    sources = {s: [{"url": url, "role": "official"}] for s in ("WorldSBK", "WorldSSP", "WorldSPB")}
    row = {"url": url, "role": "official", "text": "Official fixture", "event_pages": []}
    with patch.object(updater, "CALENDAR_SOURCES", sources), patch.object(updater, "_scan_source", return_value=row) as scan:
        result = updater.scan_calendar_sources()
    scan.assert_called_once_with(url, "official")
    assert all(result[s] == [row] for s in sources)


def test_shared_unavailable_source_has_no_silent_repeated_attempts():
    url = "https://www.worldsbk.com/en/calendar"
    sources = {s: [{"url": url, "role": "official"}] for s in ("WorldSBK", "WorldSSP")}
    with patch.object(updater, "CALENDAR_SOURCES", sources), \
         patch.object(updater, "_scan_source", side_effect=updater.requests.Timeout("fixture")) as scan:
        result = updater.scan_calendar_sources()
    scan.assert_called_once_with(url, "official")
    assert result == {s: [] for s in sources}


if __name__ == "__main__":
    test_page_text_strips_executable_markup()
    test_page_text_keeps_calendar_json_but_drops_javascript()
    test_official_calendar_scanner_fetches_event_pages()
    test_secondary_source_is_scanned_without_crawling_event_links()
    test_late_season_event_pages_are_included_with_bounded_deduplication()
    test_shared_calendar_is_fetched_once_and_reused_for_each_series()
    test_shared_unavailable_source_has_no_silent_repeated_attempts()
    print("Race-calendar source scan tests: PASS")
