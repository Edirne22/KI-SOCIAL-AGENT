import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ApprovalWiringTests(unittest.TestCase):
    def test_private_stages_do_not_require_approval(self):
        source = (ROOT / "scripts/openmontage_private_plan.py").read_text()
        self.assertIn('"proposal": "AUTO_AUTHORIZED"', source)
        self.assertIn('"storyboard": "AUTO_AUTHORIZED"', source)
        self.assertIn('"private_preview": "AUTO_AUTHORIZED"', source)
        self.assertIn('"publication": "AWAITING_APPROVAL"', source)
        self.assertNotIn('proposal": "AWAITING_APPROVAL"', source)
        self.assertNotIn('proposal"] == "APPROVED"', source)

    def test_publication_not_automatically_dispatched(self):
        source = (ROOT / ".github/workflows/openmontage.yml").read_text()
        self.assertNotIn("instagram.publish", source)
        self.assertNotIn("facebook.publish", source)
