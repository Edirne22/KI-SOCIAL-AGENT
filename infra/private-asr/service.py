"""Authenticated private ASR service. Only the Worker may call its loopback port."""
import hmac
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import run_private_asr
import research_gateway
import scripts.private_birthday_first_production as private_birthday
from scripts.ai_central_shared_inbox import client_from_env
from content_factory_private_video_orchestrator import (
    STAGES, CREATIVE_REVISION, MOTION_MODES, build_plan, load_private_prompt, persist_stage, PrivateQM,
)

_lock = threading.Lock()
_uuid = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
_date = re.compile(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}\Z")
_task = re.compile(r"[A-Za-z0-9_-]{10,64}\Z")

# Guarded OpenCode runtime contract. Keep these fixed in code: requests may not select
# a provider/model or expand execution time/output beyond the reviewed boundary.
_opencode_model = "openrouter/anthropic/claude-sonnet-4.5"
_opencode_timeout = 90
_opencode_max_output = 65536
_opencode_code_config = "/etc/opencode/code.json"
_code_workspace = "/tmp/edirne22-code-workspace"
_code_repo = "https://github.com/Edirne22/KI-SOCIAL-AGENT.git"
_code_executor_contract = "repo-readonly-v1"
_research_runtime_revision = "block9-groq-429-fallback-v1"
_private_video_runtime_revision = "duenya-creative-chain-v3"
_private_runtime_origin = "https://edirne22-private-asr.butupeli.workers.dev"


def _authorized(headers):
    expected = os.getenv("PRIVATE_ASR_INTERNAL_TOKEN", "")
    provided = headers.get("Authorization", "")
    return bool(expected and hmac.compare_digest(provided, "Bearer " + expected))

def _opencode_health():
    binary = shutil.which("opencode")
    git_binary = shutil.which("git")
    config = "/etc/opencode/opencode.json"
    digest = config + ".sha256"
    code_digest = _opencode_code_config + ".sha256"
    ready = bool(binary and os.path.isfile(config) and os.path.isfile(digest))
    code_ready = bool(ready and git_binary and os.path.isfile(_opencode_code_config) and os.path.isfile(code_digest))
    return ready, {"ready": ready, "service": "opencode", "model": _opencode_model if ready else None,
                   "response_contract": "text-v2" if ready else None,
                   "code_ready": code_ready,
                   "code_executor": _code_executor_contract if code_ready else None}

def _opencode_result(output):
    """Extract final assistant text plus completed tool names from OpenCode JSON events."""
    chunks = []
    tools = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid_opencode_json") from exc
        if not isinstance(event, dict):
            raise ValueError("invalid_opencode_event")
        part = event.get("part")
        if event.get("type") == "text" and isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
        elif event.get("type") == "tool_use" and isinstance(part, dict):
            state = part.get("state")
            tool = part.get("tool")
            if isinstance(state, dict) and state.get("status") == "completed" and isinstance(tool, str):
                tools.append(tool[:40])
    if not chunks:
        raise ValueError("missing_opencode_text")
    return "".join(chunks).strip(), list(dict.fromkeys(tools))


def _prepare_code_workspace():
    git = shutil.which("git")
    if not git:
        return False
    git_dir = os.path.join(_code_workspace, ".git")
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "GIT_TERMINAL_PROMPT": "0"}
    try:
        if not os.path.isdir(git_dir):
            if os.path.exists(_code_workspace):
                shutil.rmtree(_code_workspace)
            clone = subprocess.run(
                [git, "clone", "--depth", "1", "--filter=blob:none", "--sparse", "--branch", "main",
                 "--single-branch", _code_repo, _code_workspace],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120, check=False,
            )
            if clone.returncode != 0:
                return False
            sparse = subprocess.run(
                [git, "-C", _code_workspace, "sparse-checkout", "set",
                 ".github", ".opencode", "Claude-Instandhaltung", "agents", "ai-central", "config",
                 "docs", "infra", "memory", "profile", "race", "remotion", "rules", "scripts",
                 "snapshots", "tests", "vision"],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90, check=False,
            )
            if sparse.returncode != 0:
                return False
        else:
            fetch = subprocess.run(
                [git, "-C", _code_workspace, "fetch", "--depth", "1", "origin", "main"],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90, check=False,
            )
            if fetch.returncode != 0:
                return False
            reset = subprocess.run(
                [git, "-C", _code_workspace, "reset", "--hard", "FETCH_HEAD"],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, check=False,
            )
            if reset.returncode != 0:
                return False
            clean = subprocess.run(
                [git, "-C", _code_workspace, "clean", "-fdx"],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, check=False,
            )
            if clean.returncode != 0:
                return False
    except (OSError, subprocess.TimeoutExpired):
        return False
    return True


def _sanitize_diagnostic(raw):
    if not isinstance(raw, str) or not raw.strip():
        return "none"
    text = raw.strip()
    text = re.sub(r"(?:sk-or-v1-[A-Za-z0-9_-]+|Bearer\s+[A-Za-z0-9._-]+|[a-zA-Z0-9_-]{32,})", "[REDACTED]", text)
    clean = " ".join(text.splitlines())
    return clean[:300]


def _run_opencode(message):
    if not _lock.acquire(False):
        return 409, {"error": "busy"}
    try:
        # Fixed argv only. User text is one argv element; no shell, model, path or agent is accepted.
        clean_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": "/tmp",
            "OPENCODE_CONFIG": "/etc/opencode/opencode.json",
            "OPENCODE_DISABLE_AUTOUPDATE": "1",
        }
        provider_key = os.getenv("OPENROUTER_API_KEY", "")
        if not provider_key:
            return 503, {"error": "provider_unavailable"}
        clean_env["OPENROUTER_API_KEY"] = provider_key
        with tempfile.TemporaryDirectory(prefix="opencode-", dir="/tmp") as workdir:
            try:
                result = subprocess.run(
                    ["opencode", "run", "--model", _opencode_model, "--format", "json", message],
                    cwd=workdir, env=clean_env, stdin=subprocess.DEVNULL,
                    capture_output=True, text=True, timeout=_opencode_timeout, check=False,
                )
            except subprocess.TimeoutExpired:
                return 504, {"error": "timeout"}
        output = (result.stdout or "").strip()
        if len(output.encode("utf-8")) > _opencode_max_output:
            return 502, {"error": "output_too_large"}
        if result.returncode != 0:
            detail = _sanitize_diagnostic(result.stderr or result.stdout)
            return 502, {"error": "opencode_failed", "detail": detail}
        try:
            text, _ = _opencode_result(output)
        except ValueError as exc:
            return 502, {"error": "invalid_opencode_output", "detail": _sanitize_diagnostic(str(exc))}
        return 200, {"text": text}
    finally:
        _lock.release()


def _run_opencode_code(message):
    if not _lock.acquire(False):
        return 409, {"error": "busy"}
    try:
        if not _prepare_code_workspace():
            return 503, {"error": "code_workspace_unavailable", "detail": "git workspace clone or fetch failed"}
        provider_key = os.getenv("OPENROUTER_API_KEY", "")
        if not provider_key:
            return 503, {"error": "provider_unavailable"}
        clean_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": "/tmp",
            "GIT_TERMINAL_PROMPT": "0",
            "OPENCODE_CONFIG": _opencode_code_config,
            "OPENCODE_DISABLE_AUTOUPDATE": "1",
            "OPENROUTER_API_KEY": provider_key,
        }
        guarded_prompt = (
            "EDIRNE22 CODE EXECUTION CONTRACT:\n"
            "You are inside a read-only sparse clone of the KI-SOCIAL-AGENT repository. "
            "Use native OpenCode tools for repository facts. Do not emit XML or pseudo function_calls. "
            "Shell is restricted to read-only git inspection and repository file discovery. "
            "Do not claim commit, push or remote write access. Return a normal final answer only after tool results.\n\n"
            "USER REQUEST:\n" + message
        )
        try:
            result = subprocess.run(
                ["opencode", "run", "--model", _opencode_model, "--format", "json", guarded_prompt],
                cwd=_code_workspace, env=clean_env, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=120, check=False,
            )
        except subprocess.TimeoutExpired:
            return 504, {"error": "timeout"}
        output = (result.stdout or "").strip()
        if len(output.encode("utf-8")) > _opencode_max_output:
            return 502, {"error": "output_too_large"}
        if result.returncode != 0:
            detail = _sanitize_diagnostic(result.stderr or result.stdout)
            return 502, {"error": "opencode_failed", "detail": detail}
        try:
            text, tools = _opencode_result(output)
        except ValueError as exc:
            return 502, {"error": "invalid_opencode_output", "detail": _sanitize_diagnostic(str(exc))}
        if "<function_calls>" in text or "<invoke name=" in text:
            return 502, {"error": "pseudo_tool_call_not_executed"}
        return 200, {"text": text, "tools_used": tools, "workspace": _code_executor_contract}
    finally:
        _lock.release()

def _renew_private_video_activity(opener=urlopen):
    """Keep Cloudflare's container activity lease alive during background rendering.

    The origin is fixed in code; no request input can select a URL. Failure is non-fatal
    here because the R2 heartbeat still provides watchdog evidence and Agent 21 recovery.
    """
    token=os.getenv("PRIVATE_ASR_INTERNAL_TOKEN","")
    if not token:
        return False
    request=Request(_private_runtime_origin+"/health",method="GET",headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/json",
    })
    try:
        with opener(request,timeout=8) as response:
            return response.status==200
    except (HTTPError,URLError,OSError,TimeoutError):
        return False

def _video_status(task_id, status, error_code=None, detail=None, stage=None, production_revision=None):
    client,bucket=client_from_env()
    payload={"schema":"PRIVATE-VIDEO-STATUS-V1","task_id":task_id,"status":status,
             "runtime_revision":_private_video_runtime_revision,
             "updated_at":datetime.now(timezone.utc).isoformat()}
    if stage: payload["stage"]=stage
    if production_revision: payload["production_revision"]=production_revision
    if error_code: payload["error_code"]=str(error_code)[:80]
    if detail: payload["detail"]=str(detail)[:300]
    body=json.dumps(payload).encode("utf-8")
    client.put_object(Bucket=bucket,Key=f"ai-central/v1/private-video/{task_id}/status.json",
                      Body=body,ContentType="application/json",CacheControl="private, no-store")
    if production_revision:
        client.put_object(Bucket=bucket,Key=f"ai-central/v1/private-video/{task_id}/revisions/{production_revision}/status.json",
                          Body=body,ContentType="application/json",CacheControl="private, no-store")

def _run_video(task_id, production_revision=None):
    heartbeat_stop=threading.Event()
    current={"stage":"production_lead"}
    def heartbeat():
        ticks=0
        while not heartbeat_stop.wait(10):
            ticks+=1
            try:
                _video_status(task_id,"RUNNING",stage=current["stage"],production_revision=production_revision)
            except Exception:
                pass
            # Cloudflare Container.sleepAfter counts incoming requests, not work done by
            # this background thread. Renew activity every ~30s through the fixed Worker.
            if ticks % 3 == 0:
                _renew_private_video_activity()
    heartbeat_thread=threading.Thread(target=heartbeat,daemon=True)
    try:
        _video_status(task_id,"RUNNING",stage=current["stage"],production_revision=production_revision)
        heartbeat_thread.start()
        client,bucket=client_from_env()
        persist_stage(client,bucket,task_id,"production_lead","RUNNING")
        prompt=load_private_prompt(client,bucket,task_id)
        assets=private_birthday.recent_assets(client,bucket)
        persist_stage(client,bucket,task_id,"production_lead","COMPLETED","prompt resolved and job decomposed")
        current["stage"]="creative_director"
        persist_stage(client,bucket,task_id,"creative_director","RUNNING")
        current["stage"]="creative_director"
        plan=build_plan(task_id,prompt,assets)
        persist_stage(client,bucket,task_id,"creative_director","COMPLETED",plan.story_style)
        current["stage"]="media_story"
        persist_stage(client,bucket,task_id,"media_story","COMPLETED",f"{len(assets)} private assets bound")
        current["stage"]="music_audio"
        persist_stage(client,bucket,task_id,"music_audio","COMPLETED","documented track selected")
        current["stage"]="video_editor_ffmpeg"
        persist_stage(client,bucket,task_id,"video_editor_ffmpeg","RUNNING")
        result=private_birthday.run(task_id=task_id,prompt=prompt,plan=plan,assets_override=assets)
        persist_stage(client,bucket,task_id,"video_editor_ffmpeg","COMPLETED")
        current["stage"]="qm"
        persist_stage(client,bucket,task_id,"qm","RUNNING")
        evidence=result.get("creative_evidence",{})
        qm=PrivateQM().checks(duration=result["duration"],has_audio=result["has_audio"],
                              has_video=result["has_video"],creative={
                                  **evidence,
                                  "expected_effects":MOTION_MODES,
                                  "privacy":plan.privacy,
                              })
        if not qm["passed"]:
            raise RuntimeError("PRIVATE_AGENT_QM_FAILED")
        persist_stage(client,bucket,task_id,"qm","COMPLETED","technical + creative render evidence passed")
        current["stage"]="private_preview"
        preview={"schema":"PRIVATE-VIDEO-PREVIEW-V1","task_id":task_id,"state":"READY_FOR_HUMAN",
                 "r2_key":result["r2_key"],"sha256":result["sha256"],"private":True,"publishable":False}
        preview["production_revision"]=production_revision
        preview_body=json.dumps(preview).encode()
        client.put_object(Bucket=bucket,Key=f"ai-central/v1/private-video/{task_id}/preview.json",
            Body=preview_body,ContentType="application/json",CacheControl="private, no-store")
        if production_revision:
            client.put_object(Bucket=bucket,Key=f"ai-central/v1/private-video/{task_id}/revisions/{production_revision}/preview.json",
                Body=preview_body,ContentType="application/json",CacheControl="private, no-store")
        persist_stage(client,bucket,task_id,"private_preview","COMPLETED","private R2/Telegram preview ready")
        _video_status(task_id,"COMPLETED",stage="private_preview",production_revision=production_revision)
    except Exception as exc:
        try:
            # Never persist the private prompt or secrets; only bounded exception diagnostics.
            _video_status(task_id,"FAILED",exc.__class__.__name__,str(exc),stage=current.get("stage"),production_revision=production_revision)
        except Exception:
            pass
    finally:
        heartbeat_stop.set()
        _lock.release()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Never log private request metadata or audio.

    def respond(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/opencode/health":
            if not _authorized(self.headers):
                return self.respond(401, {"error": "unauthorized"})
            ready, payload = _opencode_health()
            return self.respond(200 if ready else 503, payload)
        if self.path != "/health":
            return self.respond(404, {"error": "not_found"})
        root = os.getenv("EDIRNE22_LOCAL_WHISPER_MODEL", "")
        ready = bool(root and os.path.isfile(os.path.join(root, "model.bin"))
                     and os.path.isfile(os.path.join(root, "config.json")))
        self.respond(200 if ready else 503, {"ready": ready,
                                                "research_runtime_revision": _research_runtime_revision,
                                                "private_video_runtime_revision": _private_video_runtime_revision})

    def do_POST(self):
        if self.path not in ("/jobs","/private-video/jobs","/opencode/chat","/opencode/code","/research/search"):
            return self.respond(404, {"error": "not_found"})
        if not _authorized(self.headers):
            return self.respond(401, {"error": "unauthorized"})
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            limit = 8192 if self.path in ("/opencode/chat","/opencode/code") else (2048 if self.path == "/research/search" else 1024)
            if not 0 < size <= limit:
                return self.respond(413, {"error": "size"})
            data = json.loads(self.rfile.read(size))
            if self.path == "/research/search":
                if not isinstance(data, dict) or set(data) != {"query"} or not isinstance(data.get("query"), str):
                    raise ValueError()
                try:
                    result = research_gateway.research(data["query"])
                except ValueError:
                    raise
                except Exception:
                    return self.respond(502, {"error": "research_provider_failed"})
                return self.respond(200, result)
            if self.path in ("/opencode/chat","/opencode/code"):
                if not isinstance(data, dict) or set(data) != {"message"}:
                    raise ValueError()
                message = data.get("message")
                if not isinstance(message, str) or not message.strip() or len(message) > 6000:
                    raise ValueError()
                status, payload = (_run_opencode_code(message) if self.path == "/opencode/code" else _run_opencode(message))
                return self.respond(status, payload)
            if self.path == "/private-video/jobs":
                if (not isinstance(data, dict) or not set(data).issubset({"task_id","production_revision"})
                    or "task_id" not in data or not isinstance(data["task_id"],str) or not _task.fullmatch(data["task_id"])):
                    raise ValueError()
                production_revision=data.get("production_revision")
                if production_revision is not None and (not isinstance(production_revision,str) or not _revision.fullmatch(production_revision)):
                    raise ValueError()
                client,bucket=client_from_env()
                key=(f"ai-central/v1/private-video/{data['task_id']}/revisions/{production_revision}/status.json"
                     if production_revision else f"ai-central/v1/private-video/{data['task_id']}/status.json")
                try:
                    existing=json.loads(client.get_object(Bucket=bucket,Key=key)["Body"].read(4096))
                except Exception as exc:
                    code=str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))
                    if code not in ("404","NoSuchKey","NotFound"): raise
                else:
                    if existing.get("schema")=="PRIVATE-VIDEO-STATUS-V1" and existing.get("task_id")==data["task_id"]:
                        status=existing.get("status","UNKNOWN")
                        same_revision=existing.get("runtime_revision")==_private_video_runtime_revision
                        if status!="FAILED" and same_revision:
                            return self.respond(200, {"status":status,"task_id":data["task_id"]})
                        # A completed result from an older renderer revision is intentionally
                        # eligible for one explicit authenticated V2 rerender.
                        # FAILED is terminal for automatic retries, but this endpoint is an
                        # explicit authenticated human restart. Reuse the same task id/prompt.

                if not _lock.acquire(False):
                    return self.respond(409, {"error":"busy"})
                _video_status(data["task_id"],"ACCEPTED",production_revision=production_revision)
                threading.Thread(target=_run_video,args=(data["task_id"],production_revision),daemon=True).start()
                return self.respond(202, {"status":"ACCEPTED","task_id":data["task_id"],"production_revision":production_revision})
            if not isinstance(data, dict) or set(data) != {"inbox_id", "date", "language"}:
                raise ValueError()
            if not isinstance(data["inbox_id"], str) or not _uuid.fullmatch(data["inbox_id"]):
                raise ValueError()
            if not isinstance(data["date"], str) or not _date.fullmatch(data["date"]):
                raise ValueError()
            if data["language"] not in ("de", "tr"):
                raise ValueError()
        except (ValueError, TypeError, UnicodeDecodeError):
            return self.respond(400, {"error": "invalid_request"})
        if not _lock.acquire(False):
            return self.respond(409, {"error": "busy"})
        try:
            keys = ("PRIVATE_ASR_INBOX_ID", "PRIVATE_ASR_INBOX_DATE", "PRIVATE_ASR_LANGUAGE")
            previous = {key: os.environ.get(key) for key in keys}
            try:
                os.environ.update(PRIVATE_ASR_INBOX_ID=data["inbox_id"],
                                  PRIVATE_ASR_INBOX_DATE=data["date"],
                                  PRIVATE_ASR_LANGUAGE=data["language"])
                result = run_private_asr.main()
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            self.respond(200 if result == 0 else 422,
                         {"status": "private_draft" if result == 0 else "rejected",
                          **({} if result == 0 else {"reason": run_private_asr.LAST_FAILURE})})
        finally:
            _lock.release()

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 5200), Handler).serve_forever()
