import unittest
from scripts.openmontage_private_plan import build_plan


class PrivatePlanningTests(unittest.TestCase):
    def test_plan_requires_research_and_does_not_fabricate_sources(self):
        result = build_plan({"request_id": "tg-123", "prompt": "MotoGP Türkçe"})
        self.assertEqual(result["topic"], "MotoGP Türkçe")
        self.assertEqual(result["status"], "NEEDS_RESEARCH")
        self.assertEqual(result["verified_sources"], [])
        self.assertEqual(result["storyboard"], [])


if __name__ == "__main__":
    unittest.main()
