import unittest
from scripts.openmontage_research_refresh import snapshot
from integrations.openmontage.motorsport_source_catalog import SOURCES

class HourlyResearchRefreshTest(unittest.TestCase):
    def test_health_is_not_claimed_as_verified_facts(self):
        report = snapshot(lambda url: (200, url))
        self.assertEqual(len(report["sources"]), len(SOURCES))
        self.assertFalse(report["facts_verified"])
        self.assertTrue(all(x["reachable"] for x in report["sources"]))
    def test_untrusted_redirect_does_not_count(self):
        report = snapshot(lambda url: (200, "https://untrusted.example/"))
        self.assertFalse(any(x["reachable"] for x in report["sources"]))
