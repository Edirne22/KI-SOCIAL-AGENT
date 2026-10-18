"""B73: actual R2 bytes -> verified scene renderer -> decodable MP4."""
from io import BytesIO
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.openmontage_private_media_stage import stage_private_scenes
from scripts.openmontage_render_verified import render_verified_research


class FakeR2:
    def __init__(self, payload):
        self.payload = payload

    def get_object(self, *, Bucket, Key):
        return {"Body": BytesIO(self.payload)}


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "ffmpeg and ffprobe required")
class RealPrivateMediaAcceptance(unittest.TestCase):
    def test_r2_original_to_decodable_mp4(self):
        from tests.test_openmontage_local_media import make_media
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            make_media(source)
            payload = source.read_bytes()
            job = "tg000000001234"
            prefix = f"private/v1/2026/10/18/{job}/"
            asset_id = "file00000001"
            manifest = {"schema": "MEDIA-JOB-MANIFEST-V1", "lane": "private",
                        "job_id": job, "prefix": prefix, "assets": [{
                            "asset_id": asset_id, "mime": "image/png",
                            "key": prefix + f"originals/{asset_id}/source.png",
                            "size": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest()}]}
            selections = [{"scene_number": 1, "asset_id": asset_id,
                           "media_license": "owned_content", "rights_verified": True}]
            staged = root / "stage"
            config = stage_private_scenes(FakeR2(payload), "bucket", manifest,
                                          selections, staged)
            with patch("scripts.openmontage_render_verified.verify_research_payload",
                       return_value={"verified_item_count": 1}), patch(
                       "openmontage_production.fc.verify_research_payload",
                       return_value={"verified_item_count": 1}), patch(
                       "scripts.openmontage_render_verified.build_storyboard",
                       return_value={"scenes": [{"scene_number": 1, "title": "Test",
                                                 "duration": 1.5}]}):
                result = render_verified_research({}, root / "output",
                                                  scene_config=config, media_root=staged)
            self.assertTrue(result["source_media_included"])
            movie = Path(result["video_file"])
            self.assertGreater(movie.stat().st_size, 1024)
            probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                    "-show_entries", "stream=codec_name",
                                    "-of", "default=noprint_wrappers=1", str(movie)],
                                   capture_output=True, text=True, check=True)
            self.assertIn("codec_name=h264", probe.stdout)


if __name__ == "__main__":
    unittest.main()
