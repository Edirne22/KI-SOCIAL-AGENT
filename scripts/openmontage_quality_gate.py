"""Fail-closed MP4 quality gate before owner-only preview upload."""
import json
import subprocess
from pathlib import Path


def validate_video(path: Path, *, runner=subprocess.run) -> dict:
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != ".mp4" or path.stat().st_size == 0:
        raise ValueError("Non-empty MP4 required")
    result = runner(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    data = json.loads(result.stdout)
    duration = float(data.get("format", {}).get("duration", 0))
    videos = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    if not 0 < duration <= 600 or not videos:
        raise ValueError("Invalid video duration or missing video stream")
    if not any(int(s.get("width") or 0) >= 320 and int(s.get("height") or 0) >= 240 for s in videos):
        raise ValueError("Video dimensions below minimum")
    return {"duration_seconds": duration, "video_streams": len(videos)}
