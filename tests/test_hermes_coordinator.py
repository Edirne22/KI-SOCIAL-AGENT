import unittest
from integrations.openmontage.hermes_coordinator import run_research, ROLES

class CoordinatorTests(unittest.TestCase):
    def test_missing_worker_blocks(self):
        r = run_research("Michelin Power GP V1", {})
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["history"][0]["reason"], "WORKER_MISSING")
        self.assertFalse(r["production_started"])
    def test_empty_fact_evidence_blocks(self):
        workers = {
            "research_discovery": lambda s: {"candidates": ["https://example.org/article"]},
            "source_reader": lambda s: {"documents": ["article text"]},
            "nemotron_analyst": lambda s: {"claims": ["GP V1"]},
            "fact_checker": lambda s: {"verified_claims": [{"source_url": "https://example.org/article"}]},
            "handoff": lambda s: {"report": "ready"},
        }
        r = run_research("Michelin Power GP V1", workers, max_retries=0)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["history"][-1]["role"], "fact_checker")
    def test_complete_evidence_handoff(self):
        workers = {
            "research_discovery": lambda s: {"candidates": ["https://example.org/article"]},
            "source_reader": lambda s: {"documents": ["article text"]},
            "nemotron_analyst": lambda s: {"claims": ["GP V1"]},
            "fact_checker": lambda s: {"verified_claims": [{"source_url": "https://example.org/article", "evidence_excerpt": "GP V1"}]},
            "handoff": lambda s: {"report": "ready"},
        }
        r = run_research("Michelin Power GP V1", workers)
        self.assertEqual(r["status"], "RESEARCH_READY")
        self.assertEqual([x["role"] for x in r["history"]], list(ROLES))
        self.assertFalse(r["production_started"])

if __name__ == "__main__":
    unittest.main()
