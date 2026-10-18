"""B78: real owner album staging through verified FFmpeg production."""
from io import BytesIO
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.openmontage_render_owner_album import render_owner_album


class FakeR2:
    def __init__(self, objects):
        self.objects = objects
    def get_object(self, *, Bucket, Key):
        return {"Body": BytesIO(self.objects[Key])}


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg required")
class OwnerAlbumEndToEnd(unittest.TestCase):
    def test_owner_album_renders_real_decodable_mp4(self):
        from tests.test_openmontage_local_media import make_media
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "source.png"
            make_media(image)
            data = image.read_bytes()
            job = "tgalbum" + "a" * 32
            prefix = f"private/v1/2026/10/18/{job}/"
            aid = "file00000001"
            index = "private/v1/telegram-album-index/" + job + ".json"
            key = prefix + "originals/" + aid + "/source.png"
            objects = {
                index: json.dumps({"job_id": job, "lane": "private",
                                   "owner_hash": sha256(b"123").hexdigest(),
                                   "created_at": "2026-10-18T19:00:00+00:00"}).encode(),
                prefix + "manifest.json": json.dumps({
                    "schema": "MEDIA-JOB-MANIFEST-V1", "lane": "private",
                    "job_id": job, "prefix": prefix,
                    "assets": [{"asset_id": aid, "mime": "image/png", "key": key,
                                "size": len(data), "sha256": sha256(data).hexdigest()}]}).encode(),
                key: data,
            }
            selections = [{"scene_number": 1, "asset_id": aid,
                           "media_license": "owned_content", "rights_verified": True}]
            with patch("scripts.openmontage_render_verified.verify_research_payload",
                       return_value={"verified_item_count": 1}), patch(
                       "openmontage_production.fc.verify_research_payload",
                       return_value={"verified_item_count": 1}), patch(
                       "scripts.openmontage_render_verified.build_storyboard",
                       return_value={"scenes": [{"scene_number": 1, "title": "Real Media",
                                                 "duration": 1.5}]}):
                report = render_owner_album(
                    client=FakeR2(objects), bucket="private", owner_chat="123",
                    authorized_chat="123", job_id=job, selections=selections,
                    research={}, output_dir=root / "rendered")
            self.assertTrue(report["source_media_included"])
            self.assertEqual(report["media_mode"], "licensed_local")
            movie = Path(report["video_file"])
            self.assertTrue(movie.is_file())
            probe = subprocess.run(["ffprobe", "-v", "error",
                                    "-show_entries", "stream=codec_name",
                                    "-select_streams", "v:0",
                                    "-of", "default=noprint_wrappers=1", str(movie)],
                                   capture_output=True, text=True, check=True)
            self.assertIn("codec_name=h264", probe.stdout)


if __name__ == "__main__":
    unittest.main()
