"""Private R2 request transport for OpenMontage (no public URLs)."""
from __future__ import annotations

from integrations.openmontage.request_contract import load_request, serialize_request, MontageRequestError


def request_key(request_id: str) -> str:
    """Strictly validate IDs before constructing private object keys."""
    from integrations.openmontage.request_contract import build_request
    build_request(request_id=request_id, prompt="validate", owner_chat="validate")
    return f"openmontage/requests/{request_id}.json"


def put_request(storage, *, request_id: str, prompt: str, owner_chat: str) -> str:
    """Persist request privately; caller must only dispatch after successful write."""
    payload = serialize_request(request_id=request_id, prompt=prompt, owner_chat=owner_chat)
    key = request_key(request_id)
    storage.put_object(Key=key, Body=payload, ContentType="application/json")
    return key


def get_request(storage, *, request_id: str) -> dict:
    """Read and validate private request payload from an authenticated storage client."""
    response = storage.get_object(Key=request_key(request_id))
    payload = response["Body"].read(8193)
    return load_request(payload, expected_request_id=request_id)
