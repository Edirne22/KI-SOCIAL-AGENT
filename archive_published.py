#!/usr/bin/env python3
"""
archive_published.py - Rollierende Archivierung für content/PUBLISHED.md

Regeln:
1. Sicherheit: Stellen sicher, dass content/PUBLISHED.md.bak.2026-09-17-b existiert (Backup).
2. Liest content/PUBLISHED.md.
3. Blöcke parsen:
   - Header "# Freigegebene Beiträge" bleibt immer als oberster Teil der Datei.
   - Blöcke sind getrennt durch '\n(?=## )'.
4. Für jeden Block:
   - Header [GEPOSTET <timestamp>] finden (z.B. [GEPOSTET 2026-09-11 19:51...]):
     - Standardmäßig: Wenn Timestamp älter als 7 Tage (d.h. Timestamp < ref_date - 7 Tage) -> ins Archiv verschieben.
     - Bei --initial (Erster Lauf): Alle Blöcke vor dem heutigen Tag (17.09.2026 bzw. ref_date.date()) ins Archiv verschieben.
   - Status: FREIGEGEBEN aber ohne [GEPOSTET]:
     - Datum im Block suchen; wenn älter als 14 Tage -> Status auf VERWORFEN setzen (bleibt in PUBLISHED.md).
   - Status: ENTWURF -> nicht anfassen.
   - FREIGEGEBEN unter 14 Tage -> nicht anfassen.
   - Alles andere bleibt unberührt.
5. Archiv-Ziel:
   - Datei: content/archive/PUBLISHED_YYYY-MM.md (monatlich, z.B. PUBLISHED_2026-09.md).
   - Neue Blöcke oben einfügen (neueste zuerst).
6. Log-Ausgabe Format:
   ARCHIVE: X Blöcke archiviert → content/archive/PUBLISHED_YYYY-MM.md
   ARCHIVE: Y Blöcke älter als 14 Tage → Status VERWORFEN
   ARCHIVE: Z Blöcke bleiben (unter Frist)
"""

import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent
PUBLISHED_FILE = ROOT / "content" / "PUBLISHED.md"
BACKUP_FILE = ROOT / "content" / "PUBLISHED.md.bak.2026-09-17-b"
ARCHIVE_DIR = ROOT / "content" / "archive"

def parse_posted_timestamp(header_line):
    """Extrahiert Timestamp aus [GEPOSTET YYYY-MM-DD HH:MM...] im Block-Header."""
    m = re.search(r"\[GEPOSTET\s+(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?", header_line)
    if not m:
        return None
    date_str = m.group(1)
    time_str = m.group(2) if m.group(2) else "00:00"
    try:
        dt_str = f"{date_str} {time_str}"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M" if len(time_str) == 5 else "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

def parse_block_date(block):
    """Sucht nach einem Datumsstempel YYYY-MM-DD im Block (z.B. aus Erstellung/Header/Body)."""
    lines = block.strip().split("\n")
    header = lines[0] if lines else ""
    ts = parse_posted_timestamp(header)
    if ts:
        return ts

    for line in lines:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", line)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
    return None

def archive_published(now_dt=None, initial_run=False, days_posted=7, days_unposted=14):
    if now_dt is None:
        now_dt = datetime.now(timezone.utc)

    # 1. Sicherheits-Backup prüfen / anlegen
    if not BACKUP_FILE.exists():
        if PUBLISHED_FILE.exists():
            BACKUP_FILE.write_bytes(PUBLISHED_FILE.read_bytes())
            print(f"SAFETY: Backup angelegt: {BACKUP_FILE.relative_to(ROOT)}")
        else:
            print(f"ERROR: {PUBLISHED_FILE} existiert nicht!")
            return

    if not PUBLISHED_FILE.exists():
        print(f"ERROR: {PUBLISHED_FILE} nicht gefunden.")
        return

    content = PUBLISHED_FILE.read_text(encoding="utf-8")

    # Blöcke separieren
    raw_blocks = re.split(r"\n(?=## )", content)
    file_header = ""
    blocks = []

    if raw_blocks and not raw_blocks[0].startswith("## "):
        file_header = raw_blocks[0]
        blocks = raw_blocks[1:]
    else:
        blocks = raw_blocks

    kept_blocks = []
    archived_by_month = {}  # "YYYY-MM": list of block strings
    discarded_count = 0
    archived_count = 0
    remaining_count = 0

    for block in blocks:
        lines = block.strip().split("\n")
        header = lines[0] if lines else ""

        posted_dt = parse_posted_timestamp(header)

        # Prüfen ob Block [GEPOSTET] hat
        if posted_dt is not None:
            should_archive = False
            if initial_run:
                # Erster Lauf: Alle Blöcke vor dem heutigen Tag (now_dt.date()) archivieren
                if posted_dt.date() < now_dt.date():
                    should_archive = True
            else:
                age_days = (now_dt - posted_dt).total_seconds() / 86400.0
                if age_days > float(days_posted):
                    should_archive = True

            if should_archive:
                archived_count += 1
                month_key = posted_dt.strftime("%Y-%m-%d")[:7] # YYYY-MM
                archived_by_month.setdefault(month_key, []).append(block.strip())
                continue
            else:
                kept_blocks.append(block.strip())
                remaining_count += 1
                continue

        # Block ist nicht GEPOSTET. Prüfen auf Status: FREIGEGEBEN
        is_freigegeben = bool(re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", block))

        if is_freigegeben:
            block_dt = parse_block_date(block)
            if block_dt is not None:
                age_days = (now_dt - block_dt).total_seconds() / 86400.0
                if age_days > float(days_unposted):
                    # Status auf VERWORFEN setzen
                    updated_block = re.sub(
                        r"(?mi)^(Status:\s*)FREIGEGEBEN\s*$",
                        r"\1VERWORFEN",
                        block
                    )
                    kept_blocks.append(updated_block.strip())
                    discarded_count += 1
                    continue

        # Alles andere bleibt unberührt (einschließlich Status: ENTWURF, FREIGEGEBEN < 14 Tage, etc.)
        kept_blocks.append(block.strip())
        remaining_count += 1

    # 5. Archivdateien schreiben
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for month_key, month_blocks in archived_by_month.items():
        archive_path = ARCHIVE_DIR / f"PUBLISHED_{month_key}.md"

        existing_archived_blocks = []
        archive_header = f"# Archiviert Beiträge {month_key}\n"

        if archive_path.exists():
            arch_content = archive_path.read_text(encoding="utf-8")
            raw_arch = re.split(r"\n(?=## )", arch_content)
            if raw_arch and not raw_arch[0].startswith("## "):
                archive_header = raw_arch[0]
                existing_archived_blocks = [b.strip() for b in raw_arch[1:] if b.strip()]
            else:
                existing_archived_blocks = [b.strip() for b in raw_arch if b.strip()]

        # Neue Blöcke oben einfügen (neueste zuerst)
        all_archived = month_blocks + existing_archived_blocks

        new_arch_content = archive_header.rstrip() + "\n\n" + "\n\n".join(all_archived) + "\n"
        archive_path.write_text(new_arch_content, encoding="utf-8")

        print(f"ARCHIVE: {len(month_blocks)} Blöcke archiviert → {archive_path.relative_to(ROOT)}")

    print(f"ARCHIVE: {discarded_count} Blöcke älter als 14 Tage → Status VERWORFEN")
    print(f"ARCHIVE: {remaining_count} Blöcke bleiben (unter Frist)")

    # PUBLISHED.md aktualisieren
    new_published_content = file_header.rstrip()
    if kept_blocks:
        new_published_content += "\n\n" + "\n\n".join(kept_blocks) + "\n"
    else:
        new_published_content += "\n"

    PUBLISHED_FILE.write_text(new_published_content, encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rollierende Archivierung für PUBLISHED.md")
    parser.add_argument("--initial", action="store_true", help="Erster Lauf: archiviert alle [GEPOSTET]-Blöcke vor dem heutigen Tag")
    parser.add_argument("--days-posted", type=int, default=7, help="Tage-Frist für GEPOSTET Blöcke (Standard: 7)")
    parser.add_argument("--days-unposted", type=int, default=14, help="Tage-Frist für FREIGEGEBEN Blöcke (Standard: 14)")
    args = parser.parse_args()

    archive_published(initial_run=args.initial, days_posted=args.days_posted, days_unposted=args.days_unposted)
