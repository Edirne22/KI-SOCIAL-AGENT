"""Upload a completed synthetic MP4 privately; notify owner, never social publish."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from media_storage import R2Storage
from scripts.openmontage_r2 import upload_private_preview
from scripts.openmontage_quality_gate import validate_video
from scripts.openmontage_telegram_preview import send_owner_preview


def main():
    video = Path(os.environ["OPENMONTAGE_VIDEO_PATH"])
    validate_video(video)
    with TemporaryDirectory(prefix="om-preview-") as cache:
        storage = R2Storage.from_env(cache_root=Path(cache))
        preview = upload_private_preview(video, storage=storage)
        research_path = Path("integrations/openmontage/.runtime/verified_research.json")\n        if not research_path.is_file():\n            raise ValueError("Verified research required for social preview")\n        from scripts.openmontage_social_copy import build_social_copy\n        social_copy = build_social_copy(json.loads(research_path.read_text(encoding="utf-8")))\n        send_owner_preview(preview, social_copy=social_copy)
    print("Private preview uploaded and owner notified; signed URL withheld.")


if __name__ == "__main__":
    main()
