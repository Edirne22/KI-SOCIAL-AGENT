import unittest
from scripts.openmontage_agent05_live_sources import fetch_primary_sources


class Response:
    status_code = 200
    headers = {"Content-Type": "text/html"}
    content = ("<html><body><h1>Quickshifter</h1><p>" +
               "Quickshifter sensor engine ignition clutch shifting. " * 8 +
               "</p><script>ignore me</script></body></html>").encode()
    def raise_for_status(self):
        return None


class Session:
    def get(self, url, **kwargs):
        assert kwargs["allow_redirects"] is False
        assert kwargs["timeout"] == (5, 12)
        return Response()


class Agent05LiveTests(unittest.TestCase):
    def test_collects_primary_evidence_without_declaring_facts_verified(self):
        result = fetch_primary_sources("Wie funktioniert ein Quickshifter?", session=Session())
        self.assertEqual(result["status"], "EVIDENCE_COLLECTED")
        self.assertEqual(len(result["evidence"]), 2)
        self.assertFalse(result["evidence"][0]["independent_fact_verification"])
        self.assertNotIn("ignore me", result["evidence"][0]["source_excerpt"])

    def test_unsupported_topic_fails_closed(self):
        result = fetch_primary_sources("unknown topic", session=Session())
        self.assertEqual(result["status"], "UNSUPPORTED_TOPIC")
        self.assertEqual(result["evidence"], [])


if __name__ == "__main__":
    unittest.main()
