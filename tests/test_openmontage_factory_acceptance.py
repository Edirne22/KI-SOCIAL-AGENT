"""B10 acceptance contract: real renderer is required; mock MP4 cannot pass acceptance."""
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from content_factory_core import JobStatus, ProductionJob
from integrations.openmontage.factory_pipeline import produce_verified_montage
from media_storage import LocalScratchStorage


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe unavailable")
class OpenMontageAcceptanceTests(unittest.TestCase):
    def test_real_renderer_mp4_and_factory_storage(self):
        job = ProductionJob("b10-acceptance")
        job.status = JobStatus.STORYBOARDING
        story = {
            "title": "MotoGP Sprint Ergebnis", "summary": "MotoGP Sprint Ergebnis",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "series": "MotoGP", "source_status": "official",
            "original_url": "https://www.motogp.com/en/news/test",
            "story_id": "b10-fixture",
        }
        with tempfile.TemporaryDirectory(prefix="b10-acceptance-") as temp:
            storage = LocalScratchStorage(Path(temp) / "media")
            results = produce_verified_montage(job, agent_role_id="07_video_optimization",
                research={"stories": [story]}, storage=storage, target_duration=30)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].machine, "openmontage")
            self.assertEqual(len(results[0].outputs), 1)
            media = results[0].outputs[0]
            self.assertEqual(media.mime_type, "video/mp4")
            self.assertGreater(media.size_bytes, 1024)
            self.assertTrue(storage.resolve_local(media).is_file())
            self.assertEqual(job.media[0], media)


if __name__ == "__main__":
    unittest.main()
