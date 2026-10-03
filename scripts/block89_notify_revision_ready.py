"""Telegram notice only after canonical private revision and preview verification.

No polling, no publication authority. An R2 IfNoneMatch claim prevents duplicate
messages across workflow retries. An ambiguous Telegram timeout remains claimed:
manual reconciliation is safer than an unsolicited duplicate.
"""
import os
from uuid import UUID
from content_factory_dashboard_review_ack import _read_state
from content_factory_r2_job_repository import R2JobRepository
from media_storage import R2Storage
from telegram_bot import send_message


def notify_verified_revision(job_id, *, storage, repository, sender=send_message):
    UUID(job_id)
    state, _ = _read_state(job_id, storage)
    record = repository.get_job(job_id)
    job = record.job
    run = job.metadata.get("revision_render")
    if (state.get("state") != "READY_FOR_HUMAN"
            or not isinstance(run, dict)
            or run.get("state") != "READY_FOR_HUMAN"
            or run.get("revision") != job.revision
            or state.get("revision") != job.revision
            or not isinstance(run.get("preview"), dict)
            or state.get("preview_id") != run["preview"].get("preview_id")
            or state.get("manifest") != run["preview"].get("manifest")
            or job.status.value != "ready_for_human"):
        raise ValueError("canonical private render and current preview not verified")
    # Recheck actual immutable preview and private media bytes via existing delivery gate.
    from content_factory_revision_render import _deliver
    if _deliver(job_id, run["request_id"], storage, repository) != "READY_FOR_HUMAN":
        raise ValueError("private delivery verification failed")
    preview_id = run["preview"]["preview_id"]
    key = "ai-central/v1/notifications/revision-ready/" + preview_id + ".json"
    import json
    from datetime import datetime, timezone
    claim = {"schema": "FACTORY-REVISION-NOTICE-V1", "job_id": job_id,
             "revision": job.revision, "preview_id": preview_id,
             "state": "SEND_ATTEMPTED",
             "created_at": datetime.now(timezone.utc).isoformat()}
    try:
        storage.client.put_object(Bucket=storage.bucket, Key=key,
            Body=json.dumps(claim, sort_keys=True).encode(),
            ContentType="application/json", IfNoneMatch="*")
    except Exception as exc:
        code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
        if code in ("PreconditionFailed", "412"):
            return "ALREADY_ATTEMPTED"
        raise
    # No private media URL or token in Telegram. Human opens authenticated Dashboard.
    sender("Edirne 22: Video-Neurendern fertig und privat geprüft.\\n"
           f"Auftrag: {job_id}\\nRevision: {job.revision}\\n"
           "Bitte die aktuelle Vorschau im geschützten Dashboard prüfen. "
           "Keine automatische Veröffentlichung.")
    return "SENT"


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--job-id", required=True)
    a = p.parse_args()
    storage = R2Storage.from_env()
    print("BLOCK89_TELEGRAM_NOTICE " + notify_verified_revision(
        a.job_id, storage=storage, repository=R2JobRepository(storage)))
