"""Static contract checks for the actual OpenMontage GitHub wiring."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/openmontage.yml"
DAILY = ROOT / ".github/workflows/openmontage-daily.yml"

class WiringContractTests(unittest.TestCase):
    def test_plan_json_uses_newline_not_literal_backslash_n(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("ensure_ascii=False, indent=2) + " + repr("\n").replace("\\n", "\\n"), text)
        self.assertNotIn("ensure_ascii=False, indent=2) + " + repr("\\\\n"), text)

    def test_workflow_modules_exist_and_parse(self):
        for name in ("scripts/openmontage_control.py",
                     "scripts/openmontage_load_private_request.py",
                     "scripts/openmontage_private_plan.py",
                     "scripts/openmontage_publish_preview.py",
                     "scripts/openmontage_daily_slot.py",
                     "openmontage_research.py",
                     "openmontage_storyboard.py",
                     "openmontage_production.py"):
            with self.subTest(module=name):
                ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)

    def test_wiring_gaps_are_visible(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        daily = DAILY.read_text(encoding="utf-8")
        self.assertIn("inputs.mode == 'demo'", workflow)
        self.assertNotIn("python -m openmontage_production", workflow)
        self.assertIn("Daily autonomous video production is NOT enabled", daily)
