"""Live synthetic private R2 roundtrip; no personal media, no publishing."""
import io
import json
import os
import subprocess
import tempfile
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from scripts.ai_central_shared_inbox import client_from_env
from scripts.r2_media_warehouse import new_manifest, store_original

def main():
    if os.environ.get("WAREHOUSE_SYNTHETIC_LIVE_APPROVED") != "true":
        raise RuntimeError("LIVE_SYNTHETIC_TEST_NOT_APPROVED")
    client,bucket=client_from_env()
    job_id="smoke"+uuid4().hex
    manifest=new_manifest(lane="private",title="SYNTHETIC-TEST-NO-PERSONAL-MEDIA",
                          created_at=datetime.now(timezone.utc),job_id=job_id)
    with tempfile.TemporaryDirectory() as folder:
        photo=Path(folder)/"synthetic.jpg"
        video=Path(folder)/"synthetic.mp4"
        subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=blue:s=64x64:d=1",
                        "-frames:v","1","-y",str(photo)],check=True,timeout=30)
        subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=red:s=64x64:r=5:d=1",
                        "-c:v","mpeg4","-y",str(video)],check=True,timeout=30)
        for path,mime in ((photo,"image/jpeg"),(video,"video/mp4")):
            payload=path.read_bytes()
            ident="asset"+uuid4().hex
            manifest=store_original(client,bucket,manifest,asset_id=ident,filename=path.name,
                                    mime=mime,payload=payload)
            key=manifest["assets"][-1]["key"]
            stored=client.get_object(Bucket=bucket,Key=key)["Body"].read()
            if sha256(stored).digest()!=sha256(payload).digest():
                raise RuntimeError("R2_ORIGINAL_CHECKSUM_MISMATCH")
        remote=json.loads(client.get_object(Bucket=bucket,Key=manifest["prefix"]+"manifest.json")["Body"].read())
        if remote["lane"]!="private" or remote["job_id"]!=job_id or len(remote["assets"])!=2:
            raise RuntimeError("R2_MANIFEST_MISMATCH")
        if any(not asset["key"].startswith(manifest["prefix"]) for asset in remote["assets"]):
            raise RuntimeError("CROSS_LANE_KEY_DETECTED")
        print("LIVE_SYNTHETIC_PRIVATE_R2_ROUNDTRIP_PASS job="+job_id)

if __name__=="__main__":
    main()
