import unittest
from datetime import datetime, timezone
from scripts.openmontage_daily_slot import is_berlin_daily_slot


class DailySlotTests(unittest.TestCase):
    def test_winter(self):
        self.assertTrue(is_berlin_daily_slot(datetime(2026, 1, 15, 7, 0, tzinfo=timezone.utc)))
        self.assertFalse(is_berlin_daily_slot(datetime(2026, 1, 15, 6, 0, tzinfo=timezone.utc)))

    def test_summer(self):
        self.assertTrue(is_berlin_daily_slot(datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc)))
        self.assertFalse(is_berlin_daily_slot(datetime(2026, 7, 15, 7, 0, tzinfo=timezone.utc)))

    def test_requires_aware_datetime(self):
        with self.assertRaises(ValueError):
            is_berlin_daily_slot(datetime(2026, 7, 15, 6, 0))


if __name__ == "__main__":
    unittest.main()
