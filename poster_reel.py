"""Erzeugt aus freigegebenen oder entworfenen Rennpostern kurze Reel-Videos.

Der Generator erstellt nur ein neutrales 9:16-Video aus einer vorhandenen
Bildvorlage. Musik und Veröffentlichung erfolgen ausschließlich in den bereits
vorhandenen, getrennten Workflows.
"""
from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

PUBLISHED = Path("content/PUBLISHED.md")
VIDEO_DIR = Path("assets/videos") / datetime.now().strftime("%Y-%m")
WAITING = "WARTET_AUF_POSTER_REEL"


def blocks(content: str):
    matches = list(re.finditer(r"(?m)^## Instagram Reel\s*$", content))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        yield match.start(), end, content[match.start():end]


def render(image: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(image),
        "-t", "8", "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-an", str(output),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def main() -> None:
    if not PUBLISHED.exists():
        print("[poster-reel] PUBLISHED.md fehlt.")
        return
    content = PUBLISHED.read_text(encoding="utf-8")
    changed = False

    for start, end, block in list(blocks(content))[::-1]:
        if WAITING not in block:
            continue
        image_match = re.search(r"(?m)^Poster:\s*(.+?)\s*$", block)
        if not image_match:
            print("[poster-reel] Übersprungen: Poster-Pfad fehlt.")
            continue
        image = Path(image_match.group(1).strip())
        if not image.exists():
            print(f"[poster-reel] Übersprungen: Bild nicht gefunden: {image}")
            continue
        slug_match = re.search(r"(?m)^Titel:\s*(.+?)\s*$", block)
        slug = re.sub(r"[^a-z0-9]+", "-", (slug_match.group(1) if slug_match else image.stem).lower()).strip("-")[:60]
        output = VIDEO_DIR / f"{datetime.now():%Y-%m-%d}-{slug}-reel.mp4"
        try:
            render(image, output)
        except (OSError, subprocess.CalledProcessError) as error:
            print(f"[poster-reel] Video fehlgeschlagen: {error}")
            continue
        updated = block.replace(f"Video: {WAITING}", f"Video: {output.as_posix()}", 1)
        content = content[:start] + updated + content[end:]
        changed = True
        print(f"[poster-reel] 9:16-Reel erzeugt: {output}")

    if changed:
        PUBLISHED.write_text(content, encoding="utf-8")
    else:
        print("[poster-reel] Kein wartender Poster-Reel-Entwurf gefunden.")


if __name__ == "__main__":
    main()
