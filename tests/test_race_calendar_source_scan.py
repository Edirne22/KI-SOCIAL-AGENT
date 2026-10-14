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


def test_official_calendar_scanner_fetches_event_pages():
    calendar_url = "https://www.motogp.com/en/calendar"
    event_url = "https://www.motogp.com/en/calendar/2026/event/australia/abc"
    calendar = FakeResponse(
        '<html><body>Australia 22 - 25 Oct 2026 '
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
        '<html><body>Upcoming MotoGP news '
        '<a href="https://www.motogp.com/en/calendar/2026/event/australia/abc">event</a>'
        '</body></html>'
    )
    with patch.object(updater.requests, "get", return_value=page) as get:
        result = updater._scan_source(url, "secondary")

    assert "Upcoming MotoGP news" in result["text"]
    assert result["event_pages"] == []
    assert get.call_count == 1


if __name__ == "__main__":
    test_page_text_strips_executable_markup()
    test_official_calendar_scanner_fetches_event_pages()
    test_secondary_source_is_scanned_without_crawling_event_links()
    print("Race-calendar source scan tests: PASS")
