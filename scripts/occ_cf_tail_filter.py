"""Filter Cloudflare live tail JSON to non-sensitive lifecycle events only."""
import json,sys
ALLOWED=("openchatcut_readiness_wait","openchatcut_readiness_ready",
         "openchatcut_container_start","openchatcut_container_stop",
         "openchatcut_container_error","openchatcut_proxy")
KEEP=("event","method","path","durationMs","exitCode","reason","error","port","at","workerBootId")
count=0
invocations=0
for line in sys.stdin:
    if len(line)>500000:continue
    try:packet=json.loads(line)
    except ValueError:continue
    if isinstance(packet,dict) and isinstance(packet.get('event'),dict):
        from urllib.parse import urlparse
        req=packet.get('event',{}).get('request',{}) or {}
        res=packet.get('event',{}).get('response',{}) or {}
        print('CF_TAIL_EVENT',json.dumps({'outcome':str(packet.get('outcome',''))[:50], 'method':str(req.get('method',''))[:12], 'path':urlparse(str(req.get('url',''))).path[:100], 'status':res.get('status')}),flush=True)
        invocations+=1
    entries=packet.get("logs",[]) if isinstance(packet,dict) else []
    for entry in entries:
        message=entry.get("message") if isinstance(entry,dict) else None
        # Wrangler JSON documents the console message as an array, not a string.
        parts=message if isinstance(message,list) else [message]
        for raw in parts:
            if not isinstance(raw,str):continue
            try:data=json.loads(raw)
            except ValueError:continue
            if not isinstance(data,dict) or data.get("event") not in ALLOWED:continue
            obj={k:str(data[k])[:180] if isinstance(data[k],str) else data[k] for k in KEEP if k in data}
            print("CF_LIFECYCLE",json.dumps(obj),flush=True)
            count+=1
print("CF_TAIL_INVOCATIONS",invocations,flush=True)
print("CF_LIFECYCLE_EVENT_COUNT",count,flush=True)
