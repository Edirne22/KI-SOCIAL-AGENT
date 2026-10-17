"""Bounded, offline OpenMontage V2 renderer. Synthetic media only in Block 1.

No providers, arbitrary filter expressions, user media or publishing. Each run
owns a fresh directory: an interrupted run can never look like a valid retry.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time

FPS = 30
WIDTH, HEIGHT = 720, 1280
SCENE_SECONDS = 4
OVERLAP = 0.6
TRANSITIONS = ('fade', 'wipeleft', 'circleopen')
TITLES = ('OPEN MONTAGE', 'IN BEWEGUNG', 'NEUE PERSPEKTIVE', 'DEINE GESCHICHTE')
DURATION = 4 * SCENE_SECONDS - 3 * OVERLAP
FRAMES = round(DURATION * FPS)
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')


def run(args, timeout=240):
    # Render children do not inherit GitHub, R2, Telegram or provider credentials.
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'SYSTEMROOT') if k in os.environ}
    result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # Only fixed local sources/filters are accepted; no remote response body.
        raise RuntimeError(f'{args[0]} failed: {result.stderr[-2000:]}')
    return result.stdout


def synthetic_image(path, scene):
    """Deterministic geometric poster; stdlib PPM, no downloaded assets."""
    colors = ((20, 200, 215), (255, 100, 60), (155, 90, 255), (240, 190, 45))
    accent = colors[scene]
    w, h = 540, 960
    pixels = bytearray()
    for y in range(h):
        for x in range(w):
            radius = math.hypot(x - (170 + scene * 55), y - 420)
            ring = int(radius) % 105 < 5
            grid = (x + y // 2 + scene * 30) % 95 < 2
            glow = max(0, 1 - radius / 650)
            strength = 0.85 if ring else 0.28 if grid else 0.05 + glow * 0.12
            pixels.extend(min(255, int(c * strength + 8)) for c in accent)
    path.write_bytes(f'P6\n{w} {h}\n255\n'.encode() + pixels)


def filter_graph():
    filters = []
    for i, title in enumerate(TITLES):
        zoom = '1+0.0016*on' if i % 2 == 0 else '1.2-0.0016*on'
        x = '(iw-iw/zoom)*on/120' if i % 2 == 0 else '(iw-iw/zoom)*(1-on/120)'
        filters.append(
            f'[{i}:v]scale=1440:2560,zoompan=z=\'{zoom}\':x=\'{x}\':'
            f"y='(ih-ih/zoom)/2':d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
            f'trim=end_frame=120,settb=AVTB,setpts=PTS-STARTPTS,setsar=1,format=yuv420p,'
            f'drawbox=x=48:y=760:w=624:h=5:color=0xffcc55:t=fill,'
            f"drawtext=fontfile={FONT}:text='{title}':fontsize=34:fontcolor=white:"
            "x='(w-text_w)/2+80*max(0,1-t/0.7)':y=680:alpha='min(1,t/0.5)',"
            f"drawtext=fontfile={FONT}:text='0{i+1} / 04':fontsize=24:fontcolor=0xffcc55:x=50:y=810,"
            f"drawtext=fontfile={FONT}:text='SYNTHETISCHER TEST':fontsize=18:fontcolor=white@0.6:x=50:y=1150[s{i}]"
        )
    previous = 's0'
    for i, transition in enumerate(TRANSITIONS, 1):
        label = f'x{i}'
        filters.append(f'[{previous}][s{i}]xfade=transition={transition}:duration={OVERLAP}:'
                       f'offset={i * (SCENE_SECONDS - OVERLAP):.3f}[{label}]')
        previous = label
    filters.append(f'[{previous}]trim=end_frame={FRAMES},setpts=PTS-STARTPTS,'
                   f'fade=t=out:st={DURATION-0.5}:d=0.5[v]')
    filters.append(f'[4:a]atrim=duration={DURATION},afade=t=in:d=0.1,'
                   f'afade=t=out:st={DURATION-0.6}:d=0.6[a]')
    return ';\n'.join(filters)


def validate_probe(data):
    try:
        video = [s for s in data['streams'] if s['codec_type'] == 'video']
        audio = [s for s in data['streams'] if s['codec_type'] == 'audio']
        v = video[0]
        duration = float(data['format']['duration'])
        valid = (len(video) == len(audio) == 1 and len(data['streams']) == 2
                 and v['codec_name'] == 'h264' and v['pix_fmt'] == 'yuv420p'
                 and (v['width'], v['height']) == (WIDTH, HEIGHT)
                 and v['avg_frame_rate'] == '30/1' and int(v['nb_read_frames']) == FRAMES
                 and abs(duration - DURATION) < 0.08 and audio[0]['codec_name'] == 'aac'
                 and 0 < int(data['format']['size']) < 30 * 1024 * 1024)
    except (KeyError, ValueError, TypeError, IndexError):
        valid = False
    if not valid:
        raise ValueError('CREATIVE_MP4_CONTRACT_FAILED')
    return data


def verify(movie):
    data = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams',
                           '-show_format', '-of', 'json', str(movie)], timeout=90))
    validate_probe(data)
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(movie), '-f', 'null', '-'], timeout=90)
    return data


def render(output):
    output = Path(output)
    # Refuse overwrite, including stale output directories from interrupted runs.
    output.mkdir(parents=True, exist_ok=False)
    if not FONT.is_file():
        raise RuntimeError('DejaVu Sans Bold font missing')
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='om-creative-') as temp:
        work = Path(temp)
        args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                '-filter_complex_threads', '1']
        for i in range(4):
            source = work / f'scene-{i}.ppm'
            synthetic_image(source, i)
            args += ['-loop', '1', '-framerate', str(FPS), '-t', str(SCENE_SECONDS), '-i', str(source)]
        # Original, deterministic 100-BPM pulse and chord bed; no copyrighted audio.
        sound = ('0.12*sin(2*PI*65*t)*exp(-12*mod(t,0.6))+'
                 '0.035*(sin(2*PI*220*t)+sin(2*PI*277.1826*t)+sin(2*PI*329.6276*t))')
        args += ['-f', 'lavfi', '-i', f"aevalsrc='{sound}':s=48000:d={DURATION}"]
        graph = work / 'filters.txt'
        graph.write_text(filter_graph())
        partial = output / 'rendering.mp4'
        args += ['-filter_complex_script', str(graph), '-map', '[v]', '-map', '[a]',
                 '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '23',
                 '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-ac', '2',
                 '-t', str(DURATION), '-movflags', '+faststart', str(partial)]
        try:
            run(args)
            probe = verify(partial)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        movie = output / 'creative-demo.mp4'
        partial.rename(movie)
    elapsed = round(time.monotonic() - started, 3)
    report = {'status': 'verified', 'synthetic_only': True, 'publish': False,
              'render_and_validation_seconds': elapsed, 'duration': DURATION,
              'width': WIDTH, 'height': HEIGHT, 'fps': FPS, 'frames': FRAMES,
              'transitions': list(TRANSITIONS), 'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(),
              'bytes': movie.stat().st_size,
              'ffmpeg': run(['ffmpeg', '-version']).splitlines()[0]}
    # Remove machine-specific temporary filenames from the public ffprobe evidence.
    probe['format']['filename'] = movie.name
    (output / 'ffprobe.json').write_text(json.dumps(probe, indent=2) + '\n')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory (must not exist)')
    args = parser.parse_args()
    print(json.dumps(render(args.output), indent=2))
