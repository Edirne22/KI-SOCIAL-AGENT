from pathlib import Path
import unittest

class PrivateResearchHandoffContract(unittest.TestCase):
    def test_private_research_is_fact_checked_before_r2_handoff(self):
        source = Path("scripts/openmontage_private_plan.py").read_text(encoding="utf-8")
        self.assertIn("verify_research_payload(research)", source)
        self.assertIn('openmontage/research/{request_id}.json', source)
        self.assertIn('if checked_research["verified_item_count"]:', source)
        self.assertIn('for story in checked_research["stories"]', source)
        self.assertNotIn('for story in research["stories"]', source)
