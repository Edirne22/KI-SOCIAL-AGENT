import unittest
from unittest.mock import patch
from scripts.guarded_development_agent import plan

class DevelopmentPlanTests(unittest.TestCase):
    def test_unapproved_issue_blocked(self):
        with self.assertRaises(ValueError):
            plan(999999)

    def test_missing_sources_reported_without_fake_success(self):
        with patch("scripts.guarded_development_agent.Path.is_file",side_effect=lambda path: str(path)=="docs/GUARDED_DEVELOPMENT_AGENT_BASICS.md"), patch("scripts.guarded_development_agent.Path.read_text",return_value="Auftrag #369"):
            result=plan(369)
        self.assertEqual(result["status"],"BLOCKED_MISSING_SOURCE")
        self.assertEqual(len(result["missing_prerequisites"]),5)
        self.assertFalse(result["automatic_merge"])
        self.assertFalse(result["automatic_deploy"])

    def test_all_sources_present_plan_only(self):
        with patch("scripts.guarded_development_agent.Path.is_file",return_value=True), patch("scripts.guarded_development_agent.Path.read_text",return_value="Auftrag #369"):
            result=plan(369)
        self.assertEqual(result["status"],"PLAN_ONLY_AWAITING_CODE_REVIEW")
        self.assertEqual(result["missing_prerequisites"],[])
        self.assertFalse(result["automatic_commit"])

if __name__=="__main__":
    unittest.main()
