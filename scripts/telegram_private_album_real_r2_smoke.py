"""Manual real-R2 / synthetic-Telegram pre-merge acceptance.

Never calls Telegram, never reads personal media, never publishes. Runs only with
explicit GitHub manual workflow opt-in and the repository's existing R2 secrets.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from scripts.ai_central_shared_inbox import client_from_env
from scripts.telegram_private_media import receive


class _SyntheticReply:
    def __init__(self, payload=None, file_id=None):
        self.payload = payload
        self.file_id = file_id

    def raise_for_status(self):
        pass

    def json(self):
        assert self.file_id is not None
        return {
            "ok": True,
            "result": {
                "file_path": "synthetic/" + self.file_id,
                "file_size": len(self.payload),
            },
        }

    def iter_content(self, chunk_size=65536):
        for start in range(0, len(self.payload), chunk_size):
            yield self.payload[start:start + chunk_size]


def main():
    if os.environ.get("TELEGRAM_ALBUM_REAL_R2_SYNTHETIC_APPROVED") != "true":
        raise RuntimeError("EXPLICIT_MANUAL_OPT_IN_REQUIRED")
    client, bucket = client_from_env()
    with tempfile.TemporaryDirectory() as folder:
        photo = Path(folder) / "synthetic.jpg"
        video = Path(folder) / "synthetic.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=64x64:d=1",
             "-frames:v", "1", "-y", str(photo)],
            timeout=35, check=True,
        )
        subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=64x64:r=5:d=1",
             "-c:v", "mpeg4", "-y", str(video)],
            timeout=35, check=True,
        )
        image_bytes, video_bytes = photo.read_bytes(), video.read_bytes()
        assert image_bytes and video_bytes

        nonce = uuid4().hex
        group = "e2e" + nonce
        chat = "synthetic-" + nonce
        files = {
            "before" + nonce: image_bytes,
            "video" + nonce: video_bytes,
            "after" + nonce: image_bytes,
        }

        def fake_get(url, *, params=None, **kwargs):
            if url.endswith("/getFile"):
                ident = (params or {}).get("file_id")
                if ident not in files:
                    raise AssertionError("Unknown synthetic Telegram file")
                return _SyntheticReply(files[ident], ident)
            prefix = "/synthetic/"
            if prefix not in url:
                raise AssertionError("Unexpected network access (Telegram disabled)")
            ident = url.split(prefix, 1)[1]
            if ident not in files:
                raise AssertionError("Unknown synthetic Telegram payload")
            return _SyntheticReply(files[ident], ident)

        now = datetime.now(timezone.utc)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        base = {"chat": {"id": chat}, "media_group_id": group}
        before = {
            **base, "date": int((midnight - timedelta(seconds=1)).timestamp()),
            "photo": [{"file_id": "before" + nonce}],
        }
        authorized = {
            **base, "date": int((midnight + timedelta(seconds=1)).timestamp()),
            "caption": "/privat",
            "video": {"file_id": "video" + nonce, "mime_type": "video/mp4"},
        }
        following = {
            **base, "date": int((midnight + timedelta(seconds=2)).timestamp()),
            "photo": [{"file_id": "after" + nonce}],
        }

        # Prove that the first, unapproved media is quarantined as metadata only.
        pending = receive(before, update_id=100, token="synthetic", client=client,
                          bucket=bucket, get=fake_get, authorized_chat=chat)
        assert "zurückgehalten" in pending
        from scripts.telegram_private_media import _album_manifest, _read_manifest
        from hashlib import sha256 as digest
        job_id = "tgalbum" + digest((chat + ":" + group).encode()).hexdigest()[:32]
        manifest = _album_manifest(client, bucket, job_id, before)
        key = manifest["prefix"] + "manifest.json"
        assert _read_manifest(client, bucket, key) is None, "Unapproved manifest exists"

        # Owner authorization replays quarantined item; subsequent album items
        # belong to the exact same manifest across UTC midnight.
        result = receive(authorized, update_id=101, token="synthetic", client=client,
                         bucket=bucket, get=fake_get, authorized_chat=chat)
        assert "Privat in R2 gespeichert" in result
        receive(following, update_id=102, token="synthetic", client=client,
                bucket=bucket, get=fake_get, authorized_chat=chat)
        duplicate = receive(authorized, update_id=101, token="synthetic",
                            client=client, bucket=bucket, get=fake_get, authorized_chat=chat)
        assert "bereits gespeichert" in duplicate

        final = _read_manifest(client, bucket, key)
        assert final["job_id"] == job_id and final["lane"] == "private"
        assert final["status"] == "INTAKE" and not final["outputs"]
        assert len(final["assets"]) == 3, "Missing, duplicated, or split album item"
        expected = {
            "before" + nonce: image_bytes,
            "video" + nonce: video_bytes,
            "after" + nonce: image_bytes,
        }
        assert set(asset["mime"] for asset in final["assets"]) == {"image/jpeg", "video/mp4"}
        assert len({a["asset_id"] for a in final["assets"]}) == 3
        for asset in final["assets"]:
            assert asset["key"].startswith(manifest["prefix"] + "originals/")
            original = client.get_object(Bucket=bucket, Key=asset["key"])["Body"].read()
            assert asset["size"] == len(original)
            assert asset["sha256"] == sha256(original).hexdigest()
            assert original in expected.values()
        leftovers = client.list_objects_v2(
            Bucket=bucket, Prefix=manifest["prefix"] + "quarantine/")
        assert not leftovers.get("Contents"), "Approved album has unreplayed quarantine"

        # Force two actual R2 conditional manifest writes to race. Each
        # worker waits after reading the same manifest ETag immediately before
        # its first CAS. The loser must reload and preserve both uploads.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier, local
        from scripts.telegram_private_media import _asset_id

        parallel = {
            "racephoto" + nonce: image_bytes,
            "racevideo" + nonce: video_bytes,
        }
        files.update(parallel)
        manifest_key = manifest["prefix"] + "manifest.json"
        barrier = Barrier(2)
        class RacingClient:
            def __init__(self, original):
                self.original = original
                self.thread_state = local()
            def __getattr__(self, name):
                return getattr(self.original, name)
            def get_object(self, *, Bucket, Key, **kw):
                obj = self.original.get_object(Bucket=Bucket, Key=Key, **kw)
                if Key == manifest_key:
                    self.thread_state.manifest_reads = getattr(
                        self.thread_state, "manifest_reads", 0) + 1
                    if self.thread_state.manifest_reads == 3:
                        barrier.wait(timeout=25)
                return obj

        racing = RacingClient(client)
        concurrent_events = [
            ({**base, "date": int((midnight + timedelta(seconds=3)).timestamp()),
              "photo": [{"file_id": "racephoto" + nonce}]}, 103),
            ({**base, "date": int((midnight + timedelta(seconds=4)).timestamp()),
              "video": {"file_id": "racevideo" + nonce,
                        "mime_type": "video/mp4"}}, 104),
        ]
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(
                receive, event, update_id=uid, token="synthetic",
                client=racing, bucket=bucket, get=fake_get,
                authorized_chat=chat) for event, uid in concurrent_events]
            for future in futures:
                assert "Privat in R2 gespeichert" in future.result(timeout=40)
        final = _read_manifest(client, bucket, key)
        assert len(final["assets"]) == 5, "Real-R2 concurrent CAS lost an album item"
        asset_ids = {a["asset_id"] for a in final["assets"]}
        for event, uid in concurrent_events:
            document = event.get("video") or (event.get("photo") or [{}])[-1]
            assert _asset_id(uid, document["file_id"]) in asset_ids
        for asset in final["assets"]:
            raw = client.get_object(Bucket=bucket, Key=asset["key"])["Body"].read()
            assert len(raw) == asset["size"] and sha256(raw).hexdigest() == asset["sha256"]

        # Reject foreign chat before touching real R2.
        try:
            receive(authorized, update_id=103, token="synthetic",
                    client=client, bucket=bucket, get=fake_get, authorized_chat="not-owner")
        except PermissionError:
            pass
        else:
            raise AssertionError("Unauthorized chat accepted")
        print("LIVE_R2_SYNTHETIC_TELEGRAM_ALBUM_PASS assets=5 private=yes "
              "cross_midnight=yes quarantine_replayed=yes duplicate_safe=yes "
              "sha256_verified=yes cas_concurrency=yes no_real_telegram=yes no_publication=yes")


if __name__ == "__main__":
    main()
