"""Fail-closed OpenMontage workflow wiring and newline regression contracts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/openmontage.yml"
DAILY = ROOT / ".github/workflows/openmontage-daily.yml"
CONTROL = ROOT / "scripts/openmontage_control.py"
PLAN = ROOT / "scripts/openmontage_private_plan.py"

def audit():
    errors = []
    workflow = WORKFLOW.read_text(encoding="utf-8")
    daily = DAILY.read_text(encoding="utf-8")
    control = CONTROL.read_text(encoding="utf-8")
    plan = PLAN.read_text(encoding="utf-8")
    if "if: inputs.mode == 'erstellen'" not in workflow and "if: (inputs.mode == 'erstellen'" not in workflow:
        errors.append("ERSTELLEN_NOT_CONNECTED_TO_RENDER")
    if "creative_renderer" not in workflow and "openmontage_production" not in workflow:
        errors.append("RENDERER_NOT_DISPATCHED")
    if "openmontage_publish_preview" not in workflow or "if: inputs.mode == 'demo'" not in workflow:
        errors.append("PREVIEW_NOT_WIRED")
    if "Daily autonomous video production is NOT enabled" in daily:
        errors.append("DAILY_ONLY_READINESS")
    if "aber NICHT gestartet" in control:
        errors.append("TELEGRAM_JOB_NOT_DISPATCHED")
    if '"proposal": "AWAITING_APPROVAL"' in plan and '"storyboard": "BLOCKED"' in plan:
        errors.append("PRIVATE_PLAN_STORYBOARD_GATE")
    if ' + \'\\\\n\'' in workflow:
        errors.append("LITERAL_BACKSLASH_N_IN_PLAN_JSON")
    return errors

class WiringAuditTests(unittest.TestCase):
    def test_expected_known_gaps_are_explicit(self):
        self.assertEqual(set(audit()), {
            "ERSTELLEN_NOT_CONNECTED_TO_RENDER",
            "RENDERER_NOT_DISPATCHED",
            "DAILY_ONLY_READINESS",
            "TELEGRAM_JOB_NOT_DISPATCHED",
            "PRIVATE_PLAN_STORYBOARD_GATE",
            "LITERAL_BACKSLASH_N_IN_PLAN_JSON",
        })

    def test_no_crlf_or_escaped_newline_in_workflow_output(self):
        content = WORKFLOW.read_bytes()
        self.assertNotIn(b"\\r\\n", content)
        self.assertIn(b"f.write('claimed=' + str(claimed).lower() + '\\n')", content)

if __name__ == "__main__":
    unittest.main()
