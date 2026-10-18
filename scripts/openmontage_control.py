"""Owner-only Telegram -> OpenMontage Actions workflow. No media or keys in state."""
from __future__ import annotations
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import requests

REPO = "Edirne22/KI-SOCIAL-AGENT"
WORKFLOW = "openmontage.yml"
API = f"https://api.github.com/repos/{REPO}"
URL = f"https://github.com/{REPO}/actions/workflows/{WORKFLOW}"
STATE = Path("memory/OPENMONTAGE_REQUESTS.json")
JOBS_STATE = Path("memory/OPENMONTAGE_JOBS.json")

HELP = (
    "OpenMontage V3 – Motorsport Video Factory\n"
    "/montage erstellen <Auftrag> – Filmauftrag ausführen (z.B. /montage erstellen MotoGP News, 90 Sek, Deutsch, 9:16)\n"
    "/montage planen <Thema> – Recherche & Storyboard planen\n"
    "/montage status – Aktueller Job- & Build-Status\n"
    "/montage freigeben <Video-ID> – Redaktionelle Videofreigabe (ohne Social Publishing)\n"
    "/montage ablehnen <Video-ID> – Redaktionell ablehnen\n"
    "/montage link neu <Video-ID> – Vorschau-Link erneuern\n"
    "/montage diagnose – Systemdiagnose\n"
    "FAQ: https://github.com/Edirne22/KI-SOCIAL-AGENT/blob/main/docs/OPENMONTAGE_FAQ.md\n"
    "Freie Filmaufträge brauchen weiterhin einen Coding-Agenten. Kein Social-Publishing."
)


def is_command(text: str) -> bool:
    return bool(re.match(r"^/montage(?:@[A-Za-z0-9_]+)?(?:\s|$)", text.strip(), re.I))


def parse_command(text: str) -> Any:
    if not is_command(text):
        return None
    raw = " ".join(text.strip().split()[1:]).strip()
    args_low = raw.lower()

    if not args_low:
        return "help"
    if args_low in ("hilfe", "help", "?"):
        return "help"
    if args_low == "diagnose":
        return "diagnose"
    if args_low == "status":
        return "status"
    if args_low == "test":
        return "proposal"
    if args_low == "test starten":
        return "demo"
    if args_low == "link neu":
        return "renew_missing"

    m_link = re.fullmatch(r"link neu ([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", args_low)
    if m_link:
        return f"renew:{m_link.group(1)}"

    m_free = re.fullmatch(r"freigeben ([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", args_low)
    if m_free:
        return f"approve:{m_free.group(1)}"

    m_reject = re.fullmatch(r"ablehnen ([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})", args_low)
    if m_reject:
        return f"reject:{m_reject.group(1)}"

    if args_low.startswith("erstellen "):
        prompt = raw[10:].strip()
        return {"action": "erstellen", "prompt": prompt}

    if args_low.startswith("planen "):
        topic = raw[7:].strip()
        return {"action": "planen", "prompt": topic}

    return "invalid"


def load_jobs_ledger(path: Optional[Path] = None) -> Dict[str, Any]:
    target = path or JOBS_STATE
    if target.is_file():
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_job_entry(job_id: str, job_data: Dict[str, Any], path: Optional[Path] = None) -> None:
    target = path or JOBS_STATE
    target.parent.mkdir(parents=True, exist_ok=True)
    ledger = load_jobs_ledger(target)
    job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    ledger[job_id] = job_data

    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(target)


def headers(token: str) -> Dict[str, str]:
    if not token:
        raise ValueError("GITHUB_TOKEN fehlt; Workflow-Zugriff nicht möglich.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def recent_runs(token: str, get=None) -> str:
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
    except Exception:
        return f"Statusabfrage fehlgeschlagen; keine Zugangsdaten ausgegeben. {URL}"


def handle(text: str, update_id: int, chat: str, authorized_chat: str, *, state=None, jobs_state=None, post=None, get=None, request_storage=None, feedback_storage=None) -> str:
    if not authorized_chat or str(chat) != str(authorized_chat):
        raise PermissionError("OpenMontage ist nur im freigegebenen Chat verfügbar.")

    action = parse_command(text)
    if action is None or action == "invalid":
        return HELP
    if action == "help":
        return HELP
    if action == "renew_missing":
        return "Bitte Video-ID angeben: /montage link neu <Video-ID>"
    if action == "proposal":
        return ("Testvorschlag: die mitgelieferte OpenMontage-Demo 'code-to-screen' "
                "mit animierten Texten und Diagrammen. Ohne Stimme, Archivmaterial, Musik "
                "oder API-Keys. Das ist ein Techniktest, nicht der vorgeschlagene NASA-Film. "
                "Start nur mit /montage test starten.")

    token = os.environ.get("GITHUB_TOKEN", "")
    if isinstance(action, dict) and action.get("action") in ("erstellen", "planen"):
        if request_storage is None:
            return ("OpenMontage: Filmauftrag/Planung derzeit NICHT AUSFÜHRBAR. "
                    "Privater Auftragsspeicher nicht verbunden; Kein Job wurde gestartet.")
        if type(update_id) is not int or update_id < 0:
            raise ValueError("Ungültige Telegram-Update-ID.")
        from integrations.openmontage.private_request_store import put_request
        request_id = f"tg-{update_id}"
        try:
            put_request(request_storage, request_id=request_id,
                        prompt=action["prompt"], owner_chat=str(chat))
        except Exception:
            return ("OpenMontage: Private Speicherung fehlgeschlagen. "
                    "Kein Auftrag angenommen und kein Workflow gestartet.")
        return (f"OpenMontage: Auftrag {request_id} privat gespeichert, aber NICHT gestartet. "
                "Der Produktionsworkflow ist noch nicht freigeschaltet.")
    if action == "status":
        return recent_runs(token, get)

    if isinstance(action, str) and action.startswith("approve:"):
        video_id = action.partition(":")[2]
        job_id = f"job_{video_id[:8]}"
        existing = load_jobs_ledger(jobs_state).get(job_id)
        if not isinstance(existing, dict) or existing.get("video_id") != video_id or existing.get("status") != "READY_FOR_APPROVAL":
            return f"OpenMontage: Video {video_id} nicht zur Freigabe bereit oder unbekannt. Keine Freigabe gespeichert."
        save_job_entry(job_id, {**existing, "status": "APPROVED", "editorial_decision": "FREIGEGEBEN"}, jobs_state)
        if feedback_storage is not None:
            from integrations.openmontage.learning_memory_r2 import persist_feedback
            try:
                persist_feedback(feedback_storage, video_id=video_id, decision="approved",
                                 style=existing.get("style") if isinstance(existing.get("style"), dict) else {})
            except Exception:
                return "OpenMontage: Redaktionelle Entscheidung gespeichert, aber Lernspeicher konnte nicht aktualisiert werden."

        return f"✅ OpenMontage V3 Video {video_id} redaktionell FREIGEGEBEN (Kein automatisches Social-Posting)."

    if isinstance(action, str) and action.startswith("reject:"):
        video_id = action.partition(":")[2]
        job_id = f"job_{video_id[:8]}"
        existing = load_jobs_ledger(jobs_state).get(job_id)
        if not isinstance(existing, dict) or existing.get("video_id") != video_id or existing.get("status") != "READY_FOR_APPROVAL":
            return f"OpenMontage: Video {video_id} nicht zur Ablehnung bereit oder unbekannt. Keine Ablehnung gespeichert."
        save_job_entry(job_id, {**existing, "status": "REJECTED", "editorial_decision": "ABLEHNEN"}, jobs_state)
        if feedback_storage is not None:
            from integrations.openmontage.learning_memory_r2 import persist_feedback
            try:
                persist_feedback(feedback_storage, video_id=video_id, decision="rejected",
                                 style=existing.get("style") if isinstance(existing.get("style"), dict) else {})
            except Exception:
                return "OpenMontage: Redaktionelle Entscheidung gespeichert, aber Lernspeicher konnte nicht aktualisiert werden."

        return f"❌ OpenMontage V3 Video {video_id} ABGELEHNT."

    # Legacy workflow dispatch logic for diagnose, demo, renew:...
    if type(update_id) is not int or update_id < 0:
        raise ValueError("Ungültige Telegram-Update-ID.")

    auth = headers(token)
    if isinstance(action, str) and action.startswith("renew:"):
        media_id = action.partition(":")[2]
        workflow = "openmontage-renew-link.yml"
        inputs = {"media_id": media_id}
    else:
        workflow = WORKFLOW
        inputs = {"mode": action, "request_id": f"tg-{update_id}"}

    state_path = Path(state) if state is not None else STATE
    ledger = json.loads(state_path.read_text()) if state_path.exists() else {}
    request_id = f"tg-{update_id}"

    if request_id in ledger:
        return f"Auftrag {request_id} bereits erfasst ({ledger[request_id]}). /montage status"

    state_path.parent.mkdir(parents=True, exist_ok=True)

    def save(value):
        ledger[request_id] = value
        temp = state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(ledger, sort_keys=True) + "\n")
        temp.replace(state_path)

    save("dispatching")
    try:
        r = (post or requests.post)(
            f"{API}/actions/workflows/{workflow}/dispatches",
            headers=auth,
            json={"ref": "main", "inputs": inputs},
            timeout=20,
        )
    except requests.RequestException:
        save("uncertain")
        return (f"Auftrag {request_id}: GitHub-Antwort ausgeblieben; Annahme unklar. "
                "Kein automatischer Neustart. /montage status")

    if r.status_code != 204:
        save(f"rejected-http-{r.status_code}")
        return f"OpenMontage-Start abgelehnt (HTTP {r.status_code}). Workflow auf main und actions:write prüfen."

    save("accepted")
    return f"GitHub hat {request_id} angenommen. Das ist noch kein fertiger Film. /montage status\n{URL}"


def claim_request(request_id: str, token: str, sha: str, post=None) -> bool:
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
        return False
    raise RuntimeError(f"GitHub-Auftragsreservierung fehlgeschlagen (HTTP {r.status_code}).")
