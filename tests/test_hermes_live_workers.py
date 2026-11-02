import unittest
from unittest.mock import patch
from integrations.openmontage.hermes_live_workers import run

class LiveWorkerTests(unittest.TestCase):
    @patch("integrations.openmontage.hermes_live_workers.research")
    def test_irrelevant_research_blocks(self, search):
        search.return_value={"results":[{"title":"Auto-Reifen", "url":"https://www.michelin.de/auto/reifen"}]}
        result=run("Michelin Power GP V1")
        self.assertEqual(result["status"],"BLOCKED")
        self.assertFalse(result["production_started"])
        self.assertFalse(result["publication_authorized"])

if __name__=="__main__":
    unittest.main()
