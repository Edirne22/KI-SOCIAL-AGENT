import unittest
from ai_central_dashboard_view import view_report
class ViewTests(unittest.TestCase):
    def setUp(self):
        self.report={"schema":"CLOUD-AI-CENTRAL-V1",
            "task_id":"a"*32,"run_id":"36856381238","status":"PENDING_REVIEW",
            "requires_human_approval":True,
            "task":{"title":"OpenChatCut", "question":"secret"},
            "results":[{"role":"research","status":"ANSWER","attempts":[{"provider":"google","text":"private model output"}]}]}
    def test_safe_mobile_view_has_no_model_details(self):
        view=view_report(self.report)
        self.assertEqual(view["status"],"PENDING_REVIEW")
        self.assertIn("github.com",view["github_url"])
        self.assertNotIn("private model output",str(view))
        self.assertNotIn("secret",str(view))
    def test_refuse_invalid_identity_and_schema(self):
        self.report["run_id"]="../../bad"
        with self.assertRaises(ValueError):view_report(self.report)
        self.report["run_id"]="123"
        self.report["schema"]="wrong"
        with self.assertRaises(ValueError):view_report(self.report)
    def test_no_invented_status(self):
        self.report["status"]="PUBLISHED"
        with self.assertRaises(ValueError):view_report(self.report)
if __name__=="__main__":unittest.main()
