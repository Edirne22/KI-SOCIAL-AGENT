"""Read-only hosted capability/secret-presence inventory; no model inference or writes to repo.

Only print model identifiers and status. Never print API credentials or private config.
Results are dated R2 artifacts. GitHub Actions passes only listed secret names.
"""
import json
import os
import re
import datetime
from pathlib import Path
import requests

SECRET_NAMES=("NVIDIA_API_KEY","GROQ_API_KEY","GEMINI_API_KEY","OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY","AGNES_API_KEY","TOGETHER_API_KEY","POLLINATIONS_API_KEY",
    "CLOUDFLARE_API_TOKEN","CLOUDFLARE_ACCOUNT_ID","R2_BUCKET_NAME")
ROOT=Path(__file__).resolve().parents[1]
FILTER=("qwen","claude","kimi","minimax","nemotron","gemini","imagen","veo",
        "flux","whisper","audio","image","video","gpt")
VALID=re.compile(r"^[a-zA-Z0-9@._/:-]{1,150}$")

def sanitize_ids(rows):
    ids=sorted({v for v in rows if isinstance(v,str) and VALID.fullmatch(v) and
                any(s in v.lower() for s in FILTER)})
    return {"matching_models":ids[:180],"count":len(ids),"truncated":len(ids)>180}

def inventory_one(provider,key,fetch=requests.get):
    if not key:return {"provider":provider,"state":"NO_KEY"}
    if provider=="nvidia":base="https://integrate.api.nvidia.com/v1/models";headers={"Authorization":"Bearer "+key}
    elif provider=="groq":base="https://api.groq.com/openai/v1/models";headers={"Authorization":"Bearer "+key}
    elif provider=="openrouter":base="https://openrouter.ai/api/v1/models";headers={"Authorization":"Bearer "+key}
    elif provider=="google":base="https://generativelanguage.googleapis.com/v1beta/models?pageSize=100";headers={"x-goog-api-key":key}
    elif provider=="anthropic":base="https://api.anthropic.com/v1/models?limit=100";headers={"x-api-key":key,"anthropic-version":"2023-06-01"}
    else:return {"provider":provider,"state":"NOT_SUPPORTED"}
    ids=[]
    try:
        # Bound pagination to 3 pages; model inventory only, no inference.
        for _ in range(3):
            response=fetch(base,headers=headers,timeout=18)
            if response.status_code!=200:
                return {"provider":provider,"state":"HTTP_ERROR","status":response.status_code}
            doc=response.json()
            if not isinstance(doc,dict):raise ValueError("invalid catalog response")
            rows=doc.get("models",[]) if provider=="google" else doc.get("data",[])
            ids.extend(x.get("name" if provider=="google" else "id","") for x in rows if isinstance(x,dict))
            nxt=doc.get("nextPageToken") if provider=="google" else None
            if not nxt:break
            if not VALID.fullmatch(nxt):raise ValueError("bad pagination token")
            base="https://generativelanguage.googleapis.com/v1beta/models?pageSize=100&pageToken="+nxt
        return {"provider":provider,"state":"CATALOG_OK",**sanitize_ids(ids)}
    except (requests.RequestException,ValueError,TypeError) as exc:
        return {"provider":provider,"state":"ERROR","type":type(exc).__name__}

def main():
    pairs=[("google","GEMINI_API_KEY"),("nvidia","NVIDIA_API_KEY"),
           ("groq","GROQ_API_KEY"),("openrouter","OPENROUTER_API_KEY"),
           ("anthropic","ANTHROPIC_API_KEY")]
    output={"schema":"AI-CAPABILITY-INVENTORY-V1",
        "created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "warning":"catalog visibility does not prove inference, license, pricing, or available quota",
        "secret_presence":{n:bool(os.getenv(n)) for n in SECRET_NAMES},
        "catalog":[inventory_one(n,os.getenv(s,"")) for n,s in pairs]}
    Path("ai-capability-inventory.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"schema":output["schema"],"presence":output["secret_presence"],
          "catalog_summary":[{"provider":x["provider"],"state":x["state"],"matches":x.get("count",0)}
                             for x in output["catalog"]]},ensure_ascii=False))

if __name__=="__main__":main()
