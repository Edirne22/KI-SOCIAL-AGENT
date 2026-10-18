import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.openmontage_plan_job import plan


class PlanJobTests(unittest.TestCase):
    def test_rejects_empty_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                plan(" ", Path(d) / "plan")

    def test_rejects_unverified_news_without_files(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "plan"
            with patch("scripts.openmontage_plan_job.build_research", return_value={"stories": []}):
                with self.assertRaisesRegex(ValueError, "Keine frischen"):
                    plan("MotoGP", out)
            self.assertFalse(out.exists())

    def test_valid_verified_story_produces_plan_artifacts(self):
        from datetime import datetime, timezone
        item = {"title": "MotoGP offizieller Bericht", "summary": "Offizieller Bericht",
                "url": "https://www.motogp.com/en/news/test", "series": "MotoGP",
                "published_at": datetime.now(timezone.utc).isoformat()}
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "plan"
            from openmontage_research import build_research
            with patch("scripts.openmontage_plan_job.build_research", return_value=build_research("MotoGP", mock_items=[item])):
                result = plan("MotoGP", out)
            self.assertGreater(result["scenes"], 0)
            for name in ("research.json", "storyboard.json", "media_manifest.json"):
                self.assertTrue((out / name).is_file())


if __name__ == "__main__":
    unittest.main()
