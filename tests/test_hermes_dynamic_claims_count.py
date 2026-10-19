import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from openmontage_storyboard import build_storyboard
from scripts.hermes_toprak_production import test_media, execute, verify


class HermesDynamicClaimsCountTests(unittest.TestCase):
    def setUp(self):
        self.sample_story = {
            'story_id': 'claim-1',
            'title': 'Toprak test title',
            'summary': 'Toprak test summary statement.',
            'original_url': 'https://www.motogp.com/en/news/2026/10/19/test/1',
            'published_at': '2026-10-19T00:00:00+00:00',
            'source_status': 'journalistic',
            'content_type': 'news',
            'series': 'MotoGP',
            'riders': ['Toprak Razgatlioglu'],
            'evidence_excerpt': 'Toprak test summary statement from official source.',
        }

    def _make_research_report(self, count):
        stories = []
        for i in range(count):
            story = dict(self.sample_story)
            story['story_id'] = f'claim-{i+1}'
            story['title'] = f'Toprak claim {i+1}'
            story['summary'] = f'Toprak statement summary number {i+1}.'
            stories.append(story)
        return {'stories': stories, 'verified_item_count': count, 'rejected_item_count': 0}

    def test_build_storyboard_dynamic_claim_counts(self):
        for count in (1, 2, 3, 6):
            with self.subTest(count=count):
                report = self._make_research_report(count)
                board = build_storyboard(report, target_duration=36, aspect_ratio='9:16', language='de', film_type='news')
                self.assertGreaterEqual(len(board['scenes']), 1)
                self.assertIn('scenes', board)

    def test_test_media_manifest_structure_for_dynamic_counts(self):
        for count in (1, 2, 3, 6):
            with self.subTest(count=count):
                report = self._make_research_report(count)
                board = build_storyboard(report, target_duration=36, aspect_ratio='9:16', language='de', film_type='news')
                with patch('scripts.hermes_toprak_production.renderer.run') as mock_run:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        media_res = test_media(board, Path(temp_dir) / 'media')
                        self.assertTrue(media_res['all_rights_verified'])
                        self.assertEqual(len(media_res['manifest']), len(board['scenes']))

    @patch('scripts.hermes_toprak_production.validate_video')
    @patch('scripts.hermes_toprak_production.produce_video')
    @patch('scripts.hermes_toprak_production.test_media')
    @patch('scripts.hermes_toprak_production.research')
    def test_execute_and_verify_receipt_structure_dynamic_counts(self, mock_research, mock_test_media, mock_produce_video, mock_val_video):
        for count in (1, 2, 3, 6):
            with self.subTest(count=count):
                report = self._make_research_report(count)
                mock_research.return_value = {
                    'status': 'RESEARCH_READY',
                    'history': [{'role': '01_research_scout', 'verdict': 'PASS'}],
                    'handoff': {'report': report},
                    'source_reader': {'documents': [{'url': 'https://www.motogp.com/en/news/2026/10/19/test/1',
                                                     'published_at': '2026-10-19T00:00:00+00:00',
                                                     'retrieved_at': '2026-10-19T12:00:00Z',
                                                     'backend': 'test',
                                                     'sha256': 'abc12345'}]},
                }
                mock_test_media.side_effect = lambda board, root: {
                    'manifest': [{'scene_number': i+1, 'local_path': f'scene-{i}.mp4',
                                  'media_license': 'owned_content', 'rights_verified': True,
                                  'media_source': 'test', 'synthetic_test_media': True}
                                 for i in range(len(board['scenes']))],
                    'all_rights_verified': True
                }

                def fake_produce(checked, board, media, output_dir, media_root):
                    output_dir.mkdir(parents=True, exist_ok=True)
                    fake_mp4 = output_dir / 'creative-demo.mp4'
                    fake_mp4.write_bytes(b'fake_mp4_bytes_' + str(count).encode())
                    return {'video_file': str(fake_mp4), 'sha256': 'd820bc0a1332',
                            'duration_seconds': 36.0, 'scene_count': len(board['scenes'])}

                mock_produce_video.side_effect = fake_produce

                with tempfile.TemporaryDirectory() as temp_dir:
                    out_path = Path(temp_dir) / f'out_{count}'
                    execute(out_path, 'Toprak')
                    receipt_path = out_path / 'production-receipt.json'
                    self.assertTrue(receipt_path.is_file())
                    receipt = json.loads(receipt_path.read_text())
                    self.assertEqual(receipt['status'], 'PREVIEW_READY')
                    self.assertFalse(receipt['publication_authorized'])
                    self.assertTrue(receipt['synthetic_test_media'])

                    board = json.loads((out_path / 'storyboard.json').read_text())
                    self.assertGreaterEqual(len(board['scenes']), 1)


if __name__ == '__main__':
    unittest.main()
