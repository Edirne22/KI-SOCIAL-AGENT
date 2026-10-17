"""Bounded synthetic renderer controls and opt-in actual FFmpeg regression."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from integrations.openmontage import creative_renderer as renderer


class CreativeTests(unittest.TestCase):
    def valid_probe(self):
        return {'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'pix_fmt': 'yuv420p',
             'width': 720, 'height': 1280, 'avg_frame_rate': '30/1', 'nb_read_frames': '426'},
            {'codec_type': 'audio', 'codec_name': 'aac'}],
            'format': {'duration': '14.2', 'size': '12345'}}

    def test_positive_probe(self):
        renderer.validate_probe(self.valid_probe())

    def test_reject_invalid_media(self):
        good = self.valid_probe()
        bad = [{}, {'streams': []}, copy.deepcopy(good), copy.deepcopy(good)]
        bad[2]['format']['duration'] = 'NaN'
        bad[3]['streams'].append({'codec_type': 'subtitle'})
        for key, value in [('width', 1280), ('height', 720), ('nb_read_frames', '425'),
                           ('codec_name', 'mpeg4'), ('pix_fmt', 'yuv444p'), ('avg_frame_rate', '25/1')]:
            item = copy.deepcopy(good)
            item['streams'][0][key] = value
            bad.append(item)
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ValueError):
                renderer.validate_probe(data)

    def test_fail_closed_on_existing_output_including_symlink(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(renderer, 'run') as run:
            root = Path(tmp)
            for path in (root, root / 'link'):
                if path != root:
                    path.symlink_to(root, target_is_directory=True)
                with self.assertRaises(FileExistsError):
                    renderer.render(path)
            run.assert_not_called()

    def test_failure_or_timeout_has_no_success_artifacts(self):
        for error in (RuntimeError('render failed'), subprocess.TimeoutExpired('ffmpeg', 240)):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'result'
                def fail(*args, **kwargs):
                    (out / 'rendering.mp4').write_bytes(b'incomplete')
                    raise error
                with patch.object(renderer, 'synthetic_image'), patch.object(renderer, 'run', side_effect=fail):
                    with self.assertRaises(type(error)):
                        renderer.render(out)
                self.assertEqual(list(out.iterdir()), [])

    def test_child_has_no_credentials_or_shell(self):
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'sentinel', 'R2_SECRET_ACCESS_KEY': 'sentinel'}), \
             patch.object(subprocess, 'run') as run:
            run.return_value.returncode = 0
            renderer.run(['ffmpeg', '-version'])
            kwargs = run.call_args.kwargs
            self.assertNotIn('shell', kwargs)
            self.assertNotIn('GITHUB_TOKEN', kwargs['env'])
            self.assertNotIn('R2_SECRET_ACCESS_KEY', kwargs['env'])
            self.assertEqual(kwargs['timeout'], 240)

    def test_fixed_timeline_and_three_distinct_transitions(self):
        graph = renderer.filter_graph()
        for effect in ('fade', 'wipeleft', 'circleopen'):
            self.assertIn('xfade=transition=' + effect, graph)
        self.assertIn('offset=3.400', graph)
        self.assertIn('offset=6.800', graph)
        self.assertIn('offset=10.200', graph)
        self.assertEqual(graph.count('zoompan='), 4)

    @unittest.skipUnless(os.environ.get('OPENMONTAGE_RENDER_E2E') == '1', 'explicit real render only')
    def test_real_synthetic_movie_audio_and_full_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'render'
            result = renderer.render(out)
            self.assertEqual(result['status'], 'verified')
            self.assertEqual(result['frames'], 426)
            self.assertGreater(result['bytes'], 10000)
            probe = json.loads((out / 'ffprobe.json').read_text())
            renderer.validate_probe(probe)
            # Samples across all three joins must decode and contain actual imagery.
            for second in (0.8, 3.7, 7.1, 10.5, 13):
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(second),
                    '-i', str(out / 'creative-demo.mp4'), '-frames:v', '1', '-vf', 'scale=32:32',
                    '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'])
                self.assertEqual(len(raw), 3072)
                self.assertGreater(max(raw) - min(raw), 80)


if __name__ == '__main__':
    unittest.main()
