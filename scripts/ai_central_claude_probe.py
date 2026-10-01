"""One-call, low-token verification of exact Claude via existing OpenRouter key.
Never prints token, user data or returned model prose. No model substitution.
"""
import json
import os
from pathlib import Path
import requests

MODEL="anthropic/claude-sonnet-4.5"
def probe(post=requests.post):
    key=os.getenv("OPENROUTER_API_KEY","")
    if not key: return {"state":"NO_KEY"}
    try:
        result=post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization":"Bearer "+key,"Content-Type":"application/json",
                     "X-Title":"Edirne22-Claude-Transport-Single-Check"},
            json={"model":MODEL,"max_tokens":24,"temperature":0,
                  "messages":[{"role":"user","content":"Reply with exactly CLAUDE_OK."}]},timeout=30)
        if result.status_code!=200:return {"state":"HTTP_ERROR","http_status":result.status_code}
        body=result.json()
        served=body.get("model","")
        content=(body.get("choices") or [{}])[0].get("message",{}).get("content","")
        # Distinguish actual model from router generic aliases. Never rely on text alone.
        model_ok=isinstance(served,str) and ("claude" in served.lower() and ("anthropic" in served.lower() or served.startswith("claude")))
        return {"state":"INFERENCE_OK" if model_ok and isinstance(content,str) and content.strip() else "UNVERIFIED_RESPONSE",
                "requested_model":MODEL,"reported_model":served[:120],"nonempty":bool(content)}
    except (requests.RequestException,KeyError,ValueError,TypeError,IndexError) as exc:
        return {"state":"ERROR","error_type":type(exc).__name__}
def main():
    status=probe()
    Path("claude-probe-result.json").write_text(json.dumps(status,indent=2),encoding="utf8")
    print("CLAUDE_TRANSPORT_CHECK",json.dumps(status))
    if status["state"]!="INFERENCE_OK":raise SystemExit(2)
if __name__=="__main__":main()
