import unittest
from unittest.mock import patch

from race.race_sources import ALLOWED_SERIES, is_allowed_series
from scripts import update_race_calendar as urc


class RaceSeriesFilterTests(unittest.TestCase):
    def test_f1_event_is_ignored(self):
        with patch("builtins.print") as log:
            self.assertFalse(is_allowed_series("Formel 1"))
        log.assert_any_call("Event ignoriert: Serie Formel 1 nicht erlaubt")

    def test_motogp_event_is_allowed(self):
        self.assertIn("MotoGP", ALLOWED_SERIES)
        self.assertTrue(is_allowed_series("MotoGP"))

    def test_bike_of_weekend_not_generated_for_f1(self):
        with patch.object(urc, "call_agnes_json") as llm:
            self.assertIsNone(urc.fetch_bike_of_weekend({"series": "Formel 1", "track": "Suzuka"}, "key"))
        llm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
