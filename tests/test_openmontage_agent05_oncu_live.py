import unittest
from scripts.openmontage_agent05_oncu_live import run

class Agent05OncuTests(unittest.TestCase):
    def test_live_results_are_unverified_and_never_publish(self):
        def fake(query):
            return {"live_search": True, "provider": "mock", "results": [
                {"title": "official", "url": "https://example.org/news", "snippet": "unverified"}]}
        result = run(search=fake)
        self.assertEqual(result["status"], "DISCOVERY_COMPLETE_UNVERIFIED")
        self.assertEqual(len(result["attempts"]), 4)
        self.assertEqual(len(result["findings"]), 1)
        self.assertFalse(result["findings"][0]["claim_verified"])
        self.assertEqual(result["media_status"], "NO_MEDIA_CANDIDATES")
        self.assertFalse(result["production_started"])
        self.assertFalse(result["publication_authorized"])

    def test_no_live_provider_blocks(self):
        result = run(search=lambda q: {"live_search": False, "results": [], "warning": "NO_PROVIDER"})
        self.assertEqual(result["status"], "BLOCKED_NO_LIVE_SEARCH")
        self.assertEqual(result["findings"], [])

    def test_rate_limit_stops_further_requests(self):
        calls = []
        def fake(query):
            calls.append(query)
            return {"live_search": False, "warning": "GROQ_HTTP_429", "results": []}
        result = run(search=fake)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["status"], "BLOCKED_NO_LIVE_SEARCH")

    def test_custom_topic_queries(self):
        result = run(search=lambda q: {"live_search": False, "results": []},
                     queries=("BMW Motorrad official updates",))
        self.assertEqual(len(result["attempts"]), 1)
        self.assertEqual(result["topic"], "BMW Motorrad official updates")
