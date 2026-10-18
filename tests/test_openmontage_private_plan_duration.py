from pathlib import Path
import unittest

class PrivatePlanDurationTests(unittest.TestCase):
    def test_editorial_duration_not_fixed(self):
        source = Path("scripts/openmontage_private_plan.py").read_text(encoding="utf-8")
        self.assertIn('target_duration=editorial_duration', source)
        self.assertIn('selected_duration_seconds', source)
        self.assertIn('duration_policy', source)
        self.assertNotIn('target_duration=60', source)
        self.assertNotIn('target_duration_seconds": 30', source)
