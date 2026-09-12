"""Bright-Data-Scraper-Adapter für fünf öffentliche Inspirationsquellen.

Facebook, YouTube und TikTok werden über die von Bright Data gelieferte
Snapshot-ID abgeholt, aber ausschließlich nach einer HTTP-202-Antwort.
Instagram und X werden direkt ausgewertet.
"""
from __future__ import annotations

import copy
import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import requests

OUT = Path("memory/INSPIRATION_BRIGHTDATA.md")
DEBUG = Path("memory/BRIGHTDATA_DEBUG.md")
ALERT_STATE = Path("memory/BRIGHTDATA_ALERT_STATE.md")
API_ROOT = "https://api.brightdata.com/datasets/v3/scrape"
SNAPSHOT_ROOT = "https://api.brightdata.com/datasets/v3"
TZ = ZoneInfo("Europe/Berlin")
RETRY_DELAYS = (30, 60, 120)
ASYNC_SETTINGS = {
    "facebook": (180, 10),
    "youtube": (180, 10),
    "tiktok": (300, 15),
    "instagram": (300, 10),
}

PLATFORMS = {
    "instagram": {
        "label": "Instagram", "dataset": "gd_lk5ns7kz21pck8jpis",
        "endpoint": f"{API_ROOT}?dataset_id=gd_lk5ns7kz21pck8jpis&notify=false&include_errors=true&type=discover_new&discover_by=url",
        "date_format": "%m-%d-%Y", "text": ("description",), "date": ("date_posted",), "url": ("url",),
        "engagement": (("Likes", ("likes",)), ("Kommentare", ("num_comments",))),
    },
    "facebook": {
        "label": "Facebook", "dataset": "gd_lkaxegm826bjpoo9m5",
        "endpoint": f"{API_ROOT}?dataset_id=gd_lkaxegm826bjpoo9m5&notify=false&include_errors=true",
        "date_format": "%m-%d-%Y", "text": ("content",), "date": ("date_posted",), "url": ("url",),
        "engagement": (("Likes", ("num_likes_type",)), ("Kommentare", ("num_comments",)), ("Shares", ("num_shares",))),
    },
    "youtube": {
        "label": "YouTube", "dataset": "gd_lk56epmy2i5g7lzu0k",
        "endpoint": f"{API_ROOT}?dataset_id=gd_lk56epmy2i5g7lzu0k&notify=false&include_errors=true&type=discover_new&discover_by=keyword",
        "date_format": "%m-%d-%Y", "text": ("title",), "date": ("date_posted",), "url": ("url",),
        "engagement": (("Likes", ("likes",)), ("Kommentare", ("num_comments",)), ("Views", ("view_count",))),
    },
    "tiktok": {
        "label": "TikTok", "dataset": "gd_m7n5ixlw1gc4no56kx",
        "endpoint": f"{API_ROOT}?dataset_id=gd_m7n5ixlw1gc4no56kx&notify=false&include_errors=true",
        "date_format": None, "text": ("description",), "date": ("date_posted", "create_time"), "url": ("url",),
        "engagement": (("Likes", ("likes", "digg_count")), ("Kommentare", ("num_comments", "comment_count")), ("Shares", ("share_count",)), ("Views", ("play_count",))),
    },
    "x": {
        "label": "X", "dataset": "gd_lwxkxvnf1cynvib9co",
        "endpoint": f"{API_ROOT}?dataset_id=gd_lwxkxvnf1cynvib9co&notify=false&include_errors=true&type=discover_new&discover_by=profile_url",
        "date_format": "%Y-%m-%d", "text": ("description", "text"), "date": ("date_posted",), "url": ("url",),
        "engagement": (("Likes", ("likes",)), ("Antworten", ("replies",)), ("Reposts", ("reposts", "retweets")), ("Views", ("views",))),
    },
}


def _dates() -> tuple[date, date]:
    yesterday = datetime.now(TZ).date() - timedelta(days=1)
    return yesterday - timedelta(days=6), yesterday


def _redact(value: str, token: str) -> str:
    return (value or "").replace(token or "", "[REDACTED]")[:500]


def _debug(platform: str, endpoint: str, status: str, records: int, error: str, response: str, token: str, extra: dict | None = None, first_url: str = "") -> None:
    """Schreibt einen begrenzten, von Zugangsdaten freien Plattform-Eintrag."""
    DEBUG.parent.mkdir(parents=True, exist_ok=True)
    old = DEBUG.read_text(encoding="utf-8") if DEBUG.exists() else "# Bright Data Debug\n"
    lines = [
        f"\n## Diagnose {PLATFORMS[platform]['label']} ({datetime.now(TZ):%Y-%m-%d %H:%M})",
        f"- Endpoint: {endpoint}",
        f"- HTTP-Status: {status}",
        f"- Records: {records}",
        f"- Fehler: {error or 'keine'}",
    ]
    if extra:
        for key, value in extra.items():
            lines.append(f"- {key}: {value}")
    if first_url:
        lines.append(f"- Erste URL: {first_url}")
    lines.append(f"- Antwort (max. 500 Zeichen): {_redact(response, token)}")
    entry = "\n".join(lines)
    DEBUG.write_text(old.rstrip() + "\n" + entry[:2000] + "\n", encoding="utf-8")


def _value(record: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", [], {}):
            return json.dumps(value, ensure_ascii=False)[:300] if isinstance(value, (dict, list)) else str(value)
    return "nicht verfügbar"


def _records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "records", "items", "output"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if any(key in payload for key in ("id", "url", "description", "text", "title")):
            return [payload]
    return []


def _ndjson_records(text: str) -> list[dict]:
    """Liest zeilengetrennte JSON-Antworten und überspringt reine Fehlerzeilen."""
    records: list[dict] = []
    data_fields = ("id", "description", "content", "title", "text", "date_posted", "create_time")
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidates = _records(item)
        for candidate in candidates:
            has_data = any(candidate.get(field) not in (None, "") for field in data_fields)
            only_error = ("error" in candidate or "error_code" in candidate) and not has_data
            if has_data and not only_error:
                records.append(candidate)
    return records


def _error_text(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    values: list[str] = []
    for key in ("error", "errors", "error_codes", "dead_page"):
        value = payload.get(key)
        if value in (None, "", [], {}, 0):
            continue
        if isinstance(value, dict):
            values.extend(f"{name}={count}" for name, count in value.items() if count)
        elif isinstance(value, list):
            values.extend(str(item) for item in value[:5])
        else:
            values.append(str(value))
    return ", ".join(dict.fromkeys(values))[:500]


def _load_inputs(platform: str) -> tuple[list[dict] | None, str]:
    raw = os.environ.get(f"BRIGHTDATA_INPUT_{platform.upper()}")
    if not raw:
        return None, "nicht konfiguriert"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, "ungültiges Input-JSON"
    if not isinstance(parsed, list) or not all(isinstance(item, dict) for item in parsed):
        return None, "Input muss eine JSON-Liste mit Objekten sein"
    if any("google_query" in item for item in parsed):
        return None, "Altes SERP-Input-Format erkannt – bitte neue Input-Liste eintragen"
    return copy.deepcopy(parsed), ""


def _prepare_inputs(platform: str, inputs: list[dict]) -> tuple[list[dict] | None, str]:
    start, end = _dates()
    prepared: list[dict] = []
    for item in inputs:
        value = dict(item)
        if platform == "tiktok":
            keyword = str(value.pop("keyword", "")).strip()
            if not keyword:
                return None, "TikTok-Input benötigt keyword"
            value["url"] = f"https://www.tiktok.com/search?lang=en&q={quote_plus(keyword)}&t={int(time.time() * 1000)}"
        else:
            required = "keyword" if platform == "youtube" else "url"
            if not str(value.get(required, "")).strip():
                return None, f"Input benötigt {required}"
            value["start_date"] = start.strftime(PLATFORMS[platform]["date_format"])
            value["end_date"] = end.strftime(PLATFORMS[platform]["date_format"])
        prepared.append(value)
    return prepared, ""


def _retry_after(response: requests.Response, delay: int) -> int:
    try:
        return max(delay, int(response.headers.get("Retry-After", "0")))
    except ValueError:
        return delay


def _post_with_retry(endpoint: str, headers: dict, payload: dict) -> tuple[requests.Response | None, str]:
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
        except requests.Timeout:
            if attempt == len(RETRY_DELAYS):
                return None, "Timeout"
            time.sleep(RETRY_DELAYS[attempt])
            continue
        except requests.RequestException as error:
            return None, type(error).__name__
        if response.status_code == 429 and attempt < len(RETRY_DELAYS):
            time.sleep(_retry_after(response, RETRY_DELAYS[attempt]))
            continue
        if 500 <= response.status_code <= 599 and attempt < len(RETRY_DELAYS):
            time.sleep(RETRY_DELAYS[attempt])
            continue
        return response, ""
    return None, "unbekannter Netzwerkfehler"


def _poll_snapshot(snapshot_id: str, headers: dict, timeout_seconds: int, interval_seconds: int) -> tuple[list[dict], str, dict, str]:
    """Pollt einen bestätigten Async-Snapshot mit plattformspezifischem Zeitfenster."""
    started = time.monotonic()
    attempts = 0
    progress_endpoint = f"{SNAPSHOT_ROOT}/progress/{snapshot_id}"
    last_status = "unbekannt"
    last_response = ""
    while time.monotonic() - started <= timeout_seconds:
        attempts += 1
        try:
            progress = requests.get(progress_endpoint, headers=headers, timeout=30)
        except requests.Timeout:
            last_status = "Timeout"
            time.sleep(interval_seconds)
            continue
        except requests.RequestException as error:
            details = {"Snapshot-ID": snapshot_id, "Polling-Versuche": attempts, "Letzter Status": type(error).__name__, "Wartezeit": f"{int(time.monotonic() - started)} Sekunden"}
            return [], type(error).__name__, details, last_response
        last_response = progress.text
        try:
            payload = progress.json()
        except ValueError:
            payload = {}
        last_status = str(payload.get("status", "unbekannt"))
        details = {"Snapshot-ID": snapshot_id, "Polling-Versuche": attempts, "Letzter Status": last_status, "Wartezeit": f"{int(time.monotonic() - started)} Sekunden"}
        if progress.status_code != 200:
            return [], f"Polling HTTP {progress.status_code}", details, last_response
        if last_status == "failed":
            return [], _error_text(payload) or "Snapshot fehlgeschlagen", details, last_response
        if last_status == "ready":
            snapshot_endpoint = f"{SNAPSHOT_ROOT}/snapshot/{snapshot_id}"
            try:
                snapshot = requests.get(snapshot_endpoint, headers=headers, timeout=60)
            except requests.RequestException as error:
                return [], type(error).__name__, details, last_response
            last_response = snapshot.text
            try:
                data = snapshot.json()
            except ValueError:
                data = {}
            records = _records(data)
            if not records:
                records = _ndjson_records(last_response)
            error = _error_text(data)
            if snapshot.status_code != 200:
                error = error or f"Snapshot HTTP {snapshot.status_code}"
            return records, error, details, last_response
        time.sleep(interval_seconds)
    details = {"Snapshot-ID": snapshot_id, "Polling-Versuche": attempts, "Letzter Status": last_status, "Wartezeit": f"{timeout_seconds} Sekunden"}
    return [], f"Snapshot-Timeout nach {timeout_seconds // 60} Minuten", details, last_response


def _parse_posted_date(value: str) -> date | None:
    clean = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(clean).date()
    except ValueError:
        try:
            return date.fromisoformat(clean[:10])
        except ValueError:
            return None


def _filter_tiktok(records: list[dict]) -> tuple[list[dict], str]:
    start, end = _dates()
    dated = [_parse_posted_date(str(record.get("date_posted", ""))) for record in records]
    if any(value is None for value in dated):
        return records, "Zeitfilter für TikTok nicht verfügbar – zeige aktuelle Suchergebnisse."
    return [record for record, posted in zip(records, dated) if start <= posted <= end], ""


def _format_records(platform: str, records: list[dict], note: str = "") -> list[str]:
    config = PLATFORMS[platform]
    lines = [f"## {config['label']}"]
    if note:
        lines.append(f"- Hinweis: {note}")
    for index, record in enumerate(records, 1):
        lines += [f"### Datensatz {index}", f"- Titel: {_value(record, config['text'])[:500]}", f"- Datum: {_value(record, config['date'])}", f"- URL: {_value(record, config['url'])}"]
        lines.extend(f"- {label}: {_value(record, keys)}" for label, keys in config["engagement"])
    return lines


def _send_token_alert_once(status: int) -> None:
    signature = f"{datetime.now(TZ).date().isoformat()}|{status}"
    previous = ALERT_STATE.read_text(encoding="utf-8") if ALERT_STATE.exists() else ""
    if signature in previous:
        return
    ALERT_STATE.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE.write_text(signature + "\n", encoding="utf-8")
    try:
        from telegram_bot import send_message
        send_message(f"Bright Data: HTTP {status}. Bitte API-Token bzw. Zugriffsrechte prüfen.")
    except Exception:
        pass


def _input_hint(platform: str, error: str) -> str:
    if platform == "instagram" and error.startswith("HTTP 400"):
        return "Instagram: Input-URL ungültig. Nur Profil-URLs erlaubt, z. B. https://www.instagram.com/motogp/; keine Hashtag-URL wie /explore/tags/."
    if platform == "x" and "dead_page" in error:
        return "X: Profil nicht gefunden oder keine Posts im Zeitraum. Username, Privatsphäre und Sperrung prüfen."
    return error


def _run_platform(platform: str, token: str) -> tuple[list[dict], str, str, str]:
    inputs, input_error = _load_inputs(platform)
    if inputs is None:
        return [], "nicht konfiguriert", input_error, ""
    prepared, prepare_error = _prepare_inputs(platform, inputs)
    if prepared is None:
        return [], "nicht aufgerufen", prepare_error, ""
    endpoint = PLATFORMS[platform]["endpoint"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response, request_error = _post_with_retry(endpoint, headers, {"input": prepared, "limit_per_input": None})
    if response is None:
        _debug(platform, endpoint, request_error, 0, request_error, "", token)
        return [], request_error, request_error, ""

    try:
        payload = response.json()
    except ValueError:
        payload = {}
    records = _records(payload)
    if platform == "x" and not records:
        records = _ndjson_records(response.text)
    error = _error_text(payload)
    extra: dict = {"Body-Länge": f"{len(response.text)} Zeichen"}
    response_text = response.text
    status = str(response.status_code)

    if response.status_code in (401, 403):
        _send_token_alert_once(response.status_code)
    if response.status_code == 202 and platform in ASYNC_SETTINGS:
        snapshot_id = (payload.get("snapshot_id") or payload.get("id")) if isinstance(payload, dict) else None
        if not snapshot_id:
            error = error or "HTTP 202 ohne Snapshot-ID"
        else:
            timeout_seconds, interval_seconds = ASYNC_SETTINGS[platform]
            records, poll_error, poll_details, response_text = _poll_snapshot(str(snapshot_id), headers, timeout_seconds, interval_seconds)
            extra.update(poll_details)
            error = poll_error
            status = "202 (asynchron)"
    elif response.status_code == 202:
        error = error or "Unerwartetes asynchrones Ergebnis für synchronen Scraper"
    elif response.status_code != 200:
        error = error or f"HTTP {response.status_code}"
    elif platform == "youtube" and not response.text.strip():
        error = "Leere Antwort – Plattform nicht verfügbar"
    elif isinstance(payload, dict) and (payload.get("snapshot_id") or payload.get("id")) and not records:
        error = "Synchroner Aufruf lieferte nur eine Snapshot-ID – Endpoint laut Dashboard-Beispiel prüfen. Kein automatisches Polling."

    if platform == "tiktok" and response.status_code in (200, 202) and not error:
        records, note = _filter_tiktok(records)
    else:
        note = ""
    error = _input_hint(platform, error)
    first_url = _value(records[0], PLATFORMS[platform]["url"]) if records else ""
    _debug(platform, endpoint, status, len(records), error, response_text, token, extra, first_url)
    return records, status, error, note


def run() -> str:
    token = os.environ.get("BRIGHTDATA_API_TOKEN")
    lines = ["# Inspiration · Bright Data", ""]
    if not token:
        lines.append("Bright Data: BRIGHTDATA_API_TOKEN fehlt.")
    else:
        statuses: list[str] = []
        for platform, config in PLATFORMS.items():
            records, status, error, note = _run_platform(platform, token)
            if status == "nicht konfiguriert":
                lines += [f"## {config['label']}", f"- Status: nicht konfiguriert ({error})", ""]
                statuses.append(f"- {config['label']}: nicht konfiguriert")
                continue
            lines.extend(_format_records(platform, records, note))
            if error:
                lines.append(f"- Status: nicht verfügbar ({error})")
                statuses.append(f"- {config['label']}: nicht verfügbar ({status})")
            elif not records:
                message = "Keine Daten im Zeitraum." if platform != "tiktok" else (note or "Keine aktuellen Treffer.")
                lines.append(f"- Status: {message}")
                statuses.append(f"- {config['label']}: 0 Records")
            else:
                lines.append(f"- Status: {len(records)} Records verfügbar")
                statuses.append(f"- {config['label']}: {len(records)} Records verfügbar")
            lines.append("")
        lines += ["## Quellen", *statuses]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return OUT.read_text(encoding="utf-8")


if __name__ == "__main__":
    run()
