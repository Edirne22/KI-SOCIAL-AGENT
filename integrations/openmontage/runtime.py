"""Project-local Quick Start and diagnostics. Never serialize credentials."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent
UPSTREAM = BASE / 'upstream'
PIN = json.loads((BASE / 'upstream.json').read_text())
KEYS = ('FAL_KEY', 'ATLASCLOUD_API_KEY', 'KLING_API_KEY', 'PEXELS_API_KEY',
        'PIXABAY_API_KEY', 'UNSPLASH_ACCESS_KEY', 'SUNO_API_KEY', 'ELEVENLABS_API_KEY',
        'OPENAI_API_KEY', 'GOOGLE_API_KEY', 'XAI_API_KEY', 'ARK_API_KEY',
        'HEYGEN_API_KEY', 'RUNWAY_API_KEY')


def key_inventory(environ):
    return {key: bool(environ.get(key, '').strip()) for key in KEYS}


def local_env():
    # Installation and demo receive no inherited credentials, even if called locally.
    allowed = ('PATH', 'HOME', 'LANG', 'LC_ALL', 'SYSTEMROOT')
    env = {k: os.environ[k] for k in allowed if k in os.environ}
    cache = BASE / '.runtime'
    for name in ('pip', 'npm', 'xdg', 'tmp'):
        (cache / name).mkdir(parents=True, exist_ok=True)
    env.update(PIP_CACHE_DIR=str(cache / 'pip'), npm_config_cache=str(cache / 'npm'),
               XDG_CACHE_HOME=str(cache / 'xdg'), TMPDIR=str(cache / 'tmp'),
               PIP_DISABLE_PIP_VERSION_CHECK='1', npm_config_update_notifier='false')
    return env


def setup():
    env = local_env()
    for command in ('python3', 'ffmpeg', 'ffprobe', 'node', 'npm', 'make', 'git'):
        if not shutil.which(command):
            raise RuntimeError(f'{command} fehlt; nichts global installiert.')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=UPSTREAM, text=True).strip()
    if actual != PIN['revision']:
        raise RuntimeError('OpenMontage-Version weicht vom geprüften Pin ab.')
    subprocess.run(['python3', '-m', 'venv', '.venv'], cwd=UPSTREAM, env=env, check=True)
    subprocess.run(['make', 'setup'], cwd=UPSTREAM, env=env, check=True, timeout=900)
    python = str(UPSTREAM / '.venv/bin/python')
    # Upstream Makefile tolerates Piper failure; our contract does not.
    subprocess.run([python, '-c', 'import piper'], cwd=UPSTREAM, env=env, check=True)
    subprocess.run([python, '-m', 'pip', 'check'], cwd=UPSTREAM, env=env, check=True)


def diagnose():
    python = str(UPSTREAM / '.venv/bin/python')
    version = subprocess.check_output([python, '-c',
        'from importlib.metadata import version; print(version("piper-tts"))'], text=True).strip()
    report = {'upstream_commit': PIN['revision'], 'piper_package': version,
              'keys_present_not_validated': key_inventory(os.environ),
              'voice_model': 'NOT_INSTALLED', 'provider_calls': False,
              'render_test': 'NOT_RUN'}
    report['remotion'] = json.loads((UPSTREAM / 'remotion-composer/node_modules/remotion/package.json').read_text())['version']
    for cmd in (['python3', '--version'], ['node', '--version'], ['ffmpeg', '-version']):
        report[cmd[0]] = subprocess.check_output(cmd, text=True).splitlines()[0]
    output = BASE / '.runtime/diagnose.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def demo():
    env = local_env()
    python = str(UPSTREAM / '.venv/bin/python')
    subprocess.run([python, 'render_demo.py', 'code-to-screen'], cwd=UPSTREAM,
                   env=env, check=True, timeout=900)
    movie = UPSTREAM / 'projects/demos/renders/code-to-screen.mp4'
    data = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
        '-show_streams', '-of', 'json', str(movie)], text=True))
    if float(data['format']['duration']) <= 0 or not any(s['codec_type'] == 'video' for s in data['streams']):
        raise RuntimeError('Demo hat keinen gültigen Videostream.')
    print('Demo mit ffprobe geprüft; keine Aussage über Provider oder TTS.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['setup', 'diagnose', 'demo'])
    args = parser.parse_args()
    {'setup': setup, 'diagnose': diagnose, 'demo': demo}[args.mode]()
