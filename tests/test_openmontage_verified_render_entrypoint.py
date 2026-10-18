import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.openmontage_render_verified import render_verified_research


class VerifiedRenderTests(unittest.TestCase):
    def test_empty_research_rejected_before_render(self):
        with patch("scripts.openmontage_render_verified.produce_video") as render:
            with self.assertRaisesRegex(ValueError, "No verified research"):
                render_verified_research({"stories": []}, Path("/tmp/no-render"))
            render.assert_not_called()

    def test_stages_run_in_order_but_missing_media_blocks_render(self):
        verified = {"verified_item_count": 1, "stories": [{"title": "Test"}]}
        with patch("scripts.openmontage_render_verified.verify_research_payload",
                   return_value=verified) as facts, patch(
                   "scripts.openmontage_render_verified.build_storyboard",
                   return_value={"scenes": [{"scene_number": 1, "title": "Test"}]}) as board, patch(
                   "scripts.openmontage_render_verified.build_media_manifest",
                   return_value={"all_rights_verified": True, "manifest": []}) as media, patch(
                   "scripts.openmontage_render_verified.produce_video") as render:
            with self.assertRaisesRegex(RuntimeError, "MEDIA_RESEARCH_INCOMPLETE"):
                render_verified_research({"stories": [{"title": "Test"}]},
                                         Path("/tmp/mock"), duration=35)
        facts.assert_called_once()
        board.assert_called_once()
        media.assert_called_once()
        render.assert_not_called()
        self.assertEqual(board.call_args.kwargs["target_duration"], 35)

    def test_licensed_media_without_renderer_adapter_blocks_render(self):
        with patch("scripts.openmontage_render_verified.verify_research_payload",
                   return_value={"verified_item_count": 1}), patch(
                   "scripts.openmontage_render_verified.build_storyboard",
                   return_value={"scenes": [{"scene_number": 1, "title": "Test"}]}), patch(
                   "scripts.openmontage_render_verified.build_media_manifest",
                   return_value={"all_rights_verified": True, "manifest": [
                       {"scene_number": 1, "external_media_accepted": True, "rights_verified": True, "media_license": "owned_content", "media_url": "https://example.org/owned.mp4"}
                   ]}), patch("scripts.openmontage_render_verified.produce_video") as render:
            with self.assertRaisesRegex(RuntimeError, "SOURCE_MEDIA_RENDERER_NOT_CONNECTED"):
                render_verified_research({}, Path("/tmp/mock"))
            render.assert_not_called()


class LocalIntakeTests(unittest.TestCase):
    def config(self, path='fixture.png'):
        return {'all_rights_verified': True, 'scenes': [{
            'scene_number': 1, 'local_path': path, 'rights_verified': True,
            'media_license': 'cc0'}]}

    def invoke(self, root, config):
        with patch('scripts.openmontage_render_verified.verify_research_payload',
                   return_value={'verified_item_count': 1}), patch(
                   'openmontage_production.fc.verify_research_payload',
                   return_value={'verified_item_count': 1}), patch(
                   'scripts.openmontage_render_verified.build_storyboard',
                   return_value={'scenes': [{'scene_number': 1, 'title': 'Verified', 'duration': 1.5}]}), patch(
                   'scripts.openmontage_render_verified.build_media_manifest',
                   side_effect=AssertionError('No remote sourcing in local mode')):
            return render_verified_research({}, root / 'out', scene_config=config, media_root=root)

    def test_local_config_renders_actual_file(self):
        import tempfile
        from tests.test_openmontage_local_media import make_media
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_media(root / 'fixture.png')
            report = self.invoke(root, self.config())
            self.assertTrue(report['source_media_included'])
            self.assertEqual(report['media_mode'], 'licensed_local')
            self.assertTrue(Path(report['video_file']).is_file())

    def test_invalid_paths_reach_existing_b71_guard(self):
        import tempfile
        for name in ('missing.png', 'https://example.org/a.png', '../escape.png'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with self.assertRaisesRegex(ValueError, 'LOCAL_MEDIA_INVALID'):
                    self.invoke(root, self.config(name))
                self.assertFalse((root / 'out').exists())

    def test_rights_and_scene_identity_remain_required(self):
        import tempfile
        for key, value in (('rights_verified', False), ('scene_number', 2), ('media_license', 'unknown')):
            config = self.config()
            config['scenes'][0][key] = value
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with self.assertRaisesRegex(RuntimeError, 'LOCAL_MEDIA_INVALID'):
                    self.invoke(root, config)
                self.assertFalse((root / 'out').exists())

    def test_local_intake_still_requires_verified_research(self):
        with patch('scripts.openmontage_render_verified.verify_research_payload',
                   return_value={'verified_item_count': 0}), patch(
                   'scripts.openmontage_render_verified.produce_video') as produce:
            with self.assertRaisesRegex(ValueError, 'No verified research'):
                render_verified_research({}, Path('/tmp/unused-b72a'),
                                         scene_config=self.config(), media_root=Path('/tmp'))
            produce.assert_not_called()
