"""One-shot private ASR operator entrypoint. Never log transcript or credentials."""
import os
import sys
import boto3
from content_factory_private_asr_r2_bridge import run_private_r2_asr
from content_factory_private_asr import PrivateASRError

# Only bounded, fixed diagnostics cross the private container boundary.
LAST_FAILURE = "unknown"

def safe_failure(exc):
    if not isinstance(exc, PrivateASRError):
        return "r2_or_runtime_failure"
    msg = str(exc)
    if msg in ("missing or ambiguous inbox identity", "not a canonical private audio upload", "inbox index truncated; refuse ambiguous lookup"):
        return "inbox_verification_failed"
    if msg == "R2 audio metadata mismatch":
        return "r2_metadata_mismatch"
    if msg in ("explicit current ASR consent not found", "missing, revoked or mismatched consent"):
        return "consent_verification_failed"
    if msg == "unsupported audio format":
        return "audio_format_rejected"
    if msg in ("private audio decoding failed", "private decoded audio unavailable"):
        return "audio_decode_failed"
    if msg == "transcript already exists; no silent overwrite":
        return "transcript_already_exists"
    return "private_processing_failed"

def main():
    global LAST_FAILURE
    LAST_FAILURE = "unknown"
    names=("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME","PRIVATE_ASR_INBOX_ID","PRIVATE_ASR_INBOX_DATE","PRIVATE_ASR_LANGUAGE","EDIRNE22_LOCAL_WHISPER_MODEL")
    missing=[n for n in names if not os.getenv(n)]
    if missing:
        LAST_FAILURE = "runtime_configuration_missing"
        print("PRIVATE_ASR_NOT_CONFIGURED: "+",".join(missing),file=sys.stderr)
        return 2
    model_dir=os.environ["EDIRNE22_LOCAL_WHISPER_MODEL"]
    if not os.path.isdir(model_dir):
        LAST_FAILURE = "model_missing"
        print("PRIVATE_ASR_MODEL_NOT_PROVISIONED",file=sys.stderr)
        return 2
    endpoint="https://"+os.environ["R2_ACCOUNT_ID"]+".r2.cloudflarestorage.com"
    client=boto3.client("s3",endpoint_url=endpoint,aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
    try:
        result=run_private_r2_asr(client,os.environ["R2_BUCKET_NAME"],os.environ["PRIVATE_ASR_INBOX_ID"],os.environ["PRIVATE_ASR_INBOX_DATE"],os.environ["PRIVATE_ASR_LANGUAGE"],model_dir=model_dir)
    except Exception as exc:
        LAST_FAILURE = safe_failure(exc)
        print("PRIVATE_ASR_FAILED: "+type(exc).__name__,file=sys.stderr)
        return 1
    print("PRIVATE_ASR_COMPLETED_PRIVATE_DRAFT")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
