import unittest
from pathlib import Path


class PlanningWorkflowContractTests(unittest.TestCase):
    def test_planning_emits_artifact_and_never_claims_finished(self):
        workflow = Path(".github/workflows/openmontage.yml").read_text()
        self.assertIn("if: inputs.mode == 'planen'", workflow)
        self.assertIn("'status': 'NEEDS_RESEARCH'", workflow)
        self.assertIn("integrations/openmontage/.runtime/plan.json", workflow)
        self.assertIn("Keine bestätigte Recherche", workflow)


if __name__ == "__main__":
    unittest.main()
