import unittest
from unittest.mock import patch
from scripts.openmontage_private_plan import build_plan


class PrivateResearchContract(unittest.TestCase):
    def test_unverified_topic_stays_blocked(self):
        plan = build_plan({"request_id": "tg-12", "prompt": "MotoGP"})
        self.assertEqual(plan["status"], "NEEDS_RESEARCH")
        self.assertEqual(plan["verified_sources"], [])
        self.assertEqual(plan["storyboard"], [])


if __name__ == "__main__":
    unittest.main()
