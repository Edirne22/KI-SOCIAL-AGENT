"""Store truthful per-task execution lifecycle in private R2, never return success prematurely."""
import argparse
import json
import os
import re
from datetime import datetime, timezone
ID=re.compile(r"^[A-Za-z0-9_-]{10,64}$")
ALLOWED={"RUNNING","PENDING_REVIEW","FAILED","BLOCKED_FREE_TIER"}
def build_status(task_id,run_id,state):
    if not ID.fullmatch(task_id) or not re.fullmatch(r"[0-9]{1,18}",run_id):
        raise ValueError("invalid task/run id")
    if state not in ALLOWED:raise ValueError("invalid lifecycle state")
    return {"schema":"AI-CENTRAL-TASK-STATUS-V1","task_id":task_id,
      "github_run_id":run_id,"status":state,
      "updated_at":datetime.now(timezone.utc).isoformat(),
      "report_expected":state=="PENDING_REVIEW"}
def persist(client,bucket,payload):
    key=f"ai-central/v1/tasks/{payload['task_id']}/status.json"
    client.put_object(Bucket=bucket,Key=key,
      Body=json.dumps(payload,sort_keys=True).encode(),ContentType="application/json")
    return key
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--id",required=True)
    p.add_argument("--state",required=True,choices=sorted(ALLOWED))
    a=p.parse_args()
    x=build_status(a.id,os.environ["GITHUB_RUN_ID"],a.state)
    needed=["R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME"]
    if not all(os.environ.get(y) for y in needed):raise RuntimeError("R2 secrets missing")
    import boto3
    c=boto3.client("s3",endpoint_url="https://"+os.environ["R2_ACCOUNT_ID"]+".r2.cloudflarestorage.com",
       aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
    persist(c,os.environ["R2_BUCKET_NAME"],x)
    print(json.dumps({"task_id":x["task_id"],"run_id":x["github_run_id"],"status":x["status"]}))
if __name__=="__main__":main()
