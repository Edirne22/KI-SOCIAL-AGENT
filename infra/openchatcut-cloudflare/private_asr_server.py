"""Private one-shot ASR endpoint bound to existing authenticated Cloudflare Container proxy."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_POST(self):
        if self.path != "/internal/private-asr" or self.headers.get("X-Internal-ASR-Token") != os.getenv("OPENCHATCUT_MCP_TOKEN", "") or not os.getenv("OPENCHATCUT_MCP_TOKEN"):
            self.send_error(404)
            return
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0 < length <= 1024: raise ValueError()
            body=json.loads(self.rfile.read(length))
            if set(body)!={"id","date","language"}: raise ValueError()
            import re
            if not re.fullmatch(r"[0-9a-f-]{36}",body["id"]) or not re.fullmatch(r"20\d\d-\d\d-\d\d",body["date"]) or body["language"] not in ("de","tr"): raise ValueError()
            import boto3
            from content_factory_private_asr_r2_bridge import run_private_r2_asr
            client=boto3.client("s3",endpoint_url="https://"+os.environ["R2_ACCOUNT_ID"]+".r2.cloudflarestorage.com",aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
            result=run_private_r2_asr(client,os.environ["R2_BUCKET_NAME"],body["id"],body["date"],body["language"],model_dir=os.environ["EDIRNE22_LOCAL_WHISPER_MODEL"])
            response={"status":result["status"]}
            code=200
        except Exception as exc:
            response={"status":"PRIVATE_ASR_REJECTED","error_type":type(exc).__name__}
            code=400
        raw=json.dumps(response).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

if __name__=="__main__":
    ThreadingHTTPServer(("127.0.0.1",5200),Handler).serve_forever()
