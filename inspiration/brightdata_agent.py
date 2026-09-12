"""Bright-Data-Adapter mit präzisem, tokenfreiem Debug-Protokoll."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests

from .search_config import BRIGHTDATA_DATASETS

OUT = Path("memory/INSPIRATION_BRIGHTDATA.md")
DEBUG = Path("memory/BRIGHTDATA_DEBUG.md")
API = "https://api.brightdata.com/datasets/v3"
UNLOCKER = "https://api.brightdata.com/request"


def _redact(value: str, token: str) -> str:
    return (value or "").replace(token, "[REDACTED]")[:500]


def _debug(endpoint: str, status: str, response: str, token: str) -> None:
    DEBUG.parent.mkdir(parents=True, exist_ok=True)
    old = DEBUG.read_text(encoding="utf-8") if DEBUG.exists() else "# Bright Data Debug\n"
    entry = (
        f"\n## {datetime.now():%Y-%m-%d %H:%M}\n"
        f"- Endpunkt: {endpoint}\n"
        f"- Status: {status}\n"
        f"- Antwort (max. 500 Zeichen): {_redact(response, token)}\n"
    )
    DEBUG.write_text(old.rstrip() + entry, encoding="utf-8")


def _response_json(response: requests.Response, endpoint: str, token: str):
    _debug(endpoint, str(response.status_code), response.text, token)
    try:
        return response.json()
    except json.JSONDecodeError:
        return None


def _records(payload) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "items", "records"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def _value(record: dict, names: tuple[str, ...]) -> str:
    for name in names:
        value = record.get(name)
        if value not in (None, "", [], {}):
            return str(value)
    return "nicht verfügbar"


def _format_records(platform: str, records: list[dict]) -> list[str]:
    lines = [f"## {platform}"]
    if not records:
        return lines + [f"Keine konkreten Datensätze von {platform} erhalten."]
    lines.append(f"Konkrete Datensätze: {len(records)}")
    for index, record in enumerate(records, start=1):
        lines += [
            f"### Datensatz {index}",
            f"- Titel: {_value(record, ('title', 'caption', 'text', 'description', 'name'))}",
            f"- Datum: {_value(record, ('published_at', 'date', 'timestamp', 'created_at', 'time'))}",
            f"- URL: {_value(record, ('url', 'post_url', 'link', 'permalink', 'video_url'))}",
            f"- Likes: {_value(record, ('likes', 'like_count', 'likes_count'))}",
            f"- Kommentare: {_value(record, ('comments', 'comments_count', 'comment_count'))}",
            f"- Views: {_value(record, ('views', 'view_count', 'plays'))}",
        ]
    return lines


def _download_snapshot(snapshot_id: str, headers: dict, token: str) -> list[dict]:
    for _ in range(6):
        endpoint = f"{API}/progress/{snapshot_id}"
        progress = requests.get(endpoint, headers=headers, timeout=30)
        payload = _response_json(progress, endpoint, token)
        if progress.status_code == 200 and isinstance(payload, dict) and payload.get("status") == "ready":
            endpoint = f"{API}/snapshot/{snapshot_id}"
            result = requests.get(endpoint, headers=headers, params={"format": "json"}, timeout=60)
            return _records(_response_json(result, endpoint, token))
        time.sleep(5)
    return []


def _trigger_dataset(platform: str, dataset: str, headers: dict, token: str) -> tuple[list[dict], str]:
    endpoint = f"{API}/trigger?dataset_id={dataset}"
    response = requests.post(
        endpoint,
        headers=headers,
        json=[{"url": f"https://www.{platform}.com/"}],
        timeout=90,
    )
    payload = _response_json(response, endpoint, token)
    if response.status_code not in (200, 201, 202):
        return [], f"HTTP {response.status_code}"
    direct = _records(payload)
    if direct:
        return direct, "direkte Daten"
    snapshot_id = payload.get("snapshot_id") or payload.get("id") if isinstance(payload, dict) else None
    if snapshot_id:
        records = _download_snapshot(str(snapshot_id), headers, token)
        return records, "Snapshot bereit" if records else "Snapshot noch nicht bereit"
    return [], "Keine Datensätze in der Antwort"


def _unlocker_google_test(zone: str, headers: dict, token: str) -> tuple[bool, str]:
    query = "MotoGP News heute"
    target = "https://www.google.com/search?q=" + quote_plus(query)
    payload = {"zone": zone, "url": target, "format": "raw", "method": "GET"}
    response = requests.post(UNLOCKER, headers=headers, json=payload, timeout=90)
    _debug(UNLOCKER, str(response.status_code), response.text, token)
    if response.status_code != 200:
        return False, f"HTTP {response.status_code}"
    try:
        data = response.json()
        body = str(data.get("body", ""))
        return bool(body), "HTML erhalten" if body else "Leere Antwort"
    except json.JSONDecodeError:
        return bool(response.text.strip()), "HTML erhalten" if response.text.strip() else "Leere Antwort"


def run() -> str:
    token = os.environ.get("BRIGHTDATA_API_TOKEN")
    zone = os.environ.get("BRIGHTDATA_ZONE")
    lines = ["# Inspiration · Bright Data", ""]
    if not token:
        lines.append("Keine Daten von Bright Data: BRIGHTDATA_API_TOKEN fehlt.")
    else:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        any_records = False
        for platform, configured_dataset in BRIGHTDATA_DATASETS.items():
            dataset = os.environ.get(f"BRIGHTDATA_{platform.upper()}_DATASET_ID", configured_dataset)
            if not dataset:
                lines += [f"## {platform}", "Keine Daten von Bright Data: Dataset-ID fehlt.", ""]
                continue
            try:
                records, status = _trigger_dataset(platform, dataset, headers, token)
                lines.extend(_format_records(platform, records))
                lines.append(f"Diagnose: {status}.")
                lines.append("")
                any_records = any_records or bool(records)
            except requests.Timeout:
                lines += [f"## {platform}", "Keine Daten von Bright Data: Timeout.", ""]
            except requests.RequestException as error:
                lines += [f"## {platform}", f"Keine Daten von Bright Data: Netzwerkfehler {type(error).__name__}.", ""]

        if not any_records:
            if zone:
                try:
                    success, status = _unlocker_google_test(zone, headers, token)
                    lines += ["## Web Unlocker-Test", f"Google-Suche „MotoGP News heute“: {status}."]
                    if not success:
                        lines.append("Keine verwertbaren Unlocker-Daten erhalten.")
                except requests.Timeout:
                    lines += ["## Web Unlocker-Test", "Timeout."]
                except requests.RequestException as error:
                    lines += ["## Web Unlocker-Test", f"Netzwerkfehler {type(error).__name__}."]
            else:
                lines += ["## Web Unlocker-Test", "Übersprungen: BRIGHTDATA_ZONE fehlt. Keine Zone wird geraten."]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return OUT.read_text(encoding="utf-8")


if __name__ == "__main__":
    run()
