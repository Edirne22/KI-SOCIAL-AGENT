"""Offline TÜV for local project navigation; no network, secrets or publishing."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("INDEX.md", "docs/ARCHITEKTUR_INDEX.md", "README.md")
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
GITHUB_PREFIX = "https://github.com/Edirne22/KI-SOCIAL-AGENT/"


def inspect_link(page: Path, raw: str) -> str | None:
    target = raw.strip().split("#", 1)[0]
    if not target or target.startswith(("mailto:", "tel:")):
        return None
    if target.startswith(GITHUB_PREFIX):
        # Repository-local tree/blob links are checked, but action-run and PR URLs
        # are intentionally external evidence, not filesystem paths.
        suffix = target[len(GITHUB_PREFIX):]
        if suffix.startswith(("blob/main/", "tree/main/")):
            target = suffix.split("/", 2)[2]
            resolved = ROOT / unquote(target)
        elif suffix.startswith(("tree/backup/", "blob/backup/")):
            # Frozen recovery branch is not part of the checked-out main tree.
            return None
        else:
            return None
    elif urlparse(target).scheme or target.startswith("//"):
        return None
    else:
        resolved = page.parent / unquote(target)
    try:
        path = resolved.resolve(strict=False)
        path.relative_to(ROOT.resolve())
    except (ValueError, OSError):
        return f"ESCAPES_REPOSITORY: {raw}"
    if not path.exists():
        return f"MISSING: {raw} -> {path.relative_to(ROOT)}"
    return None


def main() -> int:
    errors = []
    checked = 0
    for name in PAGES:
        page = ROOT / name
        if not page.is_file():
            errors.append(f"MISSING_INDEX: {name}")
            continue
        for match in LINK.finditer(page.read_text(encoding="utf-8")):
            checked += 1
            issue = inspect_link(page, match.group(1))
            if issue:
                errors.append(f"{name}: {issue}")
    for issue in errors:
        print("FAIL", issue)
    print(f"PROJECT_NAVIGATION_TUV checked={checked} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
