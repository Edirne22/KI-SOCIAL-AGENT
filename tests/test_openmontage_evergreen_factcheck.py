import unittest
from openmontage_fact_checker import verify_story_facts

class EvergreenFactChecks(unittest.TestCase):
    def test_official_evergreen_explainer_without_date(self):
        item = {"title": "Schaltassistent erklärt", "summary": "Funktionsprinzip",
                "series": "Motorsport", "source_status": "official",
                "content_type": "technical_explainer", "published_at": ""}
        result = verify_story_facts(item)
        self.assertTrue(result["recency_passed"])
        self.assertTrue(result["fact_check_passed"])

    def test_news_without_date_still_rejected(self):
        item = {"title": "Neuer Rennbericht", "summary": "Meldung",
                "source_status": "official", "published_at": ""}
        self.assertFalse(verify_story_facts(item)["fact_check_passed"])

    def test_nonofficial_evergreen_still_rejected(self):
        item = {"title": "Schaltassistent erklärt", "summary": "Behauptung",
                "source_status": "journalistic", "content_type": "technical_explainer"}
        self.assertFalse(verify_story_facts(item)["fact_check_passed"])
