"""One-shot private ASR operator entrypoint. Never log transcript or credentials."""
import os
import sys
import boto3
from content_factory_private_asr_r2_bridge import run_private_r2_asr

def main():
    names=("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME","PRIVATE_ASR_INBOX_ID","PRIVATE_ASR_INBOX_DATE","PRIVATE_ASR_LANGUAGE","EDIRNE22_LOCAL_WHISPER_MODEL")
    missing=[n for n in names if not os.getenv(n)]
    if missing:
        print("PRIVATE_ASR_NOT_CONFIGURED: "+",".join(missing),file=sys.stderr)
        return 2
    model_dir=os.environ["EDIRNE22_LOCAL_WHISPER_MODEL"]
    if not os.path.isdir(model_dir):
        print("PRIVATE_ASR_MODEL_NOT_PROVISIONED",file=sys.stderr)
        return 2
    endpoint="https://"+os.environ["R2_ACCOUNT_ID"]+".r2.cloudflarestorage.com"
    client=boto3.client("s3",endpoint_url=endpoint,aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
    try:
        result=run_private_r2_asr(client,os.environ["R2_BUCKET_NAME"],os.environ["PRIVATE_ASR_INBOX_ID"],os.environ["PRIVATE_ASR_INBOX_DATE"],os.environ["PRIVATE_ASR_LANGUAGE"],model_dir=model_dir)
    except Exception as exc:
        print("PRIVATE_ASR_FAILED: "+type(exc).__name__,file=sys.stderr)
        return 1
    print("PRIVATE_ASR_COMPLETED_PRIVATE_DRAFT")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
