"""B71 local file integration: self-created CC0 fixtures, no downloads."""
from pathlib import Path
import subprocess
from unittest.mock import patch

import unittest
import tempfile
from integrations.openmontage import creative_renderer as r
from openmontage_production import produce_video


def asset(name):
    return {'scene_number': 1, 'local_path': name, 'rights_verified': True, 'media_license': 'cc0'}


def make_media(path):
    args = ['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=red:s=96x160:r=24:d=0.5']
    args += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p'] if path.suffix == '.mp4' else ['-frames:v', '1', '-threads', '1']
    subprocess.run([*args, str(path)], check=True, capture_output=True, timeout=20)


def check_licensed_local_pixels_reach_production(tmp_path, extension):
    source = tmp_path / ('input' + extension)
    make_media(source)
    scenes = [{'scene_number': 1, 'title': 'Local fixture', 'duration': 1.5}]
    with patch('openmontage_production.fc.verify_research_payload', return_value={'verified_item_count': 1}), \
         patch.object(r, 'synthetic_image', side_effect=AssertionError('No demo fallback allowed')):
        report = produce_video({}, {'scenes': scenes},
                               {'all_rights_verified': True, 'manifest': [asset(source.name)]},
                               tmp_path / 'out', media_root=tmp_path)
    assert report['source_media_included'] is True
    assert report['media_mode'] == 'licensed_local'
    assert report['render_report']['synthetic_only'] is False
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', '0.5', '-i', report['video_file'],
                                   '-frames:v', '1', '-vf', 'crop=32:32:0:0', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'])
    assert len(raw) == 32 * 32 * 3
    assert sum(raw[0::3]) / 1024 > 200
    assert sum(raw[1::3]) / 1024 < 30


def check_invalid_local_files_fail_before_output(tmp_path, name):
    (tmp_path / 'bad.png').write_bytes(b'broken')
    make_media(tmp_path / 'valid.png')
    (tmp_path / 'wrong.mp4').write_bytes((tmp_path / 'valid.png').read_bytes())
    (tmp_path / 'link.jpg').symlink_to(tmp_path / 'valid.png')
    with unittest.TestCase().assertRaisesRegex(ValueError, 'LOCAL_MEDIA_INVALID'):
        r.render(tmp_path / 'out', [{'title': 'Test', 'duration': 1.5}], media=[asset(name)], media_root=tmp_path)
    assert not (tmp_path / 'out').exists()


def check_size_and_license_guards(tmp_path):
    make_media(tmp_path / 'valid.png')
    for item, limit in [(dict(asset('valid.png'), rights_verified=False), r.MAX_MEDIA_BYTES),
                        (dict(asset('valid.png'), media_license='unknown'), r.MAX_MEDIA_BYTES),
                        (asset('valid.png'), 1)]:
        with patch.object(r, 'MAX_MEDIA_BYTES', limit), unittest.TestCase().assertRaisesRegex(ValueError, 'LOCAL_MEDIA_INVALID'):
            r.render(tmp_path / 'out', [{'title': 'Test', 'duration': 1.5}], media=[item], media_root=tmp_path)
        assert not (tmp_path / 'out').exists()


def check_demo_remains_synthetic(tmp_path):
    report = r.render(tmp_path / 'demo', [{'title': 'Demo', 'duration': 1.5}])
    assert report['synthetic_only'] is True
    assert report['source_media_included'] is False


def check_local_handoff_missing_root_never_falls_back(tmp_path):
    with patch('openmontage_production.fc.verify_research_payload', return_value={'verified_item_count': 1}):
        with unittest.TestCase().assertRaisesRegex(ValueError, 'media_root required'):
            produce_video({}, {'scenes': [{'scene_number': 1, 'title': 'Test', 'duration': 1.5}]},
                          {'all_rights_verified': True, 'manifest': [asset('valid.jpg')]}, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


class LocalMediaTests(unittest.TestCase):
    def test_licensed_images_and_video(self):
        for extension in ('.jpg', '.png', '.mp4'):
            with self.subTest(extension=extension), tempfile.TemporaryDirectory() as tmp:
                check_licensed_local_pixels_reach_production(Path(tmp), extension)

    def test_invalid_files(self):
        for name in ('missing.jpg', '../escape.jpg', '/etc/passwd', 'https://host/a.jpg', 'bad.png', 'wrong.mp4', 'link.jpg'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                check_invalid_local_files_fail_before_output(Path(tmp), name)

    def test_size_and_rights(self):
        with tempfile.TemporaryDirectory() as tmp:
            check_size_and_license_guards(Path(tmp))

    def test_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            check_demo_remains_synthetic(Path(tmp))

    def test_missing_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            check_local_handoff_missing_root_never_falls_back(Path(tmp))
