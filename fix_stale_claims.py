import shutil
import re
from pathlib import Path

published_path = Path("content/PUBLISHED.md")
backup_path = Path("content/PUBLISHED.md.bak.2026-09-17")

def cleanup_published():
    if not published_path.exists():
        print("PUBLISHED.md nicht gefunden.")
        return

    # 1. Backup erstellen
    shutil.copy2(published_path, backup_path)
    print(f"Backup erstellt: {backup_path}")

    content = published_path.read_text(encoding="utf-8")

    stale_claims_fixed = 0

    def process_block(match):
        nonlocal stale_claims_fixed
        block = match.group(0)
        header_line = block.splitlines()[0]

        if "[GEPOSTET" in header_line and "Publication-Claim:" in block:
            stale_claims_fixed += 1
            block = re.sub(
                r"(?mi)^Status:\s*FREIGEGEBEN\s*$",
                "Status: GEPOSTET",
                block
            )
            block = re.sub(
                r"(?mi)^Publication-Claim:[^\n]*\r?\n?",
                "",
                block
            )
        return block

    pattern = re.compile(r"^## .*?(?=\n## |\Z)", re.MULTILINE | re.DOTALL)
    cleaned_content = pattern.sub(process_block, content)

    published_path.write_text(cleaned_content, encoding="utf-8")
    print(f"PUBLISHED.md bereinigt. Anzahlen korrigierter Blöcke: {stale_claims_fixed}")

if __name__ == "__main__":
    cleanup_published()
