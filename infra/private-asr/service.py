"""Authenticated private ASR service. Only the Worker may call its loopback port."""
import hmac
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from run_private_asr import main as transcribe

_lock = threading.Lock()
_uuid = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
_date = re.compile(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}\Z")

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
        if self.path != "/health":
            return self.respond(404, {"error": "not_found"})
        root = os.getenv("EDIRNE22_LOCAL_WHISPER_MODEL", "")
        ready = bool(root and os.path.isfile(os.path.join(root, "model.bin"))
                     and os.path.isfile(os.path.join(root, "config.json")))
        self.respond(200 if ready else 503, {"ready": ready})

    def do_POST(self):
        if self.path != "/jobs":
            return self.respond(404, {"error": "not_found"})
        expected = os.getenv("PRIVATE_ASR_INTERNAL_TOKEN", "")
        provided = self.headers.get("Authorization", "")
        if not expected or not hmac.compare_digest(provided, "Bearer " + expected):
            return self.respond(401, {"error": "unauthorized"})
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            if not 0 < size <= 1024:
                return self.respond(413, {"error": "size"})
            data = json.loads(self.rfile.read(size))
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
                result = transcribe()
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            self.respond(200 if result == 0 else 422,
                         {"status": "private_draft" if result == 0 else "rejected"})
        finally:
            _lock.release()

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 5200), Handler).serve_forever()
