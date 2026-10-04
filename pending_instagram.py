"""Manager for pending Instagram posts awaiting two-stage Telegram approval."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

PENDING_FILE = Path("memory/PENDING_INSTAGRAM.json")


def load_pending() -> list[dict[str, Any]]:
    """Loads the list of pending Instagram posts."""
    if not PENDING_FILE.exists():
        return []
    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
        return data.get("pending", []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"PENDING_INSTAGRAM: Error loading file: {e}")
        return []


def save_pending(items: list[dict[str, Any]]) -> None:
    """Saves the list of pending Instagram posts."""
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"pending": items}
    PENDING_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def add_pending(
    batch_id: str,
    auswahl: int,
    titel: str,
    text: str,
    bild_pfad: str,
    prompt_fuer_agnes: str,
    erstellt: str | None = None,
) -> dict[str, Any]:
    """Adds a new pending Instagram item."""
    if erstellt is None:
        erstellt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    item = {
        "batch_id": batch_id,
        "auswahl": auswahl,
        "titel": titel,
        "text": text,
        "bild_pfad": bild_pfad,
        "prompt_fuer_agnes": prompt_fuer_agnes,
        "erstellt": erstellt,
    }
    pending = load_pending()
    # Replace existing if batch_id and auswahl match
    filtered = [p for p in pending if not (p.get("batch_id") == batch_id and p.get("auswahl") == auswahl)]
    filtered.append(item)
    save_pending(filtered)
    return item


def get_first_pending() -> dict[str, Any] | None:
    """Returns the first pending item in queue, or None."""
    items = load_pending()
    return items[0] if items else None


def get_latest_pending() -> dict[str, Any] | None:
    """Returns the newest pending item, matching the image most recently shown in Telegram."""
    items = load_pending()
    return items[-1] if items else None


def get_recent_pending(max_age_seconds: int = 7200, now: datetime | None = None) -> list[dict[str, Any]]:
    """Return only fresh image approvals; stale queue entries are never publish authority."""
    if max_age_seconds < 1:
        return []
    now = now or datetime.now(timezone.utc)
    out = []
    for item in load_pending():
        raw = item.get("erstellt")
        if not isinstance(raw, str):
            continue
        try:
            stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if stamp.tzinfo is None:
            continue
        age = (now - stamp.astimezone(timezone.utc)).total_seconds()
        if 0 <= age <= max_age_seconds:
            out.append(item)
    return out


def remove_pending(batch_id: str, auswahl: int) -> dict[str, Any] | None:
    """Removes a pending item matching batch_id and auswahl."""
    pending = load_pending()
    removed = None
    remaining = []
    for item in pending:
        if item.get("batch_id") == batch_id and item.get("auswahl") == auswahl:
            removed = item
        else:
            remaining.append(item)
    save_pending(remaining)
    return removed


def update_pending_image(batch_id: str, auswahl: int, new_bild_pfad: str) -> dict[str, Any] | None:
    """Updates bild_pfad for a pending item."""
    pending = load_pending()
    updated_item = None
    for item in pending:
        if item.get("batch_id") == batch_id and item.get("auswahl") == auswahl:
            item["bild_pfad"] = new_bild_pfad
            updated_item = item
            break
    if updated_item:
        save_pending(pending)
    return updated_item
