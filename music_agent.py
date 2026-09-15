"""Wählt dokumentierte Musik aus der lokalen Bibliothek und mischt sie in freigegebene Videos.

Nur ausdrücklich freigegebene Reel- und Story-Blöcke mit `Musik: auto` werden
bearbeitet. Der Publisher wartet technisch auf die fertige Mischung. Dieses
Skript veröffentlicht selbst nichts.

Mit MUSIC_AGENT_TEST_MODE=1 darf ein bereits reservierter Block testweise
verarbeitet werden. Dabei wird PUBLISHED.md nicht verändert; das Ergebnis
landet ausschließlich unter test-output/music-agent/.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PUBLISHED = Path("content/PUBLISHED.md")
LIBRARY = Path("config/MUSIC_LIBRARY.json")
LOG = Path("memory/MUSIC_LOG.md")
TEST_OUTPUT = Path("test-output/music-agent")

RACE_TERMS = ("motogp", "worldsbk", "rennen", "racer", "toprak", "yamaha", "ducati", "misano", "sprint")
TRAVEL_TERMS = ("reise", "route", "ausfahrt", "tour", "türkei", "turkey", "urlaub", "landschaft")
REQUIRED_TRACK_FIELDS = ("id", "title", "category", "path", "license", "source_page")


def test_mode() -> bool:
    return os.environ.get("MUSIC_AGENT_TEST_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


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
    valid: list[dict] = []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        missing = [field for field in REQUIRED_TRACK_FIELDS if not track.get(field)]
        if missing:
            log(f"Track übersprungen – Metadaten fehlen: {', '.join(missing)}")
            continue
        path = Path(str(track["path"]))
        if not path.exists() or not path.is_file() or path.stat().st_size < 1024:
            log(f"Track übersprungen – Musikdatei fehlt/ist ungültig: {path}")
            continue
        valid.append(track)
    return valid


def desired_category(block: str) -> str:
    text = block.lower()
    if any(term in text for term in RACE_TERMS):
        return "racing"
    if any(term in text for term in TRAVEL_TERMS):
        return "travel"
    return "chill"


def choose_track(block: str, tracks: list[dict]) -> dict | None:
    desired = desired_category(block)
    return next((track for track in tracks if track.get("category") == desired), None)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe fehlgeschlagen: {result.stderr[-300:]}")
    try:
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError("Videolänge konnte nicht bestimmt werden.") from error
    if duration <= 0:
        raise RuntimeError("Ungültige Videolänge.")
    return duration


def source_has_audio(video: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_type", "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True, check=False,
    )
    return result.returncode == 0 and "audio" in result.stdout


def output_is_valid(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1024:
        return False
    video = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_type",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=False,
    )
    audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=False,
    )
    return video.returncode == 0 and "video" in video.stdout and audio.returncode == 0 and "audio" in audio.stdout


def mix_music(video: Path, track: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output_is_valid(output):
        return
    if output.exists():
        output.unlink()

    duration = probe_duration(video)
    fade_in = min(1.0, max(0.15, duration / 8))
    fade_out_duration = min(1.5, max(0.15, duration / 8))
    fade_out_start = max(0.0, duration - fade_out_duration)
    music_filter = (
        f"volume=0.18,afade=t=in:st=0:d={fade_in:.3f},"
        f"afade=t=out:st={fade_out_start:.3f}:d={fade_out_duration:.3f}"
    )

    if source_has_audio(video):
        filter_graph = f"[1:a]{music_filter}[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        command = [
            "ffmpeg", "-y", "-i", str(video), "-stream_loop", "-1", "-i", str(track),
            "-filter_complex", filter_graph, "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output),
        ]
    else:
        filter_graph = f"[1:a]{music_filter}[music]"
        command = [
            "ffmpeg", "-y", "-i", str(video), "-stream_loop", "-1", "-i", str(track),
            "-filter_complex", filter_graph, "-map", "0:v:0", "-map", "[music]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output),
        ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        output.unlink(missing_ok=True)
        raise RuntimeError(result.stderr[-500:])
    if not output_is_valid(output):
        output.unlink(missing_ok=True)
        raise RuntimeError("Ausgabedatei enthält nach der Mischung nicht Video und Audio.")


def process() -> int:
    dry_run = test_mode()
    if dry_run:
        log("TESTMODUS aktiv: reservierte Blöcke dürfen gemischt werden; PUBLISHED.md und Publisher bleiben unangetastet.")

    if not PUBLISHED.exists():
        log("PUBLISHED.md fehlt – nichts zu bearbeiten.")
        return 0
    tracks = load_library()
    if not tracks:
        log("Keine vollständig dokumentierte lokale Musikdatei vorhanden.")
        return 0

    content = PUBLISHED.read_text(encoding="utf-8")
    pattern = re.compile(r"(^## (?:Instagram Reel|Reel|Story)(?:\s+\[[^\]]+\])?\s*\n.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    changed = 0

    for match in list(pattern.finditer(content)):
        block = match.group(1)
        if "[GEPOSTET" in block or not re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", block):
            continue
        if "Publication-Claim:" in block and not dry_run:
            log("Block bereits für Veröffentlichung reserviert – Musik-Agent verändert ihn nicht.")
            continue
        if not re.search(r"(?mi)^Musik:\s*auto\s*$", block):
            continue

        video_match = re.search(r"(?mi)^Video:\s*(?!auto\s*$)(\S+)", block)
        if not video_match:
            log("Freigegebener Block wartet auf einen echten Video-Pfad.")
            continue
        video = Path(video_match.group(1))
        if not video.exists() or not video.is_file():
            log(f"Video nicht gefunden: {video}")
            continue

        category = desired_category(block)
        track = choose_track(block, tracks)
        if not track:
            log(f"Kein dokumentierter lokaler Track für Kategorie '{category}' vorhanden – Block bleibt auf Musik: auto.")
            continue

        track_path = Path(str(track["path"]))
        if dry_run:
            output = TEST_OUTPUT / f"{video.stem}-musik-{track['id']}-TEST.mp4"
        else:
            output = video.with_name(f"{video.stem}-musik-{track['id']}.mp4")

        try:
            mix_music(video, track_path, output)
        except (OSError, RuntimeError) as error:
            log(f"Musikmischung fehlgeschlagen für {video}: {error}")
            continue

        if dry_run:
            changed += 1
            log(
                f"TEST ERFOLGREICH: {video.name} + {track['title']} → {output.as_posix()} | "
                f"Kategorie: {track['category']} | Lizenz: {track['license']} | Quelle: {track['source_page']} | "
                "PUBLISHED.md wurde nicht verändert."
            )
            continue

        updated = re.sub(r"(?mi)^Video:\s*\S+", f"Video: {output.as_posix()}", block, count=1)
        updated = re.sub(r"(?mi)^Musik:\s*auto\s*$", f"Musik: {track['title']}", updated, count=1)
        content = content.replace(block, updated, 1)
        changed += 1
        log(
            f"Gemischt: {video.name} + {track['title']} → {output.name} | "
            f"Kategorie: {track['category']} | Lizenz: {track['license']} | Quelle: {track['source_page']}"
        )

    if changed and not dry_run:
        PUBLISHED.write_text(content, encoding="utf-8")
    elif not changed:
        print("Keine passenden freigegebenen Videos mit Musik: auto gefunden.")
    return changed


if __name__ == "__main__":
    process()
