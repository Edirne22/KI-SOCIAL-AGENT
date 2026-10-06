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
import run_private_asr
import research_gateway
import scripts.private_birthday_first_production as private_birthday
from scripts.ai_central_shared_inbox import client_from_env
from content_factory_private_video_orchestrator import (
    STAGES, build_plan, load_private_prompt, persist_stage, PrivateQM,
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


def _authorized(headers):
    expected = os.getenv("PRIVATE_ASR_INTERNAL_TOKEN", "")
    provided = headers.get("Authorization", "")
    return bool(expected and hmac.compare_digest(provided, "Bearer " + expected))

def _opencode_health():
    binary = shutil.which("opencode")
    config = "/etc/opencode/opencode.json"
    digest = config + ".sha256"
    ready = bool(binary and os.path.isfile(config) and os.path.isfile(digest))
    return ready, {"ready": ready, "service": "opencode", "model": _opencode_model if ready else None,
                   "response_contract": "text-v2" if ready else None}

def _opencode_text(output):
    """Extract assistant text from OpenCode --format json NDJSON events."""
    chunks = []
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
        if event.get("type") != "text":
            continue
        part = event.get("part")
        if isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if not chunks:
        raise ValueError("missing_opencode_text")
    return "".join(chunks).strip()


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
            return 502, {"error": "opencode_failed"}
        try:
            text = _opencode_text(output)
        except ValueError:
            return 502, {"error": "invalid_opencode_output"}
        return 200, {"text": text}
    finally:
        _lock.release()

def _video_status(task_id, status, error_code=None, detail=None, stage=None):
    client,bucket=client_from_env()
    payload={"schema":"PRIVATE-VIDEO-STATUS-V1","task_id":task_id,"status":status,
             "updated_at":datetime.now(timezone.utc).isoformat()}
    if stage: payload["stage"]=stage
    if error_code: payload["error_code"]=str(error_code)[:80]
    if detail: payload["detail"]=str(detail)[:300]
    client.put_object(Bucket=bucket,Key=f"ai-central/v1/private-video/{task_id}/status.json",
                      Body=json.dumps(payload).encode("utf-8"),ContentType="application/json",
                      CacheControl="private, no-store")

def _run_video(task_id):
    heartbeat_stop=threading.Event()
    current={"stage":"production_lead"}
    def heartbeat():
        while not heartbeat_stop.wait(10):
            try:
                _video_status(task_id,"RUNNING",stage=current["stage"])
            except Exception:
                pass
    heartbeat_thread=threading.Thread(target=heartbeat,daemon=True)
    try:
        _video_status(task_id,"RUNNING",stage=current["stage"])
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
        qm=PrivateQM().checks(duration=result["duration"],has_audio=result["has_audio"],
                              has_video=result["has_video"],creative={"overlays":plan.overlays,"privacy":plan.privacy})
        if not qm["passed"]:
            raise RuntimeError("PRIVATE_AGENT_QM_FAILED")
        persist_stage(client,bucket,task_id,"qm","COMPLETED","duration/audio/video/creative/privacy passed")
        current["stage"]="private_preview"
        preview={"schema":"PRIVATE-VIDEO-PREVIEW-V1","task_id":task_id,"state":"READY_FOR_HUMAN",
                 "r2_key":result["r2_key"],"sha256":result["sha256"],"private":True,"publishable":False}
        client.put_object(Bucket=bucket,Key=f"ai-central/v1/private-video/{task_id}/preview.json",
            Body=json.dumps(preview).encode(),ContentType="application/json",CacheControl="private, no-store")
        persist_stage(client,bucket,task_id,"private_preview","COMPLETED","private R2/Telegram preview ready")
        _video_status(task_id,"COMPLETED",stage="private_preview")
    except Exception as exc:
        try:
            # Never persist the private prompt or secrets; only bounded exception diagnostics.
            _video_status(task_id,"FAILED",exc.__class__.__name__,str(exc),stage=current.get("stage"))
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
        self.respond(200 if ready else 503, {"ready": ready})

    def do_POST(self):
        if self.path not in ("/jobs","/private-video/jobs","/opencode/chat","/research/search"):
            return self.respond(404, {"error": "not_found"})
        if not _authorized(self.headers):
            return self.respond(401, {"error": "unauthorized"})
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            limit = 8192 if self.path == "/opencode/chat" else (2048 if self.path == "/research/search" else 1024)
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
            if self.path == "/opencode/chat":
                if not isinstance(data, dict) or set(data) != {"message"}:
                    raise ValueError()
                message = data.get("message")
                if not isinstance(message, str) or not message.strip() or len(message) > 6000:
                    raise ValueError()
                status, payload = _run_opencode(message)
                return self.respond(status, payload)
            if self.path == "/private-video/jobs":
                if not isinstance(data, dict) or set(data) != {"task_id"} or not isinstance(data["task_id"],str) or not _task.fullmatch(data["task_id"]):
                    raise ValueError()
                client,bucket=client_from_env()
                key=f"ai-central/v1/private-video/{data['task_id']}/status.json"
                try:
                    existing=json.loads(client.get_object(Bucket=bucket,Key=key)["Body"].read(4096))
                except Exception as exc:
                    code=str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))
                    if code not in ("404","NoSuchKey","NotFound"): raise
                else:
                    if existing.get("schema")=="PRIVATE-VIDEO-STATUS-V1" and existing.get("task_id")==data["task_id"]:
                        status=existing.get("status","UNKNOWN")
                        if status!="FAILED":
                            return self.respond(200, {"status":status,"task_id":data["task_id"]})
                        # FAILED is terminal for automatic retries, but this endpoint is an
                        # explicit authenticated human restart. Reuse the same task id/prompt.

                if not _lock.acquire(False):
                    return self.respond(409, {"error":"busy"})
                _video_status(data["task_id"],"ACCEPTED")
                threading.Thread(target=_run_video,args=(data["task_id"],),daemon=True).start()
                return self.respond(202, {"status":"ACCEPTED","task_id":data["task_id"]})
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
