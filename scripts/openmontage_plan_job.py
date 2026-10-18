"""Plan a motorsport film using verified sources; never invent news or publish."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from openmontage_research import build_research
from openmontage_fact_checker import verify_research_payload
from openmontage_storyboard import build_storyboard
from openmontage_media_sourcing import build_media_manifest


def plan(prompt: str, destination: Path) -> dict:
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000:
        raise ValueError("Filmthema fehlt oder überschreitet 2000 Zeichen")
    research = build_research(prompt.strip())
    verified = verify_research_payload(research)
    if verified.get("verified_item_count", 0) < 1:
        raise ValueError("Keine frischen, überprüfbaren Nachrichten gefunden; kein Film erfunden")
    storyboard = build_storyboard(verified)
    manifest = build_media_manifest(storyboard)
    if not manifest.get("all_rights_verified"):
        raise ValueError("Medienrechte nicht geprüft; kein Filmauftrag")
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in (("research.json", verified), ("storyboard.json", storyboard), ("media_manifest.json", manifest)):
        (destination / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"verified_stories": verified["verified_item_count"], "scenes": len(storyboard["scenes"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(plan(args.prompt, args.output)))
