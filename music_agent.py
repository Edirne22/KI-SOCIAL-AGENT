"""Wählt lizenzfreie Musik aus der lokalen Bibliothek und mischt sie in freigegebene Videos.

Nur ausdrücklich freigegebene Reel- und Story-Blöcke mit `Musik: auto` werden
bearbeitet. Bis die Mischung fertig ist, reserviert der Publisher den Beitrag
nicht. Es gibt keine Veröffentlichung durch dieses Skript.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PUBLISHED = Path("content/PUBLISHED.md")
LIBRARY = Path("config/MUSIC_LIBRARY.json")
LOG = Path("memory/MUSIC_LOG.md")

RACE_TERMS = ("motogp", "worldsbk", "rennen", "racer", "toprak", "yamaha", "ducati", "misano", "sprint")
TRAVEL_TERMS = ("reise", "route", "ausfahrt", "tour", "türkei", "turkey", "urlaub", "landschaft")


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if not LOG.exists():
        LOG.write_text("# Musik-Agent – Protokoll\n", encoding="utf-8")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"\n- {stamp}: {message}\n")
    print(message)


def load_library() -> list[dict]:
    try:
        data = json.loads(LIBRARY.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        log(f"Musikbibliothek nicht lesbar: {error}")
        return []
    tracks = data.get("tracks", []) if isinstance(data, dict) else []
    return [track for track in tracks if isinstance(track, dict) and track.get("path")]


def choose_track(block: str, tracks: list[dict]) -> dict | None:
    text = block.lower()
    desired = "racing" if any(term in text for term in RACE_TERMS) else (
        "travel" if any(term in text for term in TRAVEL_TERMS) else "chill"
    )
    for track in tracks:
        if track.get("category") == desired and Path(track["path"]).exists():
            return track
    for track in tracks:
        if Path(track["path"]).exists():
            return track
    return None


def source_has_audio(video: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_type", "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and "audio" in result.stdout


def mix_music(video: Path, track: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        return
    if source_has_audio(video):
        filter_graph = (
            "[1:a]volume=0.18,afade=t=in:st=0:d=1,"
            "afade=t=out:st=25:d=1[music];"
            "[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        command = [
            "ffmpeg", "-y", "-i", str(video), "-stream_loop", "-1", "-i", str(track),
            "-filter_complex", filter_graph, "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output),
        ]
    else:
        filter_graph = "[1:a]volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st=25:d=1[music]"
        command = [
            "ffmpeg", "-y", "-i", str(video), "-stream_loop", "-1", "-i", str(track),
            "-filter_complex", filter_graph, "-map", "0:v:0", "-map", "[music]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output),
        ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:])


def process() -> int:
    if not PUBLISHED.exists():
        log("PUBLISHED.md fehlt – nichts zu bearbeiten.")
        return 0
    tracks = load_library()
    if not tracks:
        log("Keine Musikdatei vorhanden – Musikbibliothek zuerst manuell einrichten.")
        return 0

    content = PUBLISHED.read_text(encoding="utf-8")
    pattern = re.compile(r"(^## (?:Instagram Reel|Reel|Story)(?:\s+\[[^\]]+\])?\s*\n.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    changed = 0

    for match in list(pattern.finditer(content)):
        block = match.group(1)
        if "[GEPOSTET" in block or not re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", block):
            continue
        if not re.search(r"(?mi)^Musik:\s*auto\s*$", block):
            continue
        video_match = re.search(r"(?mi)^Video:\s*(?!auto\s*$)(\S+)", block)
        if not video_match:
            log("Freigegebener Block wartet auf einen echten Video-Pfad.")
            continue

        video = Path(video_match.group(1))
        if not video.exists():
            log(f"Video nicht gefunden: {video}")
            continue
        track = choose_track(block, tracks)
        if not track:
            log("Kein passender lokaler Musiktrack vorhanden.")
            continue

        track_path = Path(track["path"])
        output = video.with_name(f"{video.stem}-musik-{track['id']}.mp4")
        try:
            mix_music(video, track_path, output)
        except (OSError, RuntimeError) as error:
            log(f"Musikmischung fehlgeschlagen für {video}: {error}")
            continue

        updated = re.sub(r"(?mi)^Video:\s*\S+", f"Video: {output.as_posix()}", block, count=1)
        updated = re.sub(r"(?mi)^Musik:\s*auto\s*$", f"Musik: {track['title']}", updated, count=1)
        content = content.replace(block, updated, 1)
        changed += 1
        log(f"Gemischt: {video.name} + {track['title']} → {output.name}")

    if changed:
        PUBLISHED.write_text(content, encoding="utf-8")
    else:
        print("Keine freigegebenen Videos mit Musik: auto gefunden.")
    return changed


if __name__ == "__main__":
    process()
