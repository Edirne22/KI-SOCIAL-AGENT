import unittest
from scripts.agent21_runtime_diagnostics import build_report
class TestAgent21RuntimeDiagnostics(unittest.TestCase):
    def test_bounded_read_only_report(self):
        r=build_report({"run_id":"123","commit":"abc","machine":"private-asr","route":"/research/search","provider":"OpenRouter-Web","state":"failure","error_class":"OPENROUTER_REQUEST_ERROR","container_health":"passed","opencode_health":"passed"})
        self.assertEqual(r["schema"],"AGENT21-RUNTIME-DIAG-V1")
        self.assertEqual(r["mode"],"READ_ONLY")
        self.assertFalse(r["secret_values_logged"])
        self.assertEqual(r["error_class"],"OPENROUTER_REQUEST_ERROR")
    def test_newlines_are_stripped_and_state_fails_closed(self):
        r=build_report({"state":"evil\nstate","error_class":"x\nTOKEN=secret"})
        self.assertEqual(r["state"],"unknown")
        self.assertNotIn("\n",r["error_class"])
if __name__=="__main__": unittest.main()
