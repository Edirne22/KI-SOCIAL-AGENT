"""Creative offline storyboard smoke test: three animated scenes, typography, transitions.

All visuals are synthetic. This does NOT claim licensed motorsport footage.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import tempfile
from scripts.openmontage_producer import probe

SCENES = [
    ("RACE WEEKEND", "MOTORSPORT // PREVIEW", "0x19243a"),
    ("THE GRID", "LIGHTS OUT // ACTION", "0x2c1736"),
    ("FULL THROTTLE", "NEXT: REAL MEDIA", "0x142f31"),
]


def make_preview(output: Path) -> dict:
    output = output.resolve()
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output must be .mp4")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="om-creative-") as tmp:
        segments = []
        for i, (title, subtitle, background) in enumerate(SCENES):
            part = Path(tmp) / f"scene-{i}.mp4"
            # Animated diagonal grid + prominent typography and fades.
            filters = (
                "drawgrid=w=100:h=100:t=3:c=white@0.13,"
                "drawbox=x=0:y=1150:w=iw:h=440:color=black@0.55:t=fill,"
                f"drawtext=text='{title}':fontcolor=white:fontsize=92:"
                "x=(w-text_w)/2:y=1230,"
                f"drawtext=text='{subtitle}':fontcolor=yellow:fontsize=39:"
                "x=(w-text_w)/2:y=1380,"
                "fade=t=in:st=0:d=0.25,fade=t=out:st=1.55:d=0.45,"
                "format=yuv420p"
            )
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-f", "lavfi", "-i", f"testsrc2=size=1080x1920:rate=30:duration=2",
                "-vf", filters, "-t", "2", "-an", "-c:v", "libx264",
                "-preset", "ultrafast", "-crf", "28", str(part)
            ], check=True, timeout=150)
            segments.append(part)
        concat = Path(tmp) / "concat.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in segments))
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c", "copy", "-movflags", "+faststart", str(output)
        ], check=True, timeout=90)
    result = probe(output)
    streams = [s for s in result.get("streams", []) if s.get("codec_type") == "video"]
    duration = float(result.get("format", {}).get("duration", 0))
    if not streams or streams[0].get("width") != 1080 or streams[0].get("height") != 1920 or duration < 5.5:
        raise RuntimeError("Creative preview quality check failed")
    return {"output": str(output), "scenes": len(SCENES), "seconds": duration,
            "media": "synthetic-only", "production_ready": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(make_preview(args.output))
