import unittest
from unittest.mock import patch
from scripts.openmontage_agent05_team_dry_run import run_quickshifter_team_dry_run


class TeamDryRunTests(unittest.TestCase):
    @patch("scripts.openmontage_agent05_team_dry_run.fetch_primary_sources")
    def test_handoff_reaches_all_roles_without_rendering(self, fetch):
        fetch.return_value = {"status": "EVIDENCE_COLLECTED", "errors": [],
                              "evidence": [{"url": "https://www.ktm.com/en-dk/tech-guide/quickshifter.html"}]}
        result = run_quickshifter_team_dry_run()
        self.assertEqual(result["status"], "BLOCKED_CLAIM_VERIFICATION_AND_MEDIA")
        self.assertEqual(len(result["trace"]), 4)
        self.assertEqual(result["trace"][0]["source_count"], 1)
        self.assertEqual(result["trace"][1]["passed"], 5)
        self.assertEqual(len(result["missing_media"]), 8)
        self.assertFalse(result["production_started"])

    @patch("scripts.openmontage_agent05_team_dry_run.fetch_primary_sources")
    def test_no_live_evidence_blocks_team(self, fetch):
        fetch.return_value = {"status": "NO_LIVE_EVIDENCE", "evidence": [], "errors": []}
        result = run_quickshifter_team_dry_run()
        self.assertEqual(result["status"], "BLOCKED_NO_LIVE_SOURCES")
        self.assertEqual(len(result["trace"]), 1)
        self.assertFalse(result["production_started"])


if __name__ == "__main__":
    unittest.main()
