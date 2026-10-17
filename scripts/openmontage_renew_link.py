"""Renew an existing private R2 preview URL and send only to the owner."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from media_storage import R2Storage
from scripts.openmontage_r2 import renew_private_preview
from scripts.openmontage_telegram_preview import send_owner_preview


def main():
    with TemporaryDirectory(prefix="om-renew-") as cache:
        storage = R2Storage.from_env(cache_root=Path(cache))
        preview = renew_private_preview(os.environ["OPENMONTAGE_MEDIA_ID"], storage=storage)
        send_owner_preview(preview)
        print("Private renewal sent to configured Telegram owner; signed URL withheld.")


if __name__ == "__main__":
    main()
