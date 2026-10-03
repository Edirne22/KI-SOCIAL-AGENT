"""Private R2 -> offline faster-whisper -> private R2 bridge.

Operator-only container entrypoint. Never run in GitHub Actions with real audio.
Requires pre-provisioned private R2 S3 credentials and an already-installed local
model. Consent is checked against a separate trusted R2 record, not a CLI flag.
No external transcription API, social publish, or public media URL.
"""
from __future__ import annotations
import json
import os
import re
from hashlib import sha256
from datetime import datetime, timezone
from content_factory_private_asr import PrivateASRRequest, PrivateASRError
from content_factory_private_asr_runtime import transcribe_private_audio

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
PREFIX = "ai-central/v1/inbox/"
OUT = "ai-central/v1/private-asr/"
MAX_INDEX = 1000

def verified_inbox(client, bucket, inbox_id, date):
    """Find the unique canonical inbox record; never accept caller R2 keys."""
    if not UUID.fullmatch(inbox_id) or not re.fullmatch(r"20\d\d-\d\d-\d\d", date):
        raise PrivateASRError("invalid inbox reference")
    if datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d") != date:
        raise PrivateASRError("invalid date")
    page = client.list_objects_v2(Bucket=bucket, Prefix=PREFIX + date + "/", MaxKeys=MAX_INDEX)
    if page.get("IsTruncated"):
        raise PrivateASRError("inbox index truncated; refuse ambiguous lookup")
    matches = []
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".json"):
            continue
        item = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read())
        if item.get("id") == inbox_id:
            matches.append(item)
    if len(matches) != 1:
        raise PrivateASRError("missing or ambiguous inbox identity")
    item = matches[0]
    f = item.get("file") or {}
    if (item.get("schema") != "AI-INBOX-V1" or item.get("kind") != "file" or
        item.get("channel") != "web" or item.get("created_at", "")[:10] != date or
        f.get("r2_key") != f"ai-central/v1/uploads/{inbox_id}/data" or
        f.get("mime") not in ("audio/webm", "audio/mp4", "audio/x-m4a", "audio/m4a", "audio/ogg")):
        raise PrivateASRError("not a canonical private audio upload")
    return f

def verified_consent(client, bucket, inbox_id, audio_sha, language):
    """Explicit per-record opt-in, stored separately from user-editable inbox.

    The authenticated dashboard consent endpoint must write this record only
    after user action. This bridge must never manufacture consent.
    """
    key = OUT + inbox_id + "/consent.json"
    try:
        record = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read())
    except Exception as exc:
        raise PrivateASRError("explicit current ASR consent not found") from exc
    expected = {"schema":"PRIVATE-ASR-CONSENT-V1","inbox_id":inbox_id,
                "source_sha256":audio_sha,"scope":"transcription","status":"granted"}
    if any(record.get(k) != v for k, v in expected.items()) or record.get("language") != language:
        raise PrivateASRError("missing, revoked or mismatched consent")
    return key

def run_private_r2_asr(client, bucket, inbox_id, date, language, *, model=None, model_dir=None):
    if language not in ("de", "tr"):
        raise PrivateASRError("choose explicit German or Turkish")
    f = verified_inbox(client, bucket, inbox_id, date)
    key = f["r2_key"]
    obj = client.get_object(Bucket=bucket, Key=key)
    if obj.get("ContentType") != f["mime"] or obj.get("ContentLength") != f["size"]:
        raise PrivateASRError("R2 audio metadata mismatch")
    # Hard cap before reading: private audio is never logged or sent to CI.
    if type(f["size"]) is not int or not 0 < f["size"] <= 8*1024*1024:
        raise PrivateASRError("invalid audio size")
    audio = obj["Body"].read(8*1024*1024 + 1)
    digest = sha256(audio).hexdigest()
    consent_key = verified_consent(client, bucket, inbox_id, digest, language)
    request = PrivateASRRequest(inbox_id, key, digest, len(audio), f["mime"],
                                language, consent_key)
    result = transcribe_private_audio(request, audio, model=model, model_dir=model_dir)
    # Re-read consent immediately before output; revocation wins.
    verified_consent(client, bucket, inbox_id, digest, language)
    output_key = OUT + inbox_id + "/" + digest + "/" + language + ".json"
    payload = {"schema":"PRIVATE-ASR-TRANSCRIPT-V1","inbox_id":inbox_id,
               "source_sha256":digest,"language":language,"text":result.text,
               "created_at":datetime.now(timezone.utc).isoformat(),
               "status":"DRAFT_REQUIRES_HUMAN_REVIEW"}
    # No public ACL; do not overwrite existing transcript silently.
    try:
        client.head_object(Bucket=bucket, Key=output_key)
    except client.exceptions.ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in ("404","NoSuchKey","NotFound"):
            raise
    else:
        raise PrivateASRError("transcript already exists; no silent overwrite")
    client.put_object(Bucket=bucket, Key=output_key, Body=json.dumps(payload).encode(),
                      ContentType="application/json", CacheControl="private, no-store")
    return {"inbox_id":inbox_id,"status":"TRANSCRIPT_PRIVATE_DRAFT",
            "transcript_key":output_key}

if __name__ == "__main__":
    raise SystemExit("Operator-only module: use authenticated container orchestration; no CLI with private identifiers")
