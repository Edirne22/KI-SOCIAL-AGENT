"""Explicit, preview-only Hermes entry into the existing OpenMontage chain.

No publisher, Telegram token, R2 or media download. Isolated run directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import textwrap
from datetime import datetime, timezone

from integrations.openmontage.hermes_live_workers import run as research
from integrations.openmontage import creative_renderer as renderer
from openmontage_storyboard import build_storyboard
from openmontage_production import produce_video
from scripts.openmontage_media_contract import validate_local_scene_media
from scripts.openmontage_quality_gate import validate_video

TOPIC = 'Toprak Razgatlioglu – aktuelle überprüfbare Motorrad-News auf Deutsch'


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def test_media(board, root):
    """Animate the existing owned procedural demo graphics into actual local clips.

    These are explicitly labelled illustrative test graphics, not racing footage.
    No research website image is treated as licensed media.
    """
    root.mkdir(parents=True, exist_ok=True)
    items = []
    colors = ('0x11d8e8', '0xff754a', '0xb38cff', '0xffcf40', '0x4fe7a8', '0xf783ce')
    for i, scene in enumerate(board['scenes']):
        color = colors[i % len(colors)]
        renderer.synthetic_image(root / f'poster-{i}.ppm', i)
        body = textwrap.fill(scene['speaker_text'].split(': ', 1)[-1], width=33)
        (root / f'body-{i}.txt').write_text(body, encoding='utf-8')
        # Animated road/grid texture and sweeping accent: every frame moves.
        graph = (
            f"[0:v]scale=800:1422,scroll=horizontal={0.025*(i+1)}:vertical=-0.04,"
            f"crop=720:1280,eq=brightness=-0.04,drawgrid=w=120:h=180:t=2:c={color}@0.25[bg];"
            f"[bg][1:v]overlay=x='mod(t*240+{i*90},1020)-300':y={180+i*35}:shortest=1,"
            f"drawbox=x=30:y=850:w=660:h=240:c=black@0.75:t=fill,"
            f"drawtext=fontfile={renderer.FONT}:textfile=body-{i}.txt:expansion=none:"
            f"fontsize=29:line_spacing=12:fontcolor=white:x=55:y=875,"
            f"drawtext=fontfile={renderer.FONT}:text='TESTGRAFIK - KEINE RENNAUFNAHME':"
            f"fontsize=24:fontcolor=white:x=45:y=75[v]"
        )
        (root / f'graph-{i}.txt').write_text(graph, encoding='utf-8')
        renderer.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-filter_complex_threads', '1',
                      '-loop', '1', '-framerate', '30', '-i', f'poster-{i}.ppm',
                      '-f', 'lavfi', '-i', f'color=c={color}:s=300x12:r=30',
                      '-filter_complex_script', f'graph-{i}.txt', '-map', '[v]',
                      '-t', str(scene['duration']), '-c:v', 'libx264', '-threads', '2',
                      '-preset', 'veryfast', '-pix_fmt', 'yuv420p', f'scene-{i}.mp4'], cwd=root)
        items.append({'scene_number': i+1, 'local_path': f'scene-{i}.mp4',
                      'media_license': 'owned_content', 'rights_verified': True,
                      'media_source': 'existing creative_renderer.synthetic_image, animated locally',
                      'synthetic_test_media': True})
    return {'manifest': items, 'all_rights_verified': True}


def execute(output, topic):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)  # duplicate/restart cannot reuse stale success
    state = research(topic)
    save(output / 'research-handoff.json', state)
    if state['status'] != 'RESEARCH_READY':
        blocked = state.get('blocked_outputs', {}).get('fact_checker', {})
        rejections = blocked.get('rejections', []) if isinstance(blocked, dict) else []
        diagnostic = {'failure': state['history'][-1],
                      'candidate_claims': len(state.get('nemotron_analyst', {}).get('claims', [])),
                      'rejections': [{'index': r.get('index'), 'reason': str(r.get('reason', ''))[:180]}
                                     for r in rejections[:12] if isinstance(r, dict)]}
        raise ValueError('RESEARCH_BLOCKED: ' + json.dumps(diagnostic, ensure_ascii=False))
    checked = state['handoff']['report']
    if not (1 <= len(checked['stories']) <= 6):
        raise ValueError(f"VERIFIED_CLAIMS_COUNT_OUT_OF_BOUNDS: {len(checked['stories'])}")
    board = build_storyboard(checked, target_duration=36, aspect_ratio='9:16', language='de', film_type='news')
    save(output / 'storyboard.json', board)
    trace = list(state['history'])
    trace.append({'role': 'creative_director', 'verdict': 'PASS', 'scenes': len(board['scenes'])})
    media = test_media(board, output / 'test-media')
    validate_local_scene_media(board, media)
    save(output / 'media-manifest.json', media)
    trace.append({'role': '07_video_optimization', 'verdict': 'PASS', 'mode': 'labelled_synthetic_test_clips'})
    result = produce_video(checked, board, media, output / 'film', media_root=output / 'test-media')
    trace.append({'role': 'openmontage_production', 'verdict': 'PASS', 'sha256': result['sha256']})
    validate_video(Path(result['video_file']))
    trace.append({'role': 'mp4_quality_gate', 'verdict': 'PASS'})
    save(output / 'production-receipt.json', {
        'status': 'PREVIEW_READY', 'topic': topic, 'created_at': datetime.now(timezone.utc).isoformat(),
        'commit': os.environ.get('GITHUB_SHA', 'local'), 'run_id': os.environ.get('GITHUB_RUN_ID', 'local'),
        'publication_authorized': False, 'synthetic_test_media': True,
        'research_sha256': hashlib.sha256((output / 'research-handoff.json').read_bytes()).hexdigest(),
        'trace': trace, 'result': result,
        'sources': [{k: d[k] for k in ('url', 'published_at', 'retrieved_at', 'backend', 'sha256')}
                    for d in state['source_reader']['documents']]})
    print('HERMES_PRODUCTION_PREVIEW_READY')


def verify(output):
    receipt = json.loads((output / 'production-receipt.json').read_text())
    if (receipt['status'] != 'PREVIEW_READY' or receipt['publication_authorized'] is not False
            or receipt['commit'] != os.environ.get('GITHUB_SHA', 'local')):
        raise ValueError('Invalid or stale production receipt')
    digest = hashlib.sha256((output / 'research-handoff.json').read_bytes()).hexdigest()
    if digest != receipt['research_sha256']:
        raise ValueError('Research handoff changed after production')
    movie = output / 'film' / 'creative-demo.mp4'
    if hashlib.sha256(movie.read_bytes()).hexdigest() != receipt['result']['sha256']:
        raise ValueError('MP4 hash mismatch')
    board = json.loads((output / 'storyboard.json').read_text())
    renderer.verify(movie, board['scenes'])
    num_scenes = len(board['scenes'])
    duration_sec = receipt['result']['duration_seconds']
    if not (1 <= num_scenes <= 8) or duration_sec < 5 or duration_sec > 300:
        raise ValueError(f'Scene count ({num_scenes}) or duration ({duration_sec}) mismatch')
    sample_count = min(7, max(3, num_scenes + 1))
    sample_times = [round(0.5 + i * (duration_sec - 1.0) / (sample_count - 1), 2) for i in range(sample_count)]
    frame_hashes = []
    for sec in sample_times:
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(sec), '-i', str(movie),
                                       '-frames:v', '1', '-vf', 'scale=72:128', '-f', 'rawvideo', '-'])
        if not raw:
            raise ValueError('Empty decoded frame')
        frame_hashes.append(hashlib.sha256(raw).hexdigest())
    if len(set(frame_hashes)) < max(1, sample_count - 1):
        raise ValueError('Video lacks changing frames')
    save(output / 'acceptance.json', {'status': 'PASS', 'decoded_frame_hashes': frame_hashes,
                                     'publication_authorized': False})
    renderer.run(['ffmpeg', '-v', 'error', '-i', str(movie), '-vf',
                  'fps=1/6,scale=180:320,tile=3x2', '-frames:v', '1', '-threads', '1',
                  str(output / 'contact-sheet.jpg')])
    print(json.dumps({'status': 'PASS', 'seconds': duration_sec,
                      'scenes': num_scenes, 'sources': receipt['sources'], 'sha256': receipt['result']['sha256']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--topic', default=TOPIC, help='Requested news topic; no publication')
    args = parser.parse_args()
    verify(args.output) if args.verify else execute(args.output, args.topic)
