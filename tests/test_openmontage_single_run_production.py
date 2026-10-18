from pathlib import Path
import unittest
import yaml

class SingleRunProduction(unittest.TestCase):
    def test_erstellen_plans_before_render(self):
        raw = Path(".github/workflows/openmontage.yml").read_text(encoding="utf-8")
        steps = yaml.safe_load(raw)["jobs"]["run"]["steps"]
        planner = next(i for i,s in enumerate(steps) if "scripts.openmontage_private_plan" in str(s.get("run","")))
        loader = next(i for i,s in enumerate(steps) if "scripts.openmontage_load_verified_research" in str(s.get("run","")))
        self.assertLess(planner,loader)
        self.assertIn("inputs.mode == 'erstellen'",steps[planner]["if"])
        self.assertIn("Privater Produktionsauftrag benötigt eine Telegram request_id",raw)
        self.assertNotIn("request_id']:\\n",raw)
