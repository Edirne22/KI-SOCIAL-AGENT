"""Sendet ausschließlich explizit freigegebene Instagram-Kommentarantworten."""
from __future__ import annotations

import os
import requests

API = "https://graph.instagram.com/v23.0"


def send_reply(comment_id: str, message: str) -> str:
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    comment_id = str(comment_id or "").strip()
    message = " ".join(str(message or "").split()).strip()
    if not token:
        raise RuntimeError("INSTAGRAM_ACCESS_TOKEN nicht gesetzt")
    if not comment_id:
        raise RuntimeError("comment_id fehlt")
    if not message:
        raise RuntimeError("message ist leer")

    try:
        response = requests.post(
            f"{API}/{comment_id}/replies",
            data={"message": message, "access_token": token},
            timeout=45,
        )
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
        # TODO: Vor erneutem Senden Idempotenz-Check gegen Instagram einbauen.
        print("AMBIGUOUS - manuell prüfen")
        raise RuntimeError("AMBIGUOUS - manuell prüfen") from exc
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Instagram Reply API {response.status_code}: {response.text[:500]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Instagram Reply API lieferte kein gültiges JSON.") from exc

    reply_id = str(payload.get("id") or "").strip()
    if not reply_id:
        raise RuntimeError("Instagram Reply API lieferte keine Reply-ID.")
    return reply_id
