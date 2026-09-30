"""Live R2 smoke test. Requires repository secrets; never prints credentials."""
from pathlib import Path
import tempfile
from media_storage import R2Storage

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    src=root/"r2-smoke.txt"
    src.write_bytes(b"Edirne22 Content Factory R2 live smoke\n")
    store=R2Storage.from_env(cache_root=root/"cache")
    ref=store.put_file(src,provenance="github-actions:r2-live-smoke",mime_type="text/plain")
    out=store.resolve_local(ref)
    if out.read_bytes()!=src.read_bytes():
        raise SystemExit("R2 roundtrip mismatch")
    print("R2 LIVE roundtrip + SHA-256 integrity: PASS")
