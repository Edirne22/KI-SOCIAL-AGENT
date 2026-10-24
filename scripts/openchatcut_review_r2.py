"""Upload bounded sanitized multi-model review reports to R2 (optional).

GitHub Actions is the compute/queue. R2 only persists JSON artifacts.
Never upload raw credentials, workflow environment, or arbitrary filesystem paths.
"""
import json
import os
import re
from pathlib import Path

def upload_report(path, *, client, bucket, run_id):
    source = Path(path)
    if source.name != "openchatcut-multi-review.json" or not source.is_file():
        raise ValueError("report path must be the expected generated file")
    report = json.loads(source.read_text(encoding="utf-8"))
    if report.get("schema") != "OPENCHATCUT-ADVISORY-REVIEW-V1" or report.get("advisory_only") is not True:
        raise ValueError("unexpected report schema")
    if source.stat().st_size > 250_000:
        raise ValueError("report exceeds size limit")
    if not re.fullmatch(r"[0-9]{1,18}", str(run_id)):
        raise ValueError("unsafe run id")
    key = f"ai-diagnostics/openchatcut/run-{run_id}/multi-model-review.json"
    client.upload_file(str(source), bucket, key, ExtraArgs={"ContentType":"application/json"})
    return key

if __name__ == "__main__":
    required=("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME")
    available=[bool(os.environ.get(k)) for k in required]
    if not any(available):
        print("R2_UPLOAD_SKIPPED: optional credentials not configured")
        raise SystemExit(0)
    if not all(available):
        raise SystemExit("R2_UPLOAD_INCOMPLETE: required configuration missing")
    import boto3
    client=boto3.client("s3",endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
    key=upload_report("openchatcut-multi-review.json",client=client,
        bucket=os.environ["R2_BUCKET_NAME"],run_id=os.environ["GITHUB_RUN_ID"])
    print("R2_UPLOAD_OK:",key)
