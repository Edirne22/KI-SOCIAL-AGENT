"""Explicitly dispatched R2 connectivity smoke test; no secret values logged."""
from __future__ import annotations

import os
import uuid

from integrations.openmontage.r2_client import from_environment


def main():
    storage = from_environment()
    key = "openmontage/smoke/" + str(uuid.uuid4()) + ".txt"
    payload = b"openmontage-r2-smoke-v1"
    try:
        storage.put_object(Key=key, Body=payload, ContentType="text/plain")
        obj = storage.get_object(Key=key)
        body = obj["Body"].read(256)
        if body != payload:
            raise RuntimeError("R2 readback mismatch")
        print("R2 smoke test: write/read OK")
    finally:
        # Cleanup is best-effort but a cleanup failure fails the job, not silently ignored.
        storage.client.delete_object(Bucket=storage.bucket, Key=key)
        print("R2 smoke test: cleanup OK")


if __name__ == "__main__":
    main()
