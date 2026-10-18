import unittest
from openmontage_fact_checker import verify_research_payload

class UndatedResearchTests(unittest.TestCase):
    def test_undated_news_held_for_review_not_render(self):
        result = verify_research_payload({"stories": [{
            "story_id": "undated-1", "title": "MotoGP Test",
            "original_url": "https://www.motogp.com/en/news/test",
            "summary": "Test"
        }]})
        self.assertEqual(result["verified_item_count"], 0)
        self.assertEqual(result["needs_date_verification_count"], 1)
        self.assertEqual(result["needs_date_verification"][0]["story_id"], "undated-1")

    def test_dated_evergreen_not_flagged_for_missing_date(self):
        result = verify_research_payload({"stories": [{
            "story_id": "tech-1", "title": "Technik erklärt",
            "original_url": "https://www.motogp.com/en/news/tech",
            "content_type": "technical_explainer", "source_status": "official"
        }]})
        self.assertEqual(result["needs_date_verification_count"], 0)
