"""Verify Telegram runner R2 prerequisites without printing secret values."""
from __future__ import annotations

import os

from integrations.openmontage.r2_client import PrivateStorageUnavailable, from_environment

REQUIRED = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")


def check_telegram_r2_contract(*, env=None, boto3_module=None) -> dict:
    env = os.environ if env is None else env
    missing = [key for key in REQUIRED if not env.get(key)]
    if missing:
        return {"configured": False, "reason": "MISSING_R2_CONFIGURATION", "missing_names": missing}
    try:
        from_environment(env=env, boto3_module=boto3_module)
    except PrivateStorageUnavailable:
        return {"configured": False, "reason": "R2_CLIENT_UNAVAILABLE", "missing_names": []}
    return {"configured": True, "reason": "R2_CLIENT_CONFIGURED", "missing_names": []}


if __name__ == "__main__":
    result = check_telegram_r2_contract()
    print(result["reason"])
    if not result["configured"]:
        raise SystemExit(1)
