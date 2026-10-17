"""Offline, deterministic portrait video producer for explicitly supplied local media.

No downloading, provider calls, publishing, or credential access. Inputs must be
reviewed/licensed by the operator before they are supplied.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)


def render(manifest: Path, output: Path) -> dict:
    manifest = manifest.resolve(strict=True)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    clips = payload.get("clips")
    if not isinstance(clips, list) or not 1 <= len(clips) <= 20:
        raise ValueError("Manifest benötigt 1 bis 20 Clips.")
    if output.suffix.lower() != ".mp4":
        raise ValueError("Ausgabe muss MP4 sein.")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="openmontage-") as tmp:
        parts = []
        for index, item in enumerate(clips):
            if not isinstance(item, dict) or set(item) != {"path", "seconds"}:
                raise ValueError("Clip benötigt genau path und seconds.")
            raw = item["path"]
            duration = item["seconds"]
            if not isinstance(raw, str) or not raw or not isinstance(duration, (int, float)) or isinstance(duration, bool) or not 0.5 <= duration <= 30:
                raise ValueError("Ungültige Clip-Dauer oder Pfadangabe.")
            source = (manifest.parent / raw).resolve(strict=True)
            if not source.is_file() or source.suffix.lower() not in {".mp4", ".mov", ".mkv", ".jpg", ".jpeg", ".png", ".webp"}:
                raise ValueError("Nicht unterstützte lokale Mediendatei.")
            is_image = source.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            if not is_image and not any(s.get("codec_type") == "video" for s in probe(source).get("streams", [])):
                raise ValueError("Quelldatei enthält keinen Videostream.")
            part = Path(tmp) / f"clip-{index:02d}.mp4"
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
            if is_image:
                command += ["-loop", "1", "-framerate", "30"]
            command += ["-i", str(source), "-t", str(duration), "-vf",
                        "scale=1080:1920:force_original_aspect_ratio=decrease,"
                        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
                        "fps=30,format=yuv420p",
                        "-an", "-c:v", "libx264", "-preset", "veryfast",
                        "-movflags", "+faststart", str(part)]
            subprocess.run(command, check=True, timeout=180)
            parts.append(part)
        concat = Path(tmp) / "concat.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                        "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                        "-c", "copy", "-movflags", "+faststart", str(output)],
                       check=True, timeout=180)
    report = probe(output)
    video = [s for s in report.get("streams", []) if s.get("codec_type") == "video"]
    if not video or video[0].get("width") != 1080 or video[0].get("height") != 1920 or float(report.get("format", {}).get("duration", 0)) <= 0:
        raise RuntimeError("Video-QC fehlgeschlagen.")
    return {"output": str(output), "duration": float(report["format"]["duration"]),
            "width": 1080, "height": 1920, "clips": len(parts)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(render(args.manifest, args.output), ensure_ascii=False))
