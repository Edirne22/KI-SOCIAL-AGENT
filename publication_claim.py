"""Reserviert genau einen freigegebenen Beitrag vor einer externen Veröffentlichung.

Die Reservierung wird vor dem Plattform-Aufruf nach Git gepusht. So verhindert das
System einen Doppelpost, wenn ein späterer Plattform- oder Git-Schritt unklar
abbricht. Ein hängen gebliebener Claim wird niemals automatisch erneut gesendet.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

PUBLISHED = Path("content/PUBLISHED.md")
CLAIM_READY = "Publication-Claim: BEREIT"
CLAIM_ACTIVE = "Publication-Claim: IN_BEARBEITUNG"

TARGETS = {
    "instagram": r"Instagram",
    "story": r"Story",
    "reel": r"(?:Instagram Reel|Reel)",
    "facebook": r"Facebook",
    "instagram-carousel": r"Instagram Karussell",
    "facebook-carousel": r"Facebook Karussell",
}


def _blocks(content: str, target: str):
    header = TARGETS[target]
    pattern = re.compile(
        rf"(^## {header}\s*\n.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    return list(pattern.finditer(content))


def _is_publishable(block: str) -> bool:
    return (
        "[GEPOSTET" not in block
        and CLAIM_READY not in block
        and CLAIM_ACTIVE not in block
        and bool(re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", block))
    )


def claim(target: str) -> bool:
    if not PUBLISHED.exists():
        print("PUBLISHED.md nicht gefunden – keine Reservierung angelegt.")
        return False
    content = PUBLISHED.read_text(encoding="utf-8")
    for match in _blocks(content, target):
        block = match.group(1)
        if not _is_publishable(block):
            continue
        updated = re.sub(
            r"(?mi)^(Status:\s*FREIGEGEBEN\s*)$",
            rf"\1\n{CLAIM_READY}",
            block,
            count=1,
        )
        PUBLISHED.write_text(content[:match.start()] + updated + content[match.end():], encoding="utf-8")
        print(f"Reserviert für Veröffentlichung: {target}.")
        return True
    print(f"Kein freigegebener, unreservierter {target}-Block gefunden.")
    return False


def start(target: str) -> bool:
    if not PUBLISHED.exists():
        print("PUBLISHED.md nicht gefunden – keine Reservierung gestartet.")
        return False
    content = PUBLISHED.read_text(encoding="utf-8")
    for match in _blocks(content, target):
        block = match.group(1)
        if CLAIM_READY not in block or CLAIM_ACTIVE in block:
            continue
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        updated = block.replace(CLAIM_READY, f"{CLAIM_ACTIVE} seit {stamp}", 1)
        PUBLISHED.write_text(content[:match.start()] + updated + content[match.end():], encoding="utf-8")
        print(f"Veröffentlichung gestartet: {target}.")
        return True
    print(f"Kein bereiter {target}-Claim gefunden.")
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=sorted(TARGETS), required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--claim", action="store_true")
    action.add_argument("--start", action="store_true")
    args = parser.parse_args()
    (claim if args.claim else start)(args.platform)


if __name__ == "__main__":
    main()
