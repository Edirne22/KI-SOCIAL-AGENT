import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.private_asr_deploy_guard import check_health


class RevisionGuardTests(unittest.TestCase):
    def setUp(self):
        self.good = {"ready": True, "research_runtime_revision": "research-v1",
                     "private_video_runtime_revision": "video-v3"}

    def check(self, data, status="200"):
        return check_health(json.dumps(data), status, "research-v1", "video-v3")

    def test_exact_ready_response_passes(self):
        self.assertEqual(self.check(self.good), "TARGET_REVISION_OK")

    def test_http_200_does_not_hide_revision_failures(self):
        for field, label in (("research_runtime_revision", "RESEARCH"),
                             ("private_video_runtime_revision", "VIDEO")):
            for value, suffix in (("old", "MISMATCH"), (None, "INVALID"), ([], "INVALID")):
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.check({**self.good, field: value}), label + "_REVISION_" + suffix)
            missing = dict(self.good)
            del missing[field]
            self.assertEqual(self.check(missing), label + "_REVISION_MISSING")

    def test_ready_is_strict_boolean_and_http_is_required(self):
        for value in (False, 1, "true", None):
            self.assertEqual(self.check({**self.good, "ready": value}), "NOT_READY")
        self.assertEqual(self.check(self.good, "503"), "HTTP_NOT_200")

    def test_invalid_json_and_shape_fail_closed(self):
        self.assertEqual(check_health("<html>", "200", "r", "v"), "INVALID_JSON")
        for value in ([], None, True, "private text"):
            self.assertEqual(self.check(value), "INVALID_OBJECT")

    def test_cli_never_logs_response_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "health.json"
            path.write_text(json.dumps({**self.good, "private_video_runtime_revision": "SECRET_PRIVATE_PREVIEW"}))
            result = subprocess.run([sys.executable, "scripts/private_asr_deploy_guard.py",
                                     str(path), "200", "research-v1", "video-v3"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), "PRIVATE_ASR_HEALTH_CHECK=VIDEO_REVISION_MISMATCH")
        self.assertEqual(result.stderr, "")

    def test_deploy_expectations_match_service_and_diagnostics_use_outcomes(self):
        workflow = Path(".github/workflows/private-asr-cloudflare-deploy.yml").read_text()
        tree = ast.parse(Path("infra/private-asr/service.py").read_text())
        constants = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in ("_research_runtime_revision", "_private_video_runtime_revision"):
                    constants[node.targets[0].id] = ast.literal_eval(node.value)
        self.assertIn('expected_research="' + constants["_research_runtime_revision"] + '"', workflow)
        self.assertIn('expected_video="' + constants["_private_video_runtime_revision"] + '"', workflow)
        self.assertIn("python3 scripts/private_asr_deploy_guard.py", workflow)
        self.assertIn('"container_health":"${{ steps.revision_health.outcome }}"', workflow)
        self.assertIn('"opencode_health":"${{ steps.opencode_health.outcome }}"', workflow)
        self.assertNotIn('"container_health":"passed"', workflow)


if __name__ == "__main__":
    unittest.main()
