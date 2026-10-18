from pathlib import Path
import unittest

class PrivatePlanDurationTests(unittest.TestCase):
    def test_storyboard_uses_configured_duration(self):
        source = Path("scripts/openmontage_private_plan.py").read_text(encoding="utf-8")
        self.assertIn('target_duration=plan["output_profile"]["target_duration_seconds"]', source)
        self.assertNotIn('target_duration=60', source)
