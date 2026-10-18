import unittest
from scripts.openmontage_quickshifter_research import quickshifter_research
from openmontage_fact_checker import verify_research_payload

class QuickshifterAcceptanceResearch(unittest.TestCase):
    def test_technical_stories_are_evergreen_and_factcheckable(self):
        payload = quickshifter_research()
        checked = verify_research_payload(payload)
        self.assertEqual(checked["verified_item_count"], 5)
        self.assertEqual(checked["needs_date_verification_count"], 0)
        self.assertTrue(all(s["source_status"] == "official" for s in checked["stories"]))
        self.assertTrue(all(s["original_url"].startswith("https://www.ktm.com/") for s in checked["stories"]))
