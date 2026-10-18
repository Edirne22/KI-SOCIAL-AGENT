"""B89: agent 05 remains independent of unavailable supplemental scouts."""
import unittest
from integrations.openmontage.parallel_scout_handoff import collect_parallel_research


class Tests(unittest.TestCase):
    def test_agent05_results_survive_scout_failure(self):
        def failed():
            raise RuntimeError("platform unavailable")
        result = collect_parallel_research(
            agent05=lambda: [{"title": "Manufacturer facts",
                              "url": "https://www.bmw-motorrad.com/"}],
            youtube=failed, instagram=lambda: [])
        self.assertEqual(len(result["agent05"]), 1)
        self.assertEqual(result["supplemental"], [])
        self.assertFalse(result["scout_status"]["youtube"])

    def test_social_links_are_discovery_not_media_rights(self):
        result = collect_parallel_research(
            agent05=lambda: [],
            youtube=lambda: [{"title": "Clip", "url": "https://www.youtube.com/watch?v=abc"}],
            instagram=lambda: [{"title": "Reel", "url": "https://www.instagram.com/reel/abc/"}])
        self.assertEqual(len(result["supplemental"]), 2)
        self.assertTrue(all(x["media_rights_verified"] is False for x in result["supplemental"]))

    def test_invalid_url_rejected(self):
        result = collect_parallel_research(
            agent05=lambda: [{"title": "bad", "url": "file:///etc/passwd"}],
            youtube=lambda: [], instagram=lambda: [])
        self.assertEqual(result["agent05"], [])


if __name__ == "__main__":
    unittest.main()
