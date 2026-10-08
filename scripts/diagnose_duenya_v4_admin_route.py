"""GET-only route provenance: no restart, recovery, redirects or private media."""
import hashlib
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ORIGIN = "https://edirne22-private-asr.butupeli.workers.dev"
CLIENTS = (("urllib-default", None), ("edirne22", "Edirne22-Private-Video-Recovery/1.0"))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(path, token, user_agent, opener):
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    if user_agent:
        headers["User-Agent"] = user_agent
    request = Request(ORIGIN + path, method="GET", headers=headers)
    try:
        response = opener(request, timeout=20)
    except HTTPError as exc:
        response = exc
    except (URLError, TimeoutError):
        return {"status": "NETWORK_ERROR"}
    with response:
        raw = response.read(16384)
        content_type = response.headers.get("content-type", "").split(";")[0].lower()
        result = {
            "status": response.status,
            "type": content_type if content_type in ("application/json", "text/html", "text/plain") else "other",
            "cloudflare_server": response.headers.get("server", "").lower() == "cloudflare",
            "bytes": len(raw),
            "body_sha256": hashlib.sha256(raw).hexdigest(),
        }
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeError):
        body = None
    result["worker_method_guard"] = isinstance(body, dict) and body.get("error") == "method"
    result["worker_auth_guard"] = isinstance(body, dict) and body.get("error") == "unauthorized"
    result["ready"] = isinstance(body, dict) and body.get("ready") is True
    result["target_video_revision"] = isinstance(body, dict) and body.get("private_video_runtime_revision") == "duenya-creative-chain-v3"
    # Only known fixed identifiers; never copy arbitrary values from a response.
    result["known_error"] = next((code for code in ("access_denied", "Forbidden", "forbidden", "not_found")
                                 if isinstance(body, dict) and body.get("error") == code), "other")
    return result


def main(opener=None):
    token = os.environ.get("PRIVATE_ASR_INTERNAL_TOKEN", "")
    if not token:
        raise SystemExit("DIAG_BLOCKED_MISSING_PRIVATE_ASR_INTERNAL_TOKEN")
    opener = opener or build_opener(NoRedirect()).open
    for label, user_agent in CLIENTS:
        for path in ("/health", "/admin/container-restart"):
            result = probe(path, token, user_agent, opener)
            print(json.dumps({"client": label, "path": path, **result}, sort_keys=True))


if __name__ == "__main__":
    main()
