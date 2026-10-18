import unittest

from scripts.openmontage_agent_chain_audit import audit_agent_chain


class AgentChainAuditTests(unittest.TestCase):
    def test_quickshifter_stops_before_render_without_real_media(self):
        from scripts.openmontage_quickshifter_research import quickshifter_research
        result = audit_agent_chain(quickshifter_research())
        self.assertEqual(result["status"], "BLOCKED_MEDIA_MISSING")
        self.assertFalse(result["production_started"])
        self.assertGreater(len(result["missing_media"]), 0)
        self.assertEqual([step["agent"] for step in result["trace"]],
                         ["05_research_synthesist", "fact_checker",
                          "creative_director", "07_video_optimization"])

    def test_empty_research_never_reaches_storyboard(self):
        result = audit_agent_chain({"stories": []})
        self.assertEqual(result["status"], "BLOCKED_NO_VERIFIED_RESEARCH")
        self.assertFalse(result["production_started"])
        self.assertEqual(len(result["trace"]), 2)


if __name__ == "__main__":
    unittest.main()
