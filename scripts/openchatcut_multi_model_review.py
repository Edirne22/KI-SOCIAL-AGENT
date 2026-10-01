"""Read-only, bounded, parallel multi-model diagnostic review; no API keys or logs with secrets in outputs."""
import argparse
import concurrent.futures
import json
import os
import re
from pathlib import Path
import requests

CONFIG = Path(__file__).resolve().parents[1] / "config/llm_providers.json"
PROVIDERS = ("nvidia", "groq", "google", "openrouter")
# Submit only sanitized, already reviewed evidence. Never send GitHub environment variables.
EVIDENCE = """
Edirne22/OpenChatCut Cloudflare: single getContainer() ID, standard-2, max_instances=1,
startAndWaitForPorts(5199). Deploy run #67: intermittent 200/500 during readiness,
three consecutive MCP initializations; later health 200, SDK initialize success,
status call ~1 second later HTTP 404 JSON-RPC -32001 session not found or expired.
Read-only isolated comparison run #272: raw initialize->initialized->status:
3 PASS/3 FAIL. SDK connect->status: 1 PASS/5 FAIL. One SDK request reported
container not listening on TCP 10.0.0.1:5199. Upstream OpenChatCut pinned commit
d1af1ade45521e8ed9a5be09e3acad823f269453 stores MCP sessions in process Map
and calls forgetSession on transport.onclose; idle limit 60min, cap 64.
Worker /_factory/health answers without contacting the container.
No cloudflare lifecycle stop/exit logs available yet.
Public similar issues: Cloudflare containers #139, #232; MCP SDK #1852.
Distinguish observation from hypothesis; raw failures rule out GET-stream-only explanation.
"""
SYSTEM = ("Act as an independent reliability engineer. Return JSON object with keys "
          "hypotheses (array of {cause,evidence_against,evidence_for}), "
          "next_isolated_test, safe_mitigation, unknowns. Keep under 900 tokens. "
          "No invented logs, no automatic code edits, no secret requests.")
def redact(text):
    text = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", str(text))
    text = re.sub(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", text)
    return text[:10000]

def query(name, cfg, question, transport=requests.post):
    key = os.environ.get(cfg["api_key_env"], "")
    if not key:
        return {"provider":name,"state":"SKIPPED_NO_KEY"}
    model = cfg["models"].get("reasoning") or cfg["models"].get("default")
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    try:
        result = transport(url,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},
             json={"model":model,"temperature":0.1,"max_tokens":950,
                   "messages":[{"role":"system","content":SYSTEM},
                               {"role":"user","content":EVIDENCE+"\nQUESTION: "+question}]},
             timeout=45)
        if result.status_code != 200:
            return {"provider":name,"state":"HTTP_ERROR","http_status":result.status_code}
        msg=result.json()["choices"][0]["message"]["content"]
        return {"provider":name,"state":"REVIEW","review":redact(msg),"model":model}
    except Exception as exc:
        return {"provider":name,"state":"ERROR","type":type(exc).__name__}

def run(question, config, names=PROVIDERS):
    configs=config["providers"]
    selected=[n for n in names if n in configs]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={n:pool.submit(query,n,configs[n],question) for n in selected}
        return [futures[n].result() for n in selected]

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--question",default="Which isolated test most reliably separates Cloudflare restart/proxy from SDK session lifecycle?")
    ap.add_argument("--output",default="")
    args=ap.parse_args()
    results=run(args.question,json.loads(CONFIG.read_text(encoding="utf-8")))
    summary={"schema":"OPENCHATCUT-ADVISORY-REVIEW-V1","source":"sanitized static run #67/#272 evidence",
             "advisory_only":True,"results":results}
    output=json.dumps(summary,ensure_ascii=False,indent=2)
    if args.output:
        Path(args.output).write_text(output,encoding="utf-8")
    else: print(output)
    if not any(x["state"]=="REVIEW" for x in results): raise SystemExit("No available model returned a review")
