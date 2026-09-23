"""Instagram Engagement V1: sichere Event-Normalisierung und Community-Memory.

V1 sendet absichtlich keine Kommentare oder DMs. Eingehende, bereits über eine
offizielle Schnittstelle empfangene Events können verarbeitet und als
Freigabe-Entwurf gespeichert werden.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEMORY_FILE = Path("memory/INSTAGRAM_COMMUNITY.md")
QUEUE_FILE = Path("memory/INSTAGRAM_ENGAGEMENT_QUEUE.jsonl")
SEEN_FILE = Path("memory/INSTAGRAM_ENGAGEMENT_SEEN.txt")

CATEGORIES = ("FRAGE", "LOB", "KRITIK", "TRIGGER", "SPAM", "UNSICHER")
TRIGGERS = {"kurs", "info", "link", "mehr"}

def _clean(value: Any, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]

def classify(text: str) -> str:
    value = text.casefold().strip()
    words = set(re.findall(r"[\wäöüß]+", value))
    if not value:
        return "UNSICHER"
    if words & TRIGGERS:
        return "TRIGGER"
    if "?" in value or words & {"wie", "welche", "welcher", "wo", "warum", "was", "wann", "how", "what", "neden", "nasıl"}:
        return "FRAGE"
    if words & {"danke", "top", "stark", "super", "mega", "schön", "nice", "great", "teşekkürler", "harika"}:
        return "LOB"
    if words & {"schlecht", "falsch", "mist", "unsinn", "bad", "yanlış"}:
        return "KRITIK"
    if len(value) > 350 or value.count("http") > 1:
        return "SPAM"
    return "UNSICHER"

def normalize_event(payload: dict[str, Any]) -> dict[str, str]:
    event_id = _clean(payload.get("event_id") or payload.get("id"), 160)
    username = _clean(payload.get("username"), 100).lstrip("@")
    text = _clean(payload.get("text"), 1000)
    media_id = _clean(payload.get("media_id"), 160)
    event_type = _clean(payload.get("event_type") or "comment", 40).lower()
    timestamp = _clean(payload.get("timestamp"), 80) or datetime.now(timezone.utc).isoformat()
    if not event_id:
        raw = "|".join((event_type, username, media_id, timestamp, text))
        event_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
    return {
        "event_id": event_id, "event_type": event_type, "username": username,
        "media_id": media_id, "text": text, "timestamp": timestamp,
        "category": classify(text), "status": "PENDING_APPROVAL",
    }

def _seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return {line.strip() for line in SEEN_FILE.read_text(encoding="utf-8").splitlines() if line.strip()}

def _append_memory(event: dict[str, str]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            "# Instagram Community Memory\n\n"
            "Nur bestätigte öffentliche Interaktionen; keine Profilbesucher-Schätzung und keine sensiblen Profile.\n",
            encoding="utf-8",
        )
    line = (
        f"\n- {event['timestamp']} | @{event['username'] or 'unbekannt'} | "
        f"{event['event_type']} | {event['category']} | Media: {event['media_id'] or '-'}\n"
    )
    with MEMORY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line)

def ingest(payload: dict[str, Any]) -> dict[str, str]:
    event = normalize_event(payload)
    if event["event_id"] in _seen():
        return {**event, "status": "DUPLICATE"}
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    with SEEN_FILE.open("a", encoding="utf-8") as handle:
        handle.write(event["event_id"] + "\n")
    _append_memory(event)
    return event

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-json", required=True, help="Pfad zu einem normalisierten Instagram-Event")
    args = parser.parse_args()
    data = json.loads(Path(args.event_json).read_text(encoding="utf-8"))
    result = ingest(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
