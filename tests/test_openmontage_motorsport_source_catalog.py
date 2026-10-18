import unittest
from integrations.openmontage.motorsport_source_catalog import SOURCES, REFRESH_POLICIES, find_sources, source_catalog_memory_lesson

class MotorsportSourceCatalogTest(unittest.TestCase):
    def test_primary_series_and_manufacturers(self):
        self.assertTrue(any(x["name"] == "MotoGP" for x in SOURCES))
        self.assertTrue(any(x["name"] == "WorldSBK" for x in SOURCES))
        self.assertTrue(any(x["name"] == "KTM" for x in SOURCES))
        self.assertTrue(any(x["name"] == "TRF1" for x in SOURCES))
    def test_season_facts_are_not_static(self):
        for topic in ("riders", "teams", "circuits", "calendar", "results"):
            self.assertIn(topic, REFRESH_POLICIES)
        self.assertIn("keine verifizierten Einzelfakten", source_catalog_memory_lesson())
        self.assertTrue(find_sources("results", "MotoGP"))
