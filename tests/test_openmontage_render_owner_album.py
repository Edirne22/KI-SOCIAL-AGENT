"""B75: verify album render CLI fails closed and cleans local staging."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.openmontage_render_owner_album import render_owner_album


class OwnerAlbumRenderTests(unittest.TestCase):
    def test_missing_selections_block_before_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("scripts.openmontage_render_owner_album.stage_owner_album") as stage:
                with self.assertRaisesRegex(ValueError, "selections"):
                    render_owner_album(client=object(), bucket="bucket",
                                       owner_chat="1", authorized_chat="1",
                                       job_id="tgalbum" + "a" * 32,
                                       selections=[], research={},
                                       output_dir=Path(tmp) / "out")
                stage.assert_not_called()

    def test_stage_render_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged_paths = []
            def stage(client, bucket, **kwargs):
                root = kwargs["destination"]
                root.mkdir(parents=True)
                (root / "scene_001.png").write_bytes(b"fixture")
                staged_paths.append(root)
                return {"all_rights_verified": True, "scenes": [
                    {"scene_number": 1, "local_path": "scene_001.png",
                     "rights_verified": True, "media_license": "owned_content"}]}
            with patch("scripts.openmontage_render_owner_album.stage_owner_album",
                       side_effect=stage), patch(
                       "scripts.openmontage_render_owner_album.render_verified_research",
                       return_value={"status": "COMPLETED", "video_file": "video.mp4"}) as render:
                result = render_owner_album(client=object(), bucket="bucket",
                                            owner_chat="1", authorized_chat="1",
                                            job_id="tgalbum" + "a" * 32,
                                            selections=[{"scene_number": 1}],
                                            research={"stories": []},
                                            output_dir=Path(tmp) / "out")
            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual(render.call_args.kwargs["scene_config"]["scenes"][0]["local_path"],
                             "scene_001.png")
            self.assertFalse(staged_paths[0].exists())


if __name__ == "__main__":
    unittest.main()
