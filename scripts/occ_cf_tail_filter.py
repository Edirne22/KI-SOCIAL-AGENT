"""Filter Cloudflare live tail JSON to non-sensitive lifecycle events only."""
import json,sys
ALLOWED=("openchatcut_readiness_wait","openchatcut_readiness_ready",
         "openchatcut_container_start","openchatcut_container_stop",
         "openchatcut_container_error","openchatcut_proxy")
KEEP=("event","method","path","durationMs","exitCode","reason","error","port","at","workerBootId")
count=0
for line in sys.stdin:
    if len(line)>500000:continue
    try:packet=json.loads(line)
    except ValueError:continue
    entries=packet.get("logs",[]) if isinstance(packet,dict) else []
    for entry in entries:
        message=entry.get("message") if isinstance(entry,dict) else None
        if not isinstance(message,str):continue
        try:data=json.loads(message)
        except ValueError:continue
        if data.get("event") not in ALLOWED:continue
        obj={k:str(data[k])[:180] if isinstance(data[k],str) else data[k] for k in KEEP if k in data}
        print("CF_LIFECYCLE",json.dumps(obj),flush=True)
        count+=1
print("CF_LIFECYCLE_EVENT_COUNT",count,flush=True)
