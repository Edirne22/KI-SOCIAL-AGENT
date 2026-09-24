"""Einmaliger, read-only Instagram Graph API Endpoint-Check."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

API_VERSION = os.environ.get("INSTAGRAM_GRAPH_API_VERSION", "v23.0")
API_BASE = f"https://graph.instagram.com/{API_VERSION}"
SUMMARY = Path(os.environ.get("GITHUB_STEP_SUMMARY", "instagram-api-test-summary.md"))

ENDPOINTS = [
    ("Basis", "", {"fields": "id,username"}),
    ("Media", "/media", {"fields": "id,caption,comments_count", "limit": "5"}),
    ("Tags", "/tags", {"fields": "id,caption,media_url", "limit": "5"}),
    ("Mentions", "/mentions", {"fields": "id,caption,media_url", "limit": "5"}),
    ("Stories", "/stories", {"fields": "id,media_type,media_url"}),
]


def safe_error(response: requests.Response) -> str:
    try:
        error = response.json().get("error", {})
    except (ValueError, AttributeError):
        return "Nicht-JSON-Fehlerantwort"
    code = error.get("code", "-")
    kind = str(error.get("type", "-")).replace("|", "\\|")
    message = str(error.get("message", "-")).replace("|", "\\|").replace("\n", " ")
    return f"code={code}; type={kind}; message={message}"


def structure(payload: object) -> tuple[int, str]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            keys = sorted({key for item in data if isinstance(item, dict) for key in item})
            return len(data), "data[list]" + (f" keys={','.join(keys)}" if keys else "")
        return 1, "object keys=" + ",".join(sorted(payload.keys()))
    return 0, type(payload).__name__


def main() -> int:
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    if not token:
        print("FEHLER: INSTAGRAM_ACCESS_TOKEN fehlt.", file=sys.stderr)
        return 1
    if not user_id:
        print("FEHLER: INSTAGRAM_USER_ID fehlt.", file=sys.stderr)
        return 1

    headers = {"Authorization": f"Bearer {token}"}
    rows = []
    print(f"Instagram Endpoint-Check ({API_VERSION})")
    for name, suffix, params in ENDPOINTS:
        path = f"/{{IG_USER_ID}}{suffix}" if suffix else "/{IG_USER_ID}"
        url = f"{API_BASE}/{user_id}{suffix}"
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            length = len(response.content)
            if response.ok:
                try:
                    payload = response.json()
                    count, shape = structure(payload)
                except ValueError:
                    count, shape = 0, "kein gültiges JSON"
                detail = f"{count} Ergebnis(se); {shape}; Response-Länge={length} Bytes"
                error = "–"
                available = "ja"
            else:
                detail = f"Response-Länge={length} Bytes"
                error = safe_error(response)
                available = "nein"
            print(f"{name}: {path} -> HTTP {response.status_code}; {available}; {detail}")
            rows.append((path, response.status_code, available, error))
        except requests.RequestException as exc:
            # Absichtlich nur der tokenfreie Pfad; keine Request-URL/Headers ausgeben.
            print(f"{name}: {path} -> REQUEST_ERROR: {type(exc).__name__}")
            rows.append((path, "REQUEST_ERROR", "nein", type(exc).__name__))

    lines = [
        "## Instagram API Endpoint-Test",
        "",
        f"Graph API: {API_VERSION}",
        "",
        "| Endpoint | Status | Verfügbar? | Fehler |",
        "|---|---:|---|---|",
    ]
    lines.extend(f"| `{path}` | {status} | {available} | {error} |" for path, status, available, error in rows)
    lines.append("")
    lines.append("Token wurde ausschließlich als Authorization-Bearer-Header verwendet und nicht ausgegeben.")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
