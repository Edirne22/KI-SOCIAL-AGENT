import ast
import json
import os
import textwrap
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


class RestartHintTests(unittest.TestCase):
    def run_step(self, code, body):
        workflow = Path(".github/workflows/private-asr-cloudflare-deploy.yml").read_text()
        step = workflow.split("      - name: Restart existing container once after deployment\n", 1)[1]
        script = textwrap.dedent(step.split("        run: |\n", 1)[1].split("      - name:", 1)[0])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mock = root / "curl"
            mock.write_text("#!/usr/bin/env python3\nimport os,sys\nfrom pathlib import Path\na=sys.argv\nPath(a[a.index('-o')+1]).write_text(os.environ['MOCK_BODY'])\nprint(os.environ['MOCK_CODE'],end='')\n")
            mock.chmod(0o755)
            script = script.replace("/tmp/container-restart", str(root / "response"))
            return subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                                  env={**os.environ, "PATH": directory + os.pathsep + os.environ["PATH"],
                                       "MOCK_CODE": code, "MOCK_BODY": body,
                                       "PRIVATE_ASR_INTERNAL_TOKEN": "synthetic"})

    def test_transient_503_defers_to_health_without_claiming_ready(self):
        result = self.run_step("503", '{"error":"PRIVATE_SECRET"}')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PRIVATE_ASR_DEPLOY_RESTART_DEFERRED_TO_HEALTH", result.stdout)
        self.assertNotIn("PRIVATE_SECRET", result.stdout + result.stderr)
        self.assertNotIn("RESTARTED_AND_PORT_READY", result.stdout)

    def test_202_requires_exact_ready_contract(self):
        good = self.run_step("202", '{"status":"container_restarted_ready"}')
        self.assertEqual(good.returncode, 0)
        for body in ('{}', '<html>', '{"status":"pending"}'):
            self.assertNotEqual(self.run_step("202", body).returncode, 0)

    def test_auth_and_unexpected_status_fail_closed(self):
        for code in ("401", "403", "404", "500", "200", "000"):
            with self.subTest(code=code):
                self.assertNotEqual(self.run_step(code, '{}').returncode, 0)


if __name__ == "__main__":
    unittest.main()
