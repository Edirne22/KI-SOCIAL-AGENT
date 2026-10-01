"""Regression: import-qualified CLI runs on ephemeral GitHub runner from repository root."""
import importlib
import pathlib
import subprocess
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS=[
    ".github/workflows/cloud-ai-central.yml",
    ".github/workflows/ai-central-free-team-once.yml",
    ".github/workflows/ai-central-inbox-agent.yml",
]
class EntrypointRegression(unittest.TestCase):
    def test_all_production_workflows_use_module_entrypoint(self):
        for name in WORKFLOWS:
            with self.subTest(name=name):
                text=(ROOT/name).read_text(encoding="utf-8")
                self.assertNotIn("python scripts/cloud_ai_central.py",text)
                self.assertIn("python -m scripts.cloud_ai_central",text)
    def test_import_works_from_repo_root(self):
        module=importlib.import_module("scripts.cloud_ai_central")
        self.assertTrue(callable(module.challenge_evidence))
    def test_cli_help_does_not_call_provider_and_exits_zero(self):
        p=subprocess.run([sys.executable,"-m","scripts.cloud_ai_central","--help"],
            cwd=ROOT,capture_output=True,text=True,timeout=12,check=False)
        self.assertEqual(p.returncode,0,p.stderr[-200:])
        self.assertIn("--free-team",p.stdout)
        self.assertIn("--free-only",p.stdout)

if __name__=="__main__":unittest.main()
