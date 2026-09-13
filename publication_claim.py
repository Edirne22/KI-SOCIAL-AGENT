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
DUPLICATES = Path("memory/PUBLICATION_DUPLICATES.md")
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


def _is_publishable(block: str, target: str) -> bool:
    if (
        "[GEPOSTET" in block
        or CLAIM_READY in block
        or CLAIM_ACTIVE in block
        or not re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", block)
    ):
        return False
    if target == "facebook":
        return bool(re.search(r"(?ms)^Text:\s*\S+", block))
    if target == "instagram":
        return bool(re.search(r"(?mi)^Bild:\s*(?!auto\s*$)\S+", block))
    if target == "story":
        return bool(re.search(r"(?mi)^(?:Bild|Video):\s*(?!auto\s*$)\S+", block))
    if target == "reel":
        return bool(re.search(r"(?mi)^Video:\s*(?!auto\s*$)\S+", block))
    images = re.findall(r"(?mi)^\s*-\s*(\S+)", block)
    return len(images) >= 2


def _text_key(block: str) -> str:
    match = re.search(
        r"(?ms)^Text:\s*(.*?)(?=^(?:Bild|Video|Bilder|Freigabe|Status|Publication-Claim):|\Z)",
        block,
    )
    return re.sub(r"\s+", " ", match.group(1).strip().lower()) if match else ""


def _write_duplicates(target: str, texts: list[str]) -> None:
    if not texts:
        return
    DUPLICATES.parent.mkdir(parents=True, exist_ok=True)
    old = DUPLICATES.read_text(encoding="utf-8") if DUPLICATES.exists() else "# Veröffentlichungs-Duplikate\n"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"\n## {stamp} – {target}", "- Status: NICHT automatisch veröffentlicht", "- Grund: Mehrere freigegebene Blöcke haben denselben Text.", "- Bitte einen Block manuell behalten oder Inhalte unterscheiden.", ""]
    for index, text in enumerate(texts, 1):
        lines.append(f"- Duplikat {index}: {text[:180]}")
    DUPLICATES.write_text(old.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def claim(target: str) -> bool:
    if not PUBLISHED.exists():
        print("PUBLISHED.md nicht gefunden – keine Reservierung angelegt.")
        return False
    content = PUBLISHED.read_text(encoding="utf-8")
    # Duplikate werden unabhängig von der Medienreife geprüft. Sonst könnten
    # zwei gleiche Reel-Entwürfe an aufeinanderfolgenden Tagen durchrutschen.
    approved = [
        match.group(1)
        for match in _blocks(content, target)
        if "[GEPOSTET" not in match.group(1)
        and CLAIM_READY not in match.group(1)
        and CLAIM_ACTIVE not in match.group(1)
        and re.search(r"(?mi)^Status:\s*FREIGEGEBEN\s*$", match.group(1))
    ]
    duplicate_keys = {
        key for key in (_text_key(block) for block in approved)
        if key and sum(_text_key(other) == key for other in approved) > 1
    }
    if duplicate_keys:
        _write_duplicates(target, [key for key in sorted(duplicate_keys)])

    for match in _blocks(content, target):
        block = match.group(1)
        if not _is_publishable(block, target):
            continue
        if _text_key(block) in duplicate_keys:
            print(f"{target}: Duplikat erkannt – nicht automatisch reserviert.")
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


def start(target: str, token: str) -> bool:
    if not PUBLISHED.exists():
        print("PUBLISHED.md nicht gefunden – keine Reservierung gestartet.")
        return False
    content = PUBLISHED.read_text(encoding="utf-8")
    for match in _blocks(content, target):
        block = match.group(1)
        if CLAIM_READY not in block or CLAIM_ACTIVE in block:
            continue
        updated = block.replace(CLAIM_READY, f"{CLAIM_ACTIVE} {token}", 1)
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
    parser.add_argument("--token", help="Eindeutiger GitHub-Run-Token; erforderlich bei --start.")
    args = parser.parse_args()
    if args.start and not args.token:
        parser.error("--start benötigt --token")
    if args.claim:
        claim(args.platform)
    else:
        start(args.platform, args.token)


if __name__ == "__main__":
    main()
