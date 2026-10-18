"""B75: explicit owner-approved private Telegram album -> verified MP4.

No publication or remote URL intake. Caller must supply already-verified
research and an explicit scene-to-asset rights selection JSON.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.openmontage_owner_album_handoff import stage_owner_album
from scripts.openmontage_render_verified import render_verified_research


def render_owner_album(*, client, bucket, owner_chat, authorized_chat, job_id,
                       selections, research, output_dir):
    if not isinstance(selections, list) or not selections:
        raise ValueError("PRIVATE_MEDIA_INVALID: explicit scene selections required")
    with TemporaryDirectory(prefix="openmontage-owner-album-") as tmp:
        root = Path(tmp) / "media"
        scene_config = stage_owner_album(
            client, bucket, job_id=job_id, owner_chat=owner_chat,
            authorized_chat=authorized_chat, selections=selections, destination=root)
        return render_verified_research(research, Path(output_dir),
                                        scene_config=scene_config, media_root=root)


def main():
    parser = argparse.ArgumentParser(description="Owner-approved Telegram album renderer")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--selections", type=Path, required=True)
    parser.add_argument("--research", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.selections.stat().st_size > 32768 or args.research.stat().st_size > 262144):
        raise ValueError("PRIVATE_MEDIA_INVALID: oversized input JSON")
    from scripts.ai_central_shared_inbox import client_from_env
    client, bucket = client_from_env()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not chat:
        raise PermissionError("PRIVATE_MEDIA_UNAUTHORIZED: Telegram owner not configured")
    result = render_owner_album(
        client=client, bucket=bucket, owner_chat=chat, authorized_chat=chat,
        job_id=args.job_id,
        selections=json.loads(args.selections.read_text(encoding="utf-8"))["scenes"],
        research=json.loads(args.research.read_text(encoding="utf-8")),
        output_dir=args.output)
    print(json.dumps({"status": result.get("status"),
                      "video_file": result.get("video_file"),
                      "source_media_included": result.get("source_media_included")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
