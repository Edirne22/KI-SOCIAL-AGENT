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


def reserve_destination(target: Path, reserved: set[str]) -> Path:
    """Reserviert Zielnamen schon während der Vorschau, nicht erst beim Verschieben."""
    candidate = target
    index = 2
    while candidate.exists() or candidate.as_posix() in reserved:
        candidate = target.with_name(f"{target.stem}-{index:02d}{target.suffix}")
        index += 1
    reserved.add(candidate.as_posix())
    return candidate


def published_destination(header: str, source: Path, reserved: set[str]) -> Path:
    posted = re.search(r"\[GEPOSTET\s+(\d{4}-\d{2}-\d{2})", header)
    if not posted:
        raise ValueError("Nur nachweislich gepostete Blöcke dürfen nach assets/published/ wandern.")
    day = date.fromisoformat(posted.group(1))
    platform = "instagram" if "instagram" in header.lower() else "facebook" if "facebook" in header.lower() else "story"
    media_type = "story" if "story" in header.lower() else "reel" if "reel" in header.lower() else "post"
    target = get_published_path(day, platform, media_type, extension=source.suffix.lower().lstrip("."))
    return reserve_destination(target, reserved)


def plan_migration(content: str):
    planned: list[dict[str, object]] = []
    referenced: set[str] = set()
    reserved: set[str] = set()
    for match in blocks(content):
        header, body = match.group(1), match.group(2) or ""
        is_posted = bool(re.search(r"\[GEPOSTET\s+\d{4}-\d{2}-\d{2}", header))
        title_match = re.search(r"(?m)^Titel:\s*(.+)$", body) or re.search(r"(?ms)^Text:\s*(.+?)(?=^(?:Bild|Video|Bilder|Status|Freigabe):|\Z)", body)
        title = title_match.group(1).strip().splitlines()[0] if title_match else "legacy-media"
        for field, filename in re.findall(r"(?m)^(Bild|Video):\s*([^\s]+)", body):
            if filename.lower() == "auto" or "/" in filename or not Path(filename).is_file():
                continue
            source = Path(filename)
            referenced.add(source.name.lower())
            if is_posted:
                target = published_destination(header, source, reserved)
            elif field == "Video":
                target = reserve_destination(get_video_path(slugify(title)), reserved)
            else:
                target = reserve_destination(get_image_path(slugify(title)), reserved)
            planned.append({"source": source, "target": target, "reference": filename, "posted": is_posted})

    for source in Path(".").iterdir():
        if not source.is_file() or not MEDIA_PATTERN.match(source.name) or source.name.lower() in referenced:
            continue
        lower = source.name.lower()
        if lower.startswith("test-agnes-"):
            candidate = get_test_path(source.name.replace("test-agnes-", "test-"))
            target = reserve_destination(candidate, reserved)
        elif lower.startswith("auto-image-"):
            target = reserve_destination(get_image_path("legacy-content"), reserved)
        elif lower.startswith("auto-video-"):
            target = reserve_destination(get_video_path("legacy-content"), reserved)
        else:
            target = reserve_destination(Path("assets/user-assets") / (source.stem.lower() + source.suffix.lower()), reserved)
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
