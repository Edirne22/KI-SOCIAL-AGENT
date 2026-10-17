"""Bounded, offline OpenMontage V2 renderer. Synthetic media with configurable scenes.

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


def normalize_scenes(scenes=None):
    """Validate before IO. Durations must lie on the 30-fps frame grid.

    Transition belongs to the outgoing scene; the last has no transition.
    Omitted options preserve the original alternating movement and effects.
    """
    if scenes is None:
        scenes = [{'title': title, 'duration': SCENE_SECONDS} for title in TITLES]
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 8:
        raise ValueError('Expected 1 to 8 scenes')
    result = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict) or set(scene) - {'title', 'duration', 'zoom', 'motion', 'transition'}:
            raise ValueError('Unknown scene fields')
        title, seconds = scene.get('title'), scene.get('duration')
        if not isinstance(title, str) or not title.strip() or len(title) > 40 or not title.isprintable():
            raise ValueError('Title must contain 1 to 40 printable characters')
        if (type(seconds) not in (int, float) or not 1.5 <= seconds <= 15
                or not math.isfinite(seconds) or abs(seconds * FPS - round(seconds * FPS)) > 1e-7):
            raise ValueError('Duration must be 1.5 to 15 seconds on the 30-fps frame grid')
        zoom = scene.get('zoom', 'in' if i % 2 == 0 else 'out')
        motion = scene.get('motion', 'right' if i % 2 == 0 else 'left')
        transition = scene.get('transition', TRANSITIONS[i % 3] if i < len(scenes) - 1 else None)
        if zoom not in ('in', 'out', 'none') or motion not in ('left', 'right', 'none'):
            raise ValueError('Unsupported zoom or motion')
        if (i < len(scenes) - 1 and transition not in TRANSITIONS) or (i == len(scenes) - 1 and transition is not None):
            raise ValueError('Unsupported transition (last scene must have null transition)')
        result.append({'title': title, 'duration': round(seconds * FPS) / FPS,
                       'zoom': zoom, 'motion': motion, 'transition': transition})
    if timeline(result)[0] > 60:
        raise ValueError('Movie exceeds 60 seconds')
    return result


def timeline(scenes):
    frames = sum(round(s['duration'] * FPS) for s in scenes) - round(OVERLAP * FPS) * (len(scenes) - 1)
    return frames / FPS, frames


def load_scenes(path):
    with Path(path).open('rb') as source:
        payload = source.read(32769)
    if len(payload) > 32768:
        raise ValueError('Scene JSON exceeds 32 KiB')
    scenes = json.loads(payload.decode('utf-8'))
    if not isinstance(scenes, list):
        raise ValueError('Scene JSON must be a list')
    return normalize_scenes(scenes)


def run(args, timeout=240, cwd=None):
    # Render children do not inherit GitHub, R2, Telegram or provider credentials.
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'SYSTEMROOT') if k in os.environ}
    result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    if result.returncode:
        # Only fixed local sources/filters are accepted; no remote response body.
        raise RuntimeError(f'{args[0]} failed: {result.stderr[-2000:]}')
    return result.stdout


def synthetic_image(path, scene):
    """Deterministic geometric poster; stdlib PPM, no downloaded assets."""
    colors = ((20, 200, 215), (255, 100, 60), (155, 90, 255), (240, 190, 45))
    scene %= len(colors)
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


def filter_graph(scenes=None, music=False):
    scenes = normalize_scenes(scenes)
    duration, frames = timeline(scenes)
    filters = []
    for i, scene in enumerate(scenes):
        count = round(scene['duration'] * FPS)
        zoom = {'in': f'1+0.192*on/{count}', 'out': f'1.2-0.192*on/{count}',
                'none': '1.2' if scene['motion'] != 'none' else '1'}[scene['zoom']]
        x = {'right': f'(iw-iw/zoom)*on/{count}',
             'left': f'(iw-iw/zoom)*(1-on/{count})', 'none': '(iw-iw/zoom)/2'}[scene['motion']]
        size = min(34, int(600 / (len(scene['title']) * 0.9)))
        filters.append(
            f"[{i}:v]scale=1440:2560,zoompan=z='{zoom}':x='{x}':"
            f"y='(ih-ih/zoom)/2':d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
            f'trim=end_frame={count},settb=AVTB,setpts=PTS-STARTPTS,setsar=1,format=yuv420p,'
            f'drawbox=x=48:y=760:w=624:h=5:color=0xffcc55:t=fill,'
            f'drawtext=fontfile={FONT}:textfile=title-{i}.txt:expansion=none:fontsize={size}:fontcolor=white:'
            "x='(w-text_w)/2+80*max(0,1-t/0.7)':y=680:alpha='min(1,t/0.5)',"
            f"drawtext=fontfile={FONT}:text='{i+1:02} / {len(scenes):02}':fontsize=24:fontcolor=0xffcc55:x=50:y=810,"
            f"drawtext=fontfile={FONT}:text='SYNTHETISCHER TEST':fontsize=18:fontcolor=white@0.6:x=50:y=1150[s{i}]"
        )
    previous = 's0'
    elapsed_frames = 0
    for i in range(1, len(scenes)):
        elapsed_frames += round(scenes[i-1]['duration'] * FPS) - round(OVERLAP * FPS)
        label = f'x{i}'
        filters.append(f"[{previous}][s{i}]xfade=transition={scenes[i-1]['transition']}:duration={OVERLAP}:"
                       f'offset={elapsed_frames / FPS:.3f}[{label}]')
        previous = label
    filters.append(f'[{previous}]trim=end_frame={frames},setpts=PTS-STARTPTS,'
                   f'fade=t=out:st={duration-0.5}:d=0.5[v]')
    filters.append(f'[{len(scenes)}:a]atrim=duration={duration},asetpts=PTS-STARTPTS,'
                   f'volume={0.7 if music else 1},afade=t=in:d=0.15,'
                   f'afade=t=out:st={duration-0.6}:d=0.6[a]')
    return ';\n'.join(filters)


def validate_probe(data, scenes=None):
    expected_duration, expected_frames = timeline(normalize_scenes(scenes))
    try:
        video = [s for s in data['streams'] if s['codec_type'] == 'video']
        audio = [s for s in data['streams'] if s['codec_type'] == 'audio']
        v = video[0]
        duration = float(data['format']['duration'])
        valid = (len(video) == len(audio) == 1 and len(data['streams']) == 2
                 and v['codec_name'] == 'h264' and v['pix_fmt'] == 'yuv420p'
                 and (v['width'], v['height']) == (WIDTH, HEIGHT)
                 and v['avg_frame_rate'] == '30/1' and int(v['nb_read_frames']) == expected_frames
                 and abs(duration - expected_duration) < 0.08 and audio[0]['codec_name'] == 'aac'
                 and 0 < int(data['format']['size']) < 30 * 1024 * 1024)
    except (KeyError, ValueError, TypeError, IndexError):
        valid = False
    if not valid:
        raise ValueError('CREATIVE_MP4_CONTRACT_FAILED')
    return data


def verify(movie, scenes=None):
    data = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams',
                           '-show_format', '-of', 'json', str(movie)], timeout=90))
    validate_probe(data, scenes)
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(movie), '-f', 'null', '-'], timeout=90)
    return data


def render(output, scenes=None, music=None):
    scenes = normalize_scenes(scenes)
    duration, frames = timeline(scenes)
    if music is not None:
        music = Path(music).resolve(strict=True)
        if not music.is_file() or music.suffix.lower() != '.wav' or music.stat().st_size > 30 * 1024 * 1024:
            raise ValueError('Music must be a local WAV file up to 30 MiB')
    output = Path(output).absolute()
    # Refuse overwrite, including stale output directories from interrupted runs.
    output.mkdir(parents=True, exist_ok=False)
    if not FONT.is_file():
        raise RuntimeError('DejaVu Sans Bold font missing')
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='om-creative-') as temp:
        work = Path(temp)
        args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                '-filter_complex_threads', '1']
        for i, scene in enumerate(scenes):
            source = work / f'scene-{i}.ppm'
            synthetic_image(source, i)
            (work / f'title-{i}.txt').write_text(scene['title'], encoding='utf-8')
            args += ['-loop', '1', '-framerate', str(FPS), '-t', str(scene['duration']), '-i', str(source)]
        # Original, deterministic 100-BPM pulse and chord bed; no copyrighted audio.
        sound = ('0.12*sin(2*PI*65*t)*exp(-12*mod(t,0.6))+'
                 '0.035*(sin(2*PI*220*t)+sin(2*PI*277.1826*t)+sin(2*PI*329.6276*t))')
        if music is None:
            args += ['-f', 'lavfi', '-i', f"aevalsrc='{sound}':s=48000:d={duration}"]
        else:
            args += ['-stream_loop', '-1', '-i', str(music)]
        graph = work / 'filters.txt'
        graph.write_text(filter_graph(scenes, music=music is not None))
        partial = output / 'rendering.mp4'
        args += ['-filter_complex_script', str(graph), '-map', '[v]', '-map', '[a]',
                 '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '23',
                 '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-ac', '2',
                 '-t', str(duration), '-movflags', '+faststart', str(partial)]
        try:
            run(args, cwd=work)
            probe = verify(partial, scenes)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        movie = output / 'creative-demo.mp4'
        partial.rename(movie)
    elapsed = round(time.monotonic() - started, 3)
    report = {'status': 'verified', 'synthetic_only': True, 'publish': False,
              'render_and_validation_seconds': elapsed, 'duration': duration,
              'music_source': 'local_wav' if music is not None else 'synthetic',
              'width': WIDTH, 'height': HEIGHT, 'fps': FPS, 'frames': frames,
              'transitions': [s['transition'] for s in scenes[:-1]], 'scene_count': len(scenes), 'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(),
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
    parser.add_argument('--scenes', type=Path, help='UTF-8 JSON list of scenes; omitted = original demo')
    parser.add_argument('--music', type=Path, help='Optional authorized local WAV soundtrack (no downloads)')
    args = parser.parse_args()
    print(json.dumps(render(args.output, load_scenes(args.scenes) if args.scenes else None, music=args.music), indent=2))
