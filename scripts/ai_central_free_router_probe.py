"""One-off NO-PAID-MODEL check: OpenRouter guarantees openrouter/free has $0 token prices.
Never retries, never logs credentials or model output. Verifies actual responding model.
"""
import json
import os
import requests

MODEL="openrouter/free"
def probe(post=requests.post):
    key=os.environ.get("OPENROUTER_API_KEY","")
    if not key:return {"status":"NO_KEY"}
    try:
        r=post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization":"Bearer "+key,"Content-Type":"application/json",
              "X-Title":"Edirne22 zero-price-model check"},
            json={"model":MODEL,"max_tokens":20,"temperature":0,
              "messages":[{"role":"user","content":"Answer only FREE_OK."}]},
            timeout=25)
        if r.status_code!=200:return {"status":"HTTP_ERROR","http_status":r.status_code}
        result=r.json()
        actual=result.get("model")
        content=(result.get("choices") or [{}])[0].get("message",{}).get("content")
        return {"status":"INFERENCE_OK" if isinstance(actual,str) and isinstance(content,str) and bool(content.strip()) else "UNVERIFIED_RESPONSE",
                "requested_model":MODEL,"actual_model":str(actual)[:130],
                "nonempty":bool(content)}
    except (requests.RequestException,ValueError,KeyError,IndexError,TypeError) as exc:
        return {"status":"ERROR","error_type":type(exc).__name__}
if __name__=="__main__":
    result=probe()
    print("FREE_ROUTER_PROBE",json.dumps(result))
    if result["status"]!="INFERENCE_OK":raise SystemExit(2)
