"""Agent 21 read-only runtime diagnostic report builder."""
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
ALLOWED_STATES={"success","failure","skipped","cancelled","unknown","in_progress","queued","waiting"}
def build_report(data:dict)->dict:
    def clean(v,n=160):
        return str(v or "unknown").replace("\n"," ").replace("\r"," ")[:n]
    state=clean(data.get("state"),32).lower()
    if state not in ALLOWED_STATES: state="unknown"
    return {"schema":"AGENT21-RUNTIME-DIAG-V1","agent":21,"mode":"READ_ONLY",
      "timestamp":datetime.now(timezone.utc).isoformat(),"run_id":clean(data.get("run_id"),40),
      "commit":clean(data.get("commit"),64),"machine":clean(data.get("machine"),80),
      "route":clean(data.get("route"),120),"provider":clean(data.get("provider"),80),
      "state":state,"error_class":clean(data.get("error_class"),120),
      "container_health":clean(data.get("container_health"),40),
      "opencode_health":clean(data.get("opencode_health"),40),"secret_values_logged":False}
if __name__=="__main__":
    print(json.dumps(build_report(json.load(sys.stdin)),ensure_ascii=False,sort_keys=True))
