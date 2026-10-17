"""Owner-only Telegram -> fixed OpenMontage Actions workflow. No media or keys in state."""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
import requests

REPO = "Edirne22/KI-SOCIAL-AGENT"
WORKFLOW = "openmontage.yml"
API = f"https://api.github.com/repos/{REPO}"
URL = f"https://github.com/{REPO}/actions/workflows/{WORKFLOW}"
STATE = Path("memory/OPENMONTAGE_REQUESTS.json")
HELP = (
    "OpenMontage\n"
    "/montage diagnose – Installation und vorhandene Key-Namen prüfen; keine API-Aufrufe\n"
    "/montage test – Testbeschreibung, startet nichts\n"
    "/montage test starten – ausdrücklich eine synthetische Remotion-Demo ohne Keys rendern\n"
    "/montage status – letzte GitHub-Läufe und Downloadlinks\n"
    "/montage link neu <Video-ID> – privaten Download-Link für 24 Stunden erneuern\\n"
    "FAQ: https://github.com/Edirne22/KI-SOCIAL-AGENT/blob/main/docs/OPENMONTAGE_FAQ.md\n"
    "Freie Filmaufträge brauchen weiterhin einen Coding-Agenten. Kein Social-Publishing."
)


def is_command(text):
    return bool(re.match(r"^/montage(?:@[A-Za-z0-9_]+)?(?:\s|$)", text.strip(), re.I))


def parse_command(text):
    if not is_command(text):
        return None
    args = " ".join(text.strip().split()[1:]).lower()
    if args == "link neu":
        return "renew_missing"
    match = re.fullmatch(r"link neu ([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", args)
    if match:
        return "renew:" + match.group(1)
    return {"": "help", "hilfe": "help", "help": "help", "diagnose": "diagnose",
            "test": "proposal", "test starten": "demo", "status": "status"}.get(args, "invalid")


def headers(token):
    if not token:
        raise ValueError("GITHUB_TOKEN fehlt; Workflow-Zugriff nicht möglich.")
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def recent_runs(token, get=None):
    get = get or requests.get
    try:
        r = get(f"{API}/actions/workflows/{WORKFLOW}/runs", headers=headers(token),
                params={"per_page": 5, "branch": "main", "event": "workflow_dispatch"}, timeout=20)
        if r.status_code != 200:
            return f"OpenMontage-Status nicht abrufbar (HTTP {r.status_code}). {URL}"
        runs = r.json().get("workflow_runs", [])
        if not runs:
            return f"Noch kein OpenMontage-Lauf gefunden. {URL}"
        lines = ["OpenMontage – tatsächlicher GitHub-Status:"]
        for run in runs:
            rid = int(run["id"])
            lines.append(f"#{rid}: {run.get('conclusion') or run.get('status')}\n"
                         f"https://github.com/{REPO}/actions/runs/{rid}")
        return "\n".join(lines)
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return f"Statusabfrage fehlgeschlagen; keine Zugangsdaten ausgegeben. {URL}"


def handle(text, update_id, chat, authorized_chat, *, state=None, post=None, get=None):
    if not authorized_chat or str(chat) != str(authorized_chat):
        raise PermissionError("OpenMontage ist nur im freigegebenen Chat verfügbar.")
    action = parse_command(text)
    if action is None:
        return None
    if action in ("help", "invalid"):
        return HELP
    if action == "renew_missing":
        return "Bitte Video-ID angeben: /montage link neu <Video-ID>"
    if action == "proposal":
        return ("Testvorschlag: die mitgelieferte OpenMontage-Demo 'code-to-screen' "
                "mit animierten Texten und Diagrammen. Ohne Stimme, Archivmaterial, Musik "
                "oder API-Keys. Das ist ein Techniktest, nicht der vorgeschlagene NASA-Film. "
                "Start nur mit /montage test starten.")
    token = os.environ.get("GITHUB_TOKEN", "")
    if action == "status":
        return recent_runs(token, get)
    if type(update_id) is not int or update_id < 0:
        raise ValueError("Ungültige Telegram-Update-ID.")
    auth = headers(token)
    if action.startswith("renew:"):
        media_id = action.partition(":")[2]
        workflow = "openmontage-renew-link.yml"
        inputs = {"media_id": media_id}
    else:
        workflow = WORKFLOW
        inputs = {"mode": action, "request_id": f"tg-{update_id}"}
    state = Path(state) if state is not None else STATE
    ledger = json.loads(state.read_text()) if state.exists() else {}
    request_id = f"tg-{update_id}"
    if request_id in ledger:
        return f"Auftrag {request_id} bereits erfasst ({ledger[request_id]}). /montage status"
    state.parent.mkdir(parents=True, exist_ok=True)

    def save(value):
        ledger[request_id] = value
        temp = state.with_suffix(".tmp")
        temp.write_text(json.dumps(ledger, sort_keys=True) + "\n")
        temp.replace(state)

    # Persist intent before dispatch. A timeout must never silently trigger a retry.
    save("dispatching")
    try:
        r = (post or requests.post)(f"{API}/actions/workflows/{workflow}/dispatches",
                                   headers=auth, json={"ref": "main", "inputs": {
                                       "mode": action, "request_id": request_id}}, timeout=20)
    except requests.RequestException:
        save("uncertain")
        return (f"Auftrag {request_id}: GitHub-Antwort ausgeblieben; Annahme unklar. "
                "Kein automatischer Neustart. /montage status")
    if r.status_code != 204:
        save(f"rejected-http-{r.status_code}")
        return f"OpenMontage-Start abgelehnt (HTTP {r.status_code}). Workflow auf main und actions:write prüfen."
    save("accepted")
    return f"GitHub hat {request_id} angenommen. Das ist noch kein fertiger Film. /montage status\n{URL}"


def claim_request(request_id, token, sha, post=None):
    """Atomic durable claim across runner retries/crashes; no secret in the Git ref."""
    if not re.fullmatch(r"(?:tg|manual)-[0-9]{1,20}", request_id):
        raise ValueError("Ungültige Auftrags-ID.")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Ungültiger Commit.")
    try:
        r = (post or requests.post)(f"{API}/git/refs", headers=headers(token),
                                   json={"ref": f"refs/tags/openmontage-requests/{request_id}",
                                         "sha": sha}, timeout=20)
    except requests.RequestException:
        raise RuntimeError("GitHub-Auftragsreservierung unklar; kein Renderstart.") from None
    if r.status_code == 201:
        return True
    if r.status_code == 422:
        # Includes existing claim or invalid ref; fail closed in either case.
        return False
    raise RuntimeError(f"GitHub-Auftragsreservierung fehlgeschlagen (HTTP {r.status_code}).")
