"""Small read-only provider inventory. No inference calls and no credential logging."""
import json, os, requests
from pathlib import Path
CONFIG=Path(__file__).resolve().parents[1]/"config"/"llm_providers.json"
NAMES=("nvidia","groq","openrouter")
FILTER=("qwen","claude","kimi","minimax","nemotron","gpt-oss")
def scan_one(name,cfg,transport=requests.get):
    key=os.environ.get(cfg["api_key_env"],"")
    if not key:return {"provider":name,"state":"SKIPPED_NO_KEY","models":[]}
    try:
        result=transport(cfg["base_url"].rstrip("/")+"/models",
            headers={"Authorization":"Bearer "+key},timeout=12)
        if result.status_code!=200:
            return {"provider":name,"state":"HTTP_ERROR","http_status":result.status_code,"models":[]}
        data=result.json().get("data",[])
        names=sorted({str(x["id"]) for x in data if isinstance(x,dict) and
            isinstance(x.get("id"),str) and any(term in x["id"].lower() for term in FILTER)})
        return {"provider":name,"state":"CATALOG_OK","matched_count":len(names),
             "models":names[:60],"truncated":len(names)>60}
    except (requests.RequestException, ValueError, TypeError) as exc:
        return {"provider":name,"state":"ERROR","type":type(exc).__name__,"models":[]}
if __name__=="__main__":
    cfg=json.loads(CONFIG.read_text(encoding="utf-8"))["providers"]
    out={"schema":"CLOUD-MODEL-INVENTORY-V1",
         "note":"Catalog listing does not prove model inference access, cost or reliability",
         "providers":[scan_one(name,cfg[name]) for name in NAMES]}
    Path("cloud-model-inventory.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"states":[{"provider":x["provider"],"state":x["state"],
        "matched_count":x.get("matched_count",0)} for x in out["providers"]]}))
