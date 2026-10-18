import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from content_factory_core import JobStatus, ProductionJob
from integrations.openmontage.factory_pipeline import produce_verified_montage


class FactoryPipelineTests(unittest.TestCase):
    def setUp(self):
        self.job = ProductionJob("openmontage-pipeline")
        self.job.status = JobStatus.STORYBOARDING
        self.story = {
            "title": "MotoGP race result", "summary": "MotoGP race result",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "series": "MotoGP", "source_status": "official",
            "original_url": "https://www.motogp.com/en/news/result",
            "story_id": "verified-one",
        }

    def test_verified_pipeline_dispatches_authorized_render(self):
        with patch("integrations.openmontage.factory_pipeline.dispatch_openmontage", return_value=("rendered",)) as dispatch:
            result = produce_verified_montage(self.job, agent_role_id="07_video_optimization",
                research={"stories": [self.story]}, storage=object())
            self.assertEqual(result, ("rendered",))
            kwargs = dispatch.call_args.kwargs
            self.assertEqual(kwargs["agent_role_id"], "07_video_optimization")
            self.assertTrue(kwargs["media_manifest"]["all_rights_verified"])
            self.assertGreater(len(kwargs["storyboard"]["scenes"]), 0)

    def test_empty_research_fails_closed(self):
        with patch("integrations.openmontage.factory_pipeline.dispatch_openmontage") as dispatch:
            with self.assertRaises(ValueError):
                produce_verified_montage(self.job, agent_role_id="07_video_optimization",
                    research={"stories": []}, storage=object())
            dispatch.assert_not_called()

    def test_old_research_fails_closed(self):
        story = dict(self.story, published_at="2020-01-01T00:00:00+00:00")
        with patch("integrations.openmontage.factory_pipeline.dispatch_openmontage") as dispatch:
            with self.assertRaises(ValueError):
                produce_verified_montage(self.job, agent_role_id="07_video_optimization",
                    research={"stories": [story]}, storage=object())
            dispatch.assert_not_called()

    def test_wrong_state_fails_closed(self):
        self.job.status = JobStatus.READY_FOR_HUMAN
        with self.assertRaises(ValueError):
            produce_verified_montage(self.job, agent_role_id="07_video_optimization",
                research={"stories": [self.story]}, storage=object())


if __name__ == "__main__":
    unittest.main()
