"""Robuster Bright-Data-Adapter: konfigurierbare Inputs, Diagnose und opt-in Web Unlocker."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests

OUT = Path("memory/INSPIRATION_BRIGHTDATA.md")
DEBUG = Path("memory/BRIGHTDATA_DEBUG.md")
DATASET_TRIGGER = "https://api.brightdata.com/datasets/v3/trigger"
DATASET_API = "https://api.brightdata.com/datasets/v3"
UNLOCKER = "https://api.brightdata.com/request"
PLATFORMS = ("instagram", "facebook", "youtube")


def _redact(value: str, token: str) -> str:
    return (value or "").replace(token, "[REDACTED]")[:500]


def _write_debug(endpoint: str, status: str, response: str, token: str, details: dict | None = None) -> None:
    DEBUG.parent.mkdir(parents=True, exist_ok=True)
    old = DEBUG.read_text(encoding="utf-8") if DEBUG.exists() else "# Bright Data Debug\n"
    lines = [
        f"\n## {datetime.now():%Y-%m-%d %H:%M}",
        f"- Endpunkt: {endpoint}",
        f"- HTTP-Status: {status}",
        f"- Antwort (max. 500 Zeichen): {_redact(response, token)}",
    ]
    if details:
        for key, value in details.items():
            lines.append(f"- {key}: {value}")
    DEBUG.write_text(old.rstrip() + "\n".join(lines) + "\n", encoding="utf-8")


def _env_dataset(platform: str) -> str | None:
    return os.environ.get(f"BRIGHTDATA_DATASET_{platform.upper()}") or None


def _env_input(platform: str) -> list | None:
    raw = os.environ.get(f"BRIGHTDATA_INPUT_{platform.upper()}")
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None


def _error_codes(payload) -> list[str]:
    if not isinstance(payload, dict):
        return []
    found: list[str] = []
    for key in ("error_codes", "errors"):
        value = payload.get(key)
        if isinstance(value, dict):
            found.extend(f"{name}={count}" for name, count in value.items() if count)
        elif isinstance(value, list):
            found.extend(str(item) for item in value)
        elif value:
            found.append(str(value))
    if payload.get("dead_page"):
        found.append(f"dead_page={payload['dead_page']}")
    return sorted(set(found))


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
    lines = [f"## {platform.title()}"]
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


def _snapshot(snapshot_id: str, headers: dict, token: str) -> tuple[list[dict], dict]:
    details = {"Snapshot-ID": snapshot_id, "Snapshot-Status": "nicht bereit", "Records": 0, "Errors": 0, "Error-Codes": "{}"}
    for _ in range(6):
        endpoint = f"{DATASET_API}/progress/{snapshot_id}"
        response = requests.get(endpoint, headers=headers, timeout=30)
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = {}
        codes = _error_codes(payload)
        details.update({"Snapshot-Status": payload.get("status", "unbekannt"), "Errors": len(codes), "Error-Codes": ", ".join(codes) or "{}"})
        _write_debug(endpoint, str(response.status_code), response.text, token, details)
        if response.status_code == 200 and payload.get("status") == "ready":
            endpoint = f"{DATASET_API}/snapshot/{snapshot_id}"
            result = requests.get(endpoint, headers=headers, params={"format": "json"}, timeout=60)
            try:
                data = result.json()
            except json.JSONDecodeError:
                data = {}
            records = _records(data)
            codes = sorted(set(codes + _error_codes(data)))
            details.update({"Snapshot-Status": "ready", "Records": len(records), "Errors": len(codes), "Error-Codes": ", ".join(codes) or "{}"})
            _write_debug(endpoint, str(result.status_code), result.text, token, details)
            if result.status_code != 200:
                details.update({"Errors": 1, "Error-Codes": f"HTTP {result.status_code}"})
            return records, details
        time.sleep(5)
    return [], details


def _diagnosis(platform: str, dataset: str | None, input_valid: bool, http_status: str, details: dict) -> list[str]:
    codes = str(details.get("Error-Codes", "{}"))
    errors = int(details.get("Errors", 0))
    records = int(details.get("Records", 0))
    if errors or codes != "{}":
        verdict = f"Konfigurationsproblem: {codes}. Input-URL/Format prüfen."
    elif records == 0 and http_status in {"200", "201", "202"} and details.get("Snapshot-Status") in {"ready", "nicht bereit"}:
        verdict = "Valides leeres Ergebnis: Suche ergab keine Treffer."
    else:
        verdict = "Daten erhalten." if records else "Abruf nicht bestätigt – Debug-Log prüfen."
    return [
        f"## Diagnose {platform.title()}",
        f"- Dataset-ID: {dataset or 'fehlt'}",
        f"- Input-JSON gültig: {'ja' if input_valid else 'nein'}",
        f"- HTTP-Status: {http_status}",
        f"- Snapshot-Status: {details.get('Snapshot-Status', 'nicht verfügbar')}",
        f"- Records: {records}",
        f"- Errors: {errors}",
        f"- Error-Codes: {codes}",
        f"- Bewertung: {verdict}",
    ]


def _run_dataset(platform: str, dataset: str, input_data: list, headers: dict, token: str) -> tuple[list[dict], str, dict]:
    endpoint = f"{DATASET_TRIGGER}?dataset_id={dataset}"
    response = requests.post(endpoint, headers=headers, json=input_data, timeout=90)
    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = {}
    details = {"Snapshot-ID": "nicht verfügbar", "Snapshot-Status": "nicht verfügbar", "Records": 0, "Errors": 0, "Error-Codes": "{}"}
    codes = _error_codes(payload)
    details.update({"Errors": len(codes), "Error-Codes": ", ".join(codes) or "{}"})
    _write_debug(endpoint, str(response.status_code), response.text, token, details)
    if response.status_code not in (200, 201, 202):
        return [], str(response.status_code), details
    direct = _records(payload)
    if direct:
        details.update({"Snapshot-Status": "direkte Antwort", "Records": len(direct)})
        return direct, str(response.status_code), details
    snapshot_id = payload.get("snapshot_id") or payload.get("id") if isinstance(payload, dict) else None
    if snapshot_id:
        records, snapshot_details = _snapshot(str(snapshot_id), headers, token)
        return records, str(response.status_code), snapshot_details
    return [], str(response.status_code), details


def _unlocker_test(zone: str, headers: dict, token: str) -> str:
    target = "https://www.google.com/search?q=" + quote_plus("MotoGP News heute")
    response = requests.post(UNLOCKER, headers=headers, json={"zone": zone, "url": target, "format": "raw", "method": "GET"}, timeout=90)
    _write_debug(UNLOCKER, str(response.status_code), response.text, token, {"Web Unlocker": "eine Anfrage"})
    return "HTML erhalten" if response.status_code == 200 and response.text.strip() else f"HTTP {response.status_code}"


def run() -> str:
    token = os.environ.get("BRIGHTDATA_API_TOKEN")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}
    lines = ["# Inspiration · Bright Data", ""]
    if not token:
        lines.append("Bright Data: BRIGHTDATA_API_TOKEN fehlt.")
    else:
        any_records = False
        for platform in PLATFORMS:
            dataset, input_data = _env_dataset(platform), _env_input(platform)
            if not dataset:
                lines += [f"## Diagnose {platform.title()}", "Bright Data: Keine Dataset-ID – übersprungen.", ""]
                continue
            if input_data is None:
                lines += _diagnosis(platform, dataset, False, "nicht aufgerufen", {"Snapshot-Status": "nicht aufgerufen", "Records": 0, "Errors": 1, "Error-Codes": "ungültiges oder fehlendes Input-JSON"})
                lines.append("")
                continue
            try:
                records, status, details = _run_dataset(platform, dataset, input_data, headers, token)
                lines.extend(_format_records(platform, records))
                lines.extend(_diagnosis(platform, dataset, True, status, details))
                lines.append("")
                any_records = any_records or bool(records)
            except requests.Timeout:
                lines += _diagnosis(platform, dataset, True, "Timeout", {"Snapshot-Status": "Timeout", "Records": 0, "Errors": 1, "Error-Codes": "Timeout"})
                lines.append("")
            except requests.RequestException as error:
                lines += _diagnosis(platform, dataset, True, "Netzwerkfehler", {"Snapshot-Status": "nicht verfügbar", "Records": 0, "Errors": 1, "Error-Codes": type(error).__name__})
                lines.append("")

        enabled = os.environ.get("BRIGHTDATA_ENABLE_UNLOCKER_FALLBACK", "false").strip().lower() == "true"
        zone = os.environ.get("BRIGHTDATA_ZONE")
        if enabled and not any_records:
            if zone:
                try:
                    lines += ["## Web Unlocker-Test", "Web Unlocker Fallback aktiviert – eine Anfrage.", f"Ergebnis: {_unlocker_test(zone, headers, token)}."]
                except requests.Timeout:
                    lines += ["## Web Unlocker-Test", "Web Unlocker Fallback aktiviert – Timeout."]
                except requests.RequestException as error:
                    lines += ["## Web Unlocker-Test", f"Web Unlocker Fallback aktiviert – Fehler: {type(error).__name__}."]
            else:
                lines += ["## Web Unlocker-Test", "Zone fehlt – Unlocker übersprungen."]
        elif not enabled:
            lines += ["## Web Unlocker-Test", "Deaktiviert: BRIGHTDATA_ENABLE_UNLOCKER_FALLBACK=false."]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return OUT.read_text(encoding="utf-8")


if __name__ == "__main__":
    run()
