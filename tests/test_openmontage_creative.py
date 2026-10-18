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

    def test_workflow_is_secret_free_and_manual_bridge_is_gated(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/openmontage-creative.yml').read_text()
        for trigger in ('pull_request:', 'workflow_dispatch:', 'workflow_call:'):
            self.assertIn(trigger, workflow)
        self.assertIn('permissions:\n  contents: read', workflow)
        self.assertNotIn('secrets.', json.dumps(workflow))
        self.assertNotIn('pull_request_target', workflow)
        bridge = (root / '.github/workflows/openmontage-tests.yml').read_text().split('  creative-manual:')[1]
        self.assertIn("if: github.event_name == 'workflow_dispatch'", bridge)
        self.assertIn('uses: ./.github/workflows/openmontage-creative.yml', bridge)
        self.assertNotIn('secrets', bridge)

    def test_music_graph_has_bounded_gain_and_fades(self):
        graph = renderer.filter_graph(music=True)
        self.assertIn('volume=0.7', graph)
        self.assertIn('afade=t=in:d=0.15', graph)
        self.assertIn('afade=t=out:', graph)
        self.assertIn('[4:a]', graph)

    def test_reject_non_wav_music_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'audio.mp3'
            source.write_bytes(b'not audio')
            output = Path(tmp) / 'render'
            with self.assertRaises(ValueError):
                renderer.render(output, music=source)
            self.assertFalse(output.exists())

    @unittest.skipUnless(os.environ.get('OPENMONTAGE_MUSIC_E2E') == '1', 'explicit soundtrack render only')
    def test_real_local_wav_music_and_full_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            music = Path(tmp) / 'authorized-test.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'sine=frequency=440:sample_rate=48000:duration=2',
                            '-c:a', 'pcm_s16le', str(music)], check=True, timeout=30)
            out = Path(tmp) / 'result'
            report = renderer.render(out, music=music)
            self.assertEqual(report['music_source'], 'local_wav')
            renderer.verify(out / 'creative-demo.mp4')

    def test_default_scene_contract_is_preserved(self):
        scenes = renderer.normalize_scenes()
        self.assertEqual([s['title'] for s in scenes], list(renderer.TITLES))
        self.assertEqual(renderer.timeline(scenes), (14.2, 426))
        self.assertEqual([s['transition'] for s in scenes[:-1]], list(renderer.TRANSITIONS))

    def test_variable_lengths_and_single_scene_timeline(self):
        scenes = [{'title': 'A', 'duration': 2, 'transition': 'circleopen'},
                  {'title': 'B', 'duration': 3, 'transition': 'wipeleft'},
                  {'title': 'C', 'duration': 4}]
        self.assertEqual(renderer.timeline(renderer.normalize_scenes(scenes)), (7.8, 234))
        graph = renderer.filter_graph(scenes)
        self.assertIn('offset=1.400', graph)
        self.assertIn('offset=3.800', graph)
        self.assertIn('[3:a]', graph)
        self.assertNotIn('xfade=', renderer.filter_graph(scenes[-1:]))
        self.assertEqual(renderer.timeline(renderer.normalize_scenes(scenes[-1:])), (4, 120))

    def test_title_is_literal_not_filter_code(self):
        title = "Bülent: 100% ' [%{pts}] \\"
        graph = renderer.filter_graph([{'title': title, 'duration': 2}])
        self.assertNotIn(title, graph)
        self.assertIn('textfile=title-0.txt:expansion=none', graph)

    def test_reject_invalid_config_before_output_or_process(self):
        good = {'title': 'Test', 'duration': 2}
        bad = [[], {}, [good] * 9]
        for key, value in [('duration', True), ('duration', 0), ('duration', 1.49),
                           ('duration', 61), ('duration', 2.01), ('duration', float('nan')),
                           ('duration', float('inf')), ('duration', 10**400),
                           ('title', ''), ('title', 'x'*41), ('title', 'a\nb'),
                           ('title', '\x00'), ('zoom', 'evil'), ('motion', '$(id)'),
                           ('transition', 'fade'), ('path', '/private/photo.jpg')]:
            bad.append([dict(good, **{key: value})])
        bad.append([dict(good, transition='movie=/etc/passwd'), good])
        with tempfile.TemporaryDirectory() as tmp, patch.object(renderer, 'run') as run:
            out = Path(tmp) / 'unused'
            for scenes in bad:
                with self.subTest(scenes=scenes), self.assertRaises(ValueError):
                    renderer.render(out, scenes)
                self.assertFalse(out.exists())
            run.assert_not_called()

    def test_all_motion_modes_and_frame_boundary(self):
        for zoom in ('in', 'out', 'none'):
            for motion in ('left', 'right', 'none'):
                scenes = [{'title': 'OK', 'duration': 46/30, 'zoom': zoom, 'motion': motion}]
                self.assertEqual(renderer.timeline(renderer.normalize_scenes(scenes)), (46/30, 46))
                self.assertIn('trim=end_frame=46', renderer.filter_graph(scenes))

    def test_json_loading_is_bounded_and_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'scenes.json'
            for content in ('null', '{}', '{broken', ' ' * 32769):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    renderer.load_scenes(path)
            path.write_text('[{"title":"Dünya", "duration":2}]', encoding='utf-8')
            self.assertEqual(renderer.load_scenes(path)[0]['title'], 'Dünya')

    def test_probe_uses_configured_duration_and_frames(self):
        scenes = [{'title': 'Single', 'duration': 2}]
        probe = self.valid_probe()
        with self.assertRaises(ValueError):
            renderer.validate_probe(probe, scenes)
        probe['format']['duration'] = '2.0'
        probe['streams'][0]['nb_read_frames'] = '60'
        renderer.validate_probe(probe, scenes)

    @unittest.skipUnless(os.environ.get('OPENMONTAGE_SCENES_E2E') == '1', 'explicit flexible render only')
    def test_real_custom_and_single_scene_movies(self):
        scenes = [{'title': "Bülent: 100% ' [%{pts}]", 'duration': 1.5 + i/10,
                   'zoom': ('none', 'in', 'out')[i % 3],
                   'motion': ('none', 'left', 'right')[i % 3],
                   'transition': renderer.TRANSITIONS[i % 3] if i < 4 else None}
                  for i in range(5)]
        with tempfile.TemporaryDirectory() as tmp:
            for count, config in ((5, scenes), (1, [dict(scenes[0], transition=None)])):
                out = Path(tmp) / str(count)
                path = Path(tmp) / f'{count}.json'
                path.write_text(json.dumps(config), encoding='utf-8')
                import sys
                subprocess.run([sys.executable, str(Path(renderer.__file__)), '--scenes', str(path),
                                '--output', str(out)], check=True, capture_output=True, timeout=120)
                report = json.loads((out / 'report.json').read_text())
                self.assertEqual(report['scene_count'], count)
                self.assertEqual(report['frames'], 183 if count == 5 else 45)
                renderer.validate_probe(json.loads((out / 'ffprobe.json').read_text()), config)

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
            for second in (0.8, 3.7, 7.1, 10.5, 13):
                raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(second),
                    '-i', str(out / 'creative-demo.mp4'), '-frames:v', '1', '-vf', 'scale=32:32',
                    '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'])
                self.assertEqual(len(raw), 3072)
                self.assertGreater(max(raw) - min(raw), 80)


if __name__ == '__main__':
    unittest.main()
