"""Sichere Phase-1-Migration: erst Inventar, dann optionales Verschieben ohne Löschung."""
from __future__ import annotations

import argparse
import re
import shutil
from datetime import date, datetime
from pathlib import Path

from asset_paths import get_image_path, get_poster_path, get_published_path, get_test_path, get_video_path, slugify

PUBLISHED = Path("content/PUBLISHED.md")
INVENTORY = Path("memory/ASSET_INVENTORY.md")
LOG = Path("memory/MIGRATION_LOG.md")
MEDIA_PATTERN = re.compile(r"^(?:auto-image-.*\.jpg|auto-video-.*\.mp4|test-agnes-.*\.(?:jpg|png|mp4)|.+\.(?:jpg|jpeg|png|mp4))$", re.IGNORECASE)


def blocks(content: str):
    return re.finditer(r"(?ms)^(## .+?)(?:\n(.*?))(?=^## |\Z)", content)


def unique_destination(target: Path) -> Path:
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    index = 2
    while True:
        candidate = target.with_name(f"{stem}-{index:02d}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def published_destination(header: str, source: Path) -> Path:
    posted = re.search(r"\[GEPOSTET\s+(\d{4}-\d{2}-\d{2})", header)
    day = date.fromisoformat(posted.group(1)) if posted else date.today()
    platform = "instagram" if "instagram" in header.lower() else "facebook" if "facebook" in header.lower() else "story"
    media_type = "story" if "story" in header.lower() else "reel" if "reel" in header.lower() else "post"
    return unique_destination(get_published_path(day, platform, media_type, extension=source.suffix.lstrip(".")))


def plan_migration(content: str):
    planned: list[dict[str, object]] = []
    referenced: set[str] = set()
    for match in blocks(content):
        header, body = match.group(1), match.group(2) or ""
        is_posted = "[GEPOSTET" in header
        title_match = re.search(r"(?m)^Titel:\s*(.+)$", body) or re.search(r"(?ms)^Text:\s*(.+?)(?=^(?:Bild|Video|Bilder|Status|Freigabe):|\Z)", body)
        title = title_match.group(1).strip().splitlines()[0] if title_match else "legacy-media"
        for field, filename in re.findall(r"(?m)^(Bild|Video):\s*([^\s]+)", body):
            if filename.lower() == "auto" or "/" in filename or not Path(filename).is_file():
                continue
            source = Path(filename)
            referenced.add(source.name.lower())
            if is_posted:
                target = published_destination(header, source)
            elif field == "Video":
                target = unique_destination(get_video_path(slugify(title)))
            else:
                target = unique_destination(get_image_path(slugify(title)))
            planned.append({"source": source, "target": target, "reference": filename, "posted": is_posted})

    for source in Path(".").iterdir():
        if not source.is_file() or not MEDIA_PATTERN.match(source.name) or source.name.lower() in referenced:
            continue
        lower = source.name.lower()
        if lower.startswith("test-agnes-"):
            target = get_test_path(source.name.replace("test-agnes-", "test-"))
        elif lower.startswith("auto-image-"):
            target = unique_destination(get_image_path("legacy-content"))
        elif lower.startswith("auto-video-"):
            target = unique_destination(get_video_path("legacy-content"))
        else:
            target = Path("assets/user-assets") / source.name.lower()
        planned.append({"source": source, "target": target, "reference": None, "posted": False})
    return planned


def write_inventory(plan):
    lines = ["# Asset-Inventar", "", f"Stand: {datetime.now():%Y-%m-%d %H:%M}", "", "| Datei | Typ | In PUBLISHED.md | Ziel-Pfad |", "|---|---|---|---|"]
    for item in plan:
        source, target = item["source"], item["target"]
        kind = "Video" if source.suffix.lower() == ".mp4" else "Bild"
        used = "Ja" if item["reference"] else "Nein"
        lines.append(f"| {source.as_posix()} | {kind} | {used} | {target.as_posix()} |")
    if not plan:
        lines.append("| – | – | Keine Root-Medien gefunden | – |")
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply(plan, content: str):
    moved, warnings = [], []
    updated = content
    for item in plan:
        source, target = item["source"], item["target"]
        if not source.exists():
            warnings.append(f"Fehlt: {source}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        if item["reference"]:
            updated = re.sub(rf"(?m)^((?:Bild|Video):\s*){re.escape(str(item['reference']))}\s*$", rf"\g<1>{target.as_posix()}", updated)
        moved.append(f"{source.as_posix()} → {target.as_posix()}")
    PUBLISHED.write_text(updated, encoding="utf-8")
    return moved, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Verschiebt erst nach vorheriger Inventar-Prüfung.")
    args = parser.parse_args()
    content = PUBLISHED.read_text(encoding="utf-8") if PUBLISHED.exists() else ""
    plan = plan_migration(content)
    write_inventory(plan)
    if not args.apply:
        print(f"Vorschau erstellt: {len(plan)} Datei(en). Keine Datei wurde verschoben.")
        return

    moved, warnings = apply(plan, content)
    lines = ["# Migrationslog", "", f"Stand: {datetime.now():%Y-%m-%d %H:%M}", "", "## Verschoben"]
    lines.extend(f"- {entry}" for entry in moved) or lines.append("- Keine Dateien verschoben.")
    if warnings:
        lines += ["", "## Manuell prüfen"] + [f"- {entry}" for entry in warnings]
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Migration abgeschlossen: {len(moved)} verschoben, {len(warnings)} Warnung(en).")


if __name__ == "__main__":
    main()
