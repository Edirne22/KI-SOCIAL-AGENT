"""Read-only diagnosis of the Dünya V4 admin route (no restart, no private data)."""
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ORIGIN = "https://edirne22-private-asr.butupeli.workers.dev"
TOKEN = os.environ.get("PRIVATE_ASR_INTERNAL_TOKEN", "")
if not TOKEN:
    raise SystemExit("DIAG_BLOCKED_MISSING_PRIVATE_ASR_INTERNAL_TOKEN")

for path in ("/health", "/admin/container-restart"):
    request = Request(
        ORIGIN + path,
        method="GET",
        headers={"Authorization": "Bearer " + TOKEN, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("content-type", "").split(";")[0].lower()
            server = response.headers.get("server", "").lower()
    except HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get("content-type", "").split(";")[0].lower()
        server = exc.headers.get("server", "").lower()
    except URLError:
        print(f"{path}: NETWORK_ERROR")
        continue
    # Never print response bodies, credentials, cookies or request headers.
    layer = (
        "EXPECTED_WORKER_METHOD_GUARD" if path == "/admin/container-restart" and status == 405
        else "EXPECTED_HEALTH" if path == "/health" and status == 200
        else "EDGE_OR_DEPLOYMENT_MISMATCH_SUSPECTED" if status == 403
        else "INVESTIGATE"
    )
    print(f"{path}: HTTP_{status} TYPE_{content_type or 'missing'} SERVER_{server or 'missing'} CLASS_{layer}")
