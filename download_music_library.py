"""Lädt die kleine Startbibliothek aus verifizierten Public-Domain/CC0-Quellen.

Dieser Initialisierer wird nur über den manuellen GitHub-Workflow ausgeführt.
Die Dateien werden in einem öffentlichen Repository gespeichert; deshalb sind
ausschließlich Tracks mit klar dokumentierter Public-Domain- oder CC0-Freigabe
enthalten.
"""

from __future__ import annotations

import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TRACKS = (
    {
        "path": "assets/musik/racing/beat-electronic.ogg",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Beat_electronic.ogg",
        "title": "Beat, electronic",
    },
    {
        "path": "assets/musik/travel/dance-electronic-fairies.ogg",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Monplaisir_-_03_-_Dance_of_the_electronic_fairies.ogg",
        "title": "Dance of the electronic fairies",
    },
    {
        "path": "assets/musik/chill/hypnotic-ambient.mp3",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Hypnotic_ambient_electronic_music_by_MusicLM.mp3",
        "title": "Hypnotic ambient electronic music",
    },
)
LOG = Path("memory/MUSIC_LIBRARY_SETUP.md")


def write_log(lines: list[str]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    LOG.write_text("# Musikbibliothek – Einrichtung\n\n" + f"Stand: {stamp}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def download(track: dict) -> str:
    target = Path(track["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1024:
        return f"Bereits vorhanden: {target}"
    request = urllib.request.Request(track["url"], headers={"User-Agent": "KI-SOCIAL-AGENT/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get_content_type()
        data = response.read()
    if not content_type.startswith("audio/") or len(data) < 1024:
        raise RuntimeError(f"Unerwartete Antwort ({content_type}, {len(data)} Bytes)")
    target.write_bytes(data)
    return f"Heruntergeladen: {target} ({len(data)} Bytes)"


if __name__ == "__main__":
    entries = []
    failed = False
    for track in TRACKS:
        try:
            message = download(track)
            print(message)
            entries.append(f"- ✅ {track['title']}: {message}")
        except Exception as error:
            failed = True
            print(f"Fehler bei {track['title']}: {error}")
            entries.append(f"- ❌ {track['title']}: {error}")
    write_log(entries)
    if failed:
        raise SystemExit(1)
