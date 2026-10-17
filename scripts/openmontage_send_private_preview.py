"""Explicit private preview: no CLI arguments containing secrets or signed URLs."""
from __future__ import annotations
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from media_storage import R2Storage
from scripts.openmontage_r2 import upload_private_preview
from scripts.openmontage_telegram_preview import send_owner_preview


def main() -> None:
    source = Path(os.environ["OPENMONTAGE_MP4"])
    with TemporaryDirectory(prefix="om-r2-cache-") as cache:
        storage = R2Storage.from_env(cache_root=Path(cache))
        result = upload_private_preview(source, storage=storage, expires_seconds=86400)
        send_owner_preview(result)
        # Intentionally do not print the bearer URL or full signed request.
        print(json.dumps({"status": "sent_to_owner", "media_id": result["media_id"],
                          "expiry_seconds": result["expires_seconds"]}))


if __name__ == "__main__":
    main()
