"""Independent cloud engineering jury with prior R2 evidence; never deploy or run model code."""
import concurrent.futures, json, os, re, time
from pathlib import Path
import requests

R2_RUN="36856381238"
R2_KEY="ai-central/v1/tasks/9bd3b70f1d494e1f9ce8fe06152a2e70/runs/"+R2_RUN+"/report.json"
EVIDENCE="""Verified: One deterministic Cloudflare getContainer() Durable Object id,
max_instances 1, standard-2, wrapper startAndWaitForPorts(5199) every fetch,
sleepAfter=5m, Worker-only /_factory/health; Worker boot ID is not container identity.
Upstream pinned OpenChatCut serves on Vite dev:shared, npm ci in Docker, Node 24.
Upstream mcp.ts holds sessions in process-local Map and forgetSession() on transport.onclose,
60-minute idle timeout and 64-session cap. No restart persistence for sessions.
Post-deploy #67: readiness responses alternated 200 and 500 then 3 valid initializes;
health 200, SDK connects, 1s later first status call 404 session expired.
Comparison #272 35min after deploy: raw init + notification + status succeeded 3/6,
SDK path 1/6, one "container not listening in TCP 10.0.0.1:5199".
Later diagnostic raw 0/6 (25s timeout each), SDK 0/6 (60s timeout), raw idle
not reached due to 25s init timeout. No Cloudflare lifecycle/start/stop/OOM logs.
Cloudflare issues #139 #232 #233 report similar ready-port or DO old-image issues,
not demonstrated to be this incident. No new deployment or runtime fix authorized."""
QUESTIONS={
"platform":"Diagnose Cloudflare container management, fixed DO id, startup and port. Distinguish deploy rollout vs later 35-minute and next-day failures. What *single no-deploy* investigation and then smallest instrumentation is worthwhile?",
"protocol":"Diagnose MCP StreamableHTTP transport immediate session delete, raw vs SDK comparison. What deterministic local regression would demonstrate whether HTTP keepalive close triggers onclose? What can and cannot explain TCP 5199 disappearing?",
"adversarial":"Challenge both platform and protocol hypotheses. Check Vite dev:shared process build and possible resource exhaustion as alternative causes. Give ranked discriminating tests based on evidence, not confidence rhetoric."}
PROVIDERS=("google","openrouter","nvidia")
SYSTEM="Engineering incident reviewer. German. Evidence before hypotheses. Do not invent Cloudflare logs or claim fixes tested. JSON keys: observations, possible_causes, decisive_test, smallest_safe_change, evidence_missing. Under 1000 tokens."
def sanitize(v):
    return re.sub(r"(?i)(Bearer\\s+|api[_-]?key\\s*[:=]\\s*)\\S+",r"\\1[REDACTED]",str(v))[:6500]
def prior():
    required=("R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY","R2_BUCKET_NAME")
    if not all(os.getenv(k) for k in required):return {"status":"NO_R2_CREDS"}
    try:
        import boto3
        client=boto3.client("s3",endpoint_url="https://"+os.environ["R2_ACCOUNT_ID"]+".r2.cloudflarestorage.com",
             aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
        obj=client.get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=R2_KEY)
        data=json.loads(obj["Body"].read(120_000))
        if data.get("schema")!="CLOUD-AI-CENTRAL-V1":return {"status":"BAD_SCHEMA"}
        results=[]
        for role in data.get("results",[]):
            review=next((x for x in reversed(role.get("attempts",[])) if x.get("status")=="ANSWER"),None)
            results.append({"role":role.get("role"),"provider":review.get("provider") if review else None,
                  "finding":sanitize(review.get("text",""))[:2400] if review else ""})
        return {"status":"FOUND","reviews":results}
    except Exception as exc:return {"status":"READ_ERROR","kind":type(exc).__name__}
def inspect(name,question,prior_packet,cfg):
    key=os.getenv(cfg["api_key_env"],"")
    if not key:return {"worker":name,"status":"NO_KEY"}
    model=cfg["models"].get("default") or cfg["models"].get("reasoning")
    prompt=json.dumps({"evidence":EVIDENCE,"previous_reviews":prior_packet,"task":question},ensure_ascii=False)
    try:
        t=time.monotonic()
        response=requests.post(cfg["base_url"].rstrip("/")+"/chat/completions",
           headers={"Authorization":"Bearer "+key},
           json={"model":model,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
                 "temperature":0.1,"max_tokens":1100},timeout=38)
        if response.status_code!=200:return {"worker":name,"model":model,"status":"HTTP_ERROR","http_status":response.status_code}
        text=sanitize(response.json()["choices"][0]["message"].get("content",""))
        if not text:return {"worker":name,"model":model,"status":"EMPTY"}
        return {"worker":name,"model":model,"status":"ANSWER","elapsed_ms":round((time.monotonic()-t)*1000),"review":text}
    except (requests.RequestException,ValueError,KeyError,TypeError,IndexError) as exc:
        return {"worker":name,"model":model,"status":"ERROR","kind":type(exc).__name__}
def main():
    cfg=json.loads(Path("config/llm_providers.json").read_text(encoding="utf-8"))["providers"]
    previous=prior()
    print("PRIOR",json.dumps(previous,ensure_ascii=False))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(inspect,name,question,previous,cfg[provider]) for (name,question),provider in zip(QUESTIONS.items(),PROVIDERS)]
        outcomes=[x.result() for x in futures]
    result={"schema":"OCC-INCIDENT-JURY-V1","advisory":True,"requires_log_verification":True,"prior_status":previous.get("status"),"workers":outcomes}
    Path("openchatcut-root-cause-jury.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    for item in outcomes:print("JURY",json.dumps(item,ensure_ascii=False))
    if not any(x.get("status")=="ANSWER" for x in outcomes):raise SystemExit("no real model answers")
if __name__=="__main__":main()
