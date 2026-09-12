"""Bright-Data-Adapter: speichert öffentliche Treffer lesbar mit Titel, Datum, URL und Kennzahlen."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from .search_config import BRIGHTDATA_DATASETS

OUT = Path("memory/INSPIRATION_BRIGHTDATA.md")
API = "https://api.brightdata.com/datasets/v3"


def _value(record: dict, names: tuple[str, ...]) -> str:
    for name in names:
        value = record.get(name)
        if value not in (None, "", [], {}):
            return str(value)
    return "nicht verfügbar"


def _records(payload) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "items", "records"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def _format_records(platform: str, records: list[dict]) -> list[str]:
    lines = [f"## {platform}"]
    if not records:
        return lines + ["Keine konkreten Datensätze erhalten."]
    lines.append(f"Konkrete Datensätze: {len(records)}")
    for index, record in enumerate(records, start=1):
        title = _value(record, ("title", "caption", "text", "description", "name"))
        url = _value(record, ("url", "post_url", "link", "permalink", "video_url"))
        published = _value(record, ("published_at", "date", "timestamp", "created_at", "time"))
        likes = _value(record, ("likes", "like_count", "likes_count"))
        comments = _value(record, ("comments", "comments_count", "comment_count"))
        views = _value(record, ("views", "view_count", "plays"))
        lines += [
            f"### Datensatz {index}",
            f"- Titel: {title}",
            f"- Datum: {published}",
            f"- URL: {url}",
            f"- Likes: {likes}",
            f"- Kommentare: {comments}",
            f"- Views: {views}",
        ]
    return lines


def _download_snapshot(snapshot_id: str, headers: dict) -> list[dict]:
    for _ in range(6):
        progress = requests.get(f"{API}/progress/{snapshot_id}", headers=headers, timeout=30)
        if progress.status_code == 200 and progress.json().get("status") == "ready":
            response = requests.get(f"{API}/snapshot/{snapshot_id}", headers=headers, params={"format": "json"}, timeout=60)
            return _records(response.json()) if response.status_code == 200 else []
        time.sleep(5)
    return []


def run() -> str:
    token = os.environ.get("BRIGHTDATA_API_TOKEN")
    lines = ["# Inspiration · Bright Data", ""]
    if not token:
        lines.append("Nicht konfiguriert: BRIGHTDATA_API_TOKEN fehlt.")
    else:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        for platform, dataset in BRIGHTDATA_DATASETS.items():
            dataset = os.environ.get(f"BRIGHTDATA_{platform.upper()}_DATASET_ID", dataset)
            if not dataset:
                lines += [f"## {platform}", "Keine Daten von Bright Data: Dataset-ID fehlt.", ""]
                continue
            try:
                response = requests.post(
                    f"{API}/scrape",
                    headers=headers,
                    params={"dataset_id": dataset},
                    json={"input": [{"url": f"https://www.{platform}.com/"}]},
                    timeout=90,
                )
                if response.status_code == 200:
                    records = _records(response.json())
                    lines.extend(_format_records(platform, records))
                elif response.status_code == 202:
                    payload = response.json() if response.content else {}
                    snapshot_id = payload.get("snapshot_id") or payload.get("id")
                    records = _download_snapshot(str(snapshot_id), headers) if snapshot_id else []
                    if records:
                        lines.extend(_format_records(platform, records))
                    else:
                        lines += [f"## {platform}", "Keine Daten von Bright Data: Snapshot noch nicht bereit.", ""]
                else:
                    lines += [f"## {platform}", f"Keine Daten von Bright Data: HTTP {response.status_code}.", ""]
            except (requests.RequestException, ValueError, json.JSONDecodeError) as error:
                lines += [f"## {platform}", f"Keine Daten von Bright Data: {type(error).__name__}.", ""]
            lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return OUT.read_text(encoding="utf-8")


if __name__ == "__main__":
    run()
