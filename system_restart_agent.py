"""Sicherer Betriebs-Agent für den KI-SOCIAL-AGENT.

Prüft GitHub-Actions-Zustände und kann ausschließlich fehlgeschlagene,
hart erlaubte Analyse- oder Wartungsworkflows zeitversetzt erneut auslösen.
Publisher, Telegram, Medienerzeugung, Migrationen und kosten- oder
außenwirksame Workflows sind nicht in der Allowlist und daher technisch gesperrt.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "Edirne22/KI-SOCIAL-AGENT")
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
STATUS_PATH = Path("memory/SYSTEM_STATUS.md")
ROADMAP_PATH = Path("memory/AGENT_ROADMAP.md")
RESTART_DELAY_SECONDS = 45

# Nur diese drei Workflows dürfen jemals durch diesen Agenten gestartet werden.
SAFE_RESTART_WORKFLOWS = {
    "quality-agent.yml": "Qualitäts-Agent",
    "analytics-fetch.yml": "Analytics Fetch",
    "viral-analysis.yml": "Viral Analysis",
}

BLOCKED_CATEGORIES = (
    "Publisher: Instagram, Facebook, Reels, Stories und Karussells",
    "Telegram: Morning, Receive und jede Freigabeverarbeitung",
    "Medien: Agnes, Stock-Fotos und Tests mit Medienerzeugung",
    "Migrationen, Deal-Hunter, Preis-Check und andere kosten- oder außenwirksame Workflows",
)


def api_request(method: str, path: str, payload: dict | None = None) -> tuple[int, object]:
    """Führt einen GitHub-API-Aufruf aus, ohne Token oder Header zu protokollieren."""
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN fehlt.")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{API_ROOT}/repos/{REPOSITORY}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")[:300]
        return error.code, {"message": raw}
    except URLError as error:
        return 0, {"message": f"Netzwerkfehler: {error.reason}"}


def assess_latest_run(run: dict | None) -> tuple[str, str]:
    """Erzeugt eine knappe, sichere Bewertung eines letzten Workflow-Laufs."""
    if not run:
        return "NICHT_GEFUNDEN", "Kein Lauf gefunden."
    status = str(run.get("status") or "unbekannt")
    conclusion = str(run.get("conclusion") or "")
    if status in {"queued", "in_progress", "waiting", "pending"}:
        return "AKTIV", f"Status: {status}"
    if conclusion == "success":
        return "OK", "Letzter Lauf erfolgreich."
    if conclusion in {"failure", "timed_out", "cancelled", "action_required"}:
        return "FEHLER", f"Letzter Lauf: {conclusion}."
    return "UNBEKANNT", f"Status: {status}; Ergebnis: {conclusion or "offen"}."


def latest_run(workflow_file: str) -> tuple[str, str, dict | None]:
    status, data = api_request("GET", f"/actions/workflows/{workflow_file}/runs?per_page=1")
    if status != 200 or not isinstance(data, dict):
        return "API_WARNUNG", f"GitHub API HTTP {status}.", None
    runs = data.get("workflow_runs", [])
    run = runs[0] if isinstance(runs, list) and runs else None
    state, detail = assess_latest_run(run if isinstance(run, dict) else None)
    return state, detail, run if isinstance(run, dict) else None


def dispatch_safe_workflow(workflow_file: str) -> tuple[bool, str]:
    status, data = api_request("POST", f"/actions/workflows/{workflow_file}/dispatches", {"ref": "main"})
    if 200 <= status < 300:
        return True, "Neustart angefordert."
    detail = data.get("message", "unbekannter Fehler") if isinstance(data, dict) else "unbekannter Fehler"
    return False, f"Neustart nicht möglich (HTTP {status}): {detail[:180]}"


def write_roadmap() -> None:
    ROADMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROADMAP_PATH.write_text(
        "# Agenten-Roadmap\n\n"
        "## Nächster Betriebs-Schritt\n"
        "- Nach einem vollständigen Tageslauf den Systemstatus prüfen und Warnungen einzeln bewerten.\n"
        "- Publisher werden niemals durch den System-Neustart-Agenten gestartet.\n\n"
        "## Spätere Vorschläge\n"
        "- TikTok erst nach separater API-, Rechte- und Testfreigabe anbinden.\n"
        "- Reise-Agent bleibt privat und vom Social-Repo getrennt.\n"
        "- Neue Plattformen, Budgets oder externe Benachrichtigungen immer einzeln freigeben.\n",
        encoding="utf-8",
    )


def run(allow_safe_restart: bool = False) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Systemstatus",
        f"Stand: {timestamp}",
        "",
        "## Sichere Workflow-Prüfung",
    ]
    restart_count = 0
    for workflow_file, label in SAFE_RESTART_WORKFLOWS.items():
        state, detail, run = latest_run(workflow_file)
        run_url = str(run.get("html_url") or "") if run else ""
        lines.append(f"- {label}: {state} – {detail}")
        if run_url:
            lines.append(f"  - Lauf: {run_url}")
        if allow_safe_restart and state == "FEHLER":
            if restart_count:
                time.sleep(RESTART_DELAY_SECONDS)
            ok, restart_detail = dispatch_safe_workflow(workflow_file)
            lines.append(f"  - Neustart: {restart_detail}")
            restart_count += 1

    lines += ["", "## Technisch gesperrt"]
    lines.extend(f"- {category}" for category in BLOCKED_CATEGORIES)
    lines += [
        "",
        "## Modus",
        f"- {"Freigegebene Fehler-Neustarts aktiv" if allow_safe_restart else "Nur Bericht; keine Neustarts ausgelöst"}.",
        "- Es werden keine Beiträge veröffentlicht, keine Telegram-Nachrichten verarbeitet und keine Medien erzeugt.",
    ]
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_roadmap()
    return STATUS_PATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-safe-restart", choices=("true", "false"), default="false")
    args = parser.parse_args()
    print(f"Systemstatus gespeichert: {run(args.allow_safe_restart == "true")}")