import test from "node:test";
import assert from "node:assert/strict";
import {randomBytes,randomUUID,createHash} from "node:crypto";
import worker from "../src/index.js";
const enc=new TextEncoder(),decode=new TextDecoder();
const sha=b=>createHash("sha256").update(b).digest("hex");
function record(content,{contentType="application/json",metadata={}}={}){
 const buf=content instanceof Uint8Array?content:enc.encode(content);
 return {size:buf.byteLength,httpMetadata:{contentType},customMetadata:metadata,
  json:async()=>JSON.parse(decode.decode(buf)),arrayBuffer:async()=>buf.slice().buffer};
}
function fixture(){
 const objects=new Map(),job_id=randomUUID(),media_id=randomUUID(),id=randomUUID();
 const token=randomBytes(32).toString("base64url"),manifest="a".repeat(64),request_id=randomUUID();
 const bytes=enc.encode("tiny harmless mock binary media, not a real video");
 const key=`media/${media_id}/verified.mp4`,digest=sha(bytes);
 const issued_at=new Date(Date.now()-15000).toISOString(),expires_at=new Date(Date.now()+3600000).toISOString();
 const handoff_key=`${job_id}:r1:${manifest.slice(0,16)}`;
 const job={job_id,revision:1,status:"publish_queued",instruction:"original editorial video",
  human_approved_at:issued_at,human_approved_revision:1,human_approved_manifest:manifest,publish_handoff_key:handoff_key,
  publish_payload:{caption:"Fully reviewed owner editorial",
    editorial_evidence:{source_fact_contract:true,human_writing:true,media_rights:true,synthetic:false,final_qm_report_id:"real-report"}},
  metadata:{"human_post:r1":{actor:"authenticated_dashboard_owner",revision:1,manifest,request_id}},
  media:[{media_id,uri:`r2://private-bucket/${key}`,sha256:digest,size_bytes:bytes.length,mime_type:"video/mp4",provenance:"verified"}]};
 const grant={schema:"META-PRIVATE-R2-DELIVERY-V1",id,job_id,media_id,key,sha256:digest,
  size_bytes:bytes.length,mime_type:"video/mp4",approval_manifest:manifest,handoff_key,
  token_sha256:sha(token),issued_at,expires_at};
 const grantkey=`ai-central/v1/meta-delivery/grants/${id}.json`;
 const canonicalkey=`ai-central/v1/factory-jobs/${job_id}.json`;
 objects.set(grantkey,record(JSON.stringify(grant)));
 objects.set(canonicalkey,record(JSON.stringify({schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id,job,store_version:3})));
 objects.set(key,record(bytes,{contentType:"video/mp4",metadata:{sha256:digest,"media-id":media_id}}));
 const env={AI_DASHBOARD_TOKEN:"private-dashboard-token-xyz",AI_CENTRAL_R2:{
   objects,async get(k){return objects.get(k)||null}},ASSETS:{fetch:async()=>new Response("ui")}};
 const path=`/api/meta-delivery?id=${id}&token=${token}`;
 const req=(url=path,method="GET")=>new Request("https://dashboard.example"+url,{method});
 const set=(k,data)=>objects.set(k,record(JSON.stringify(data)));
 return {objects,env,job,grant,bytes,key,grantkey,canonicalkey,id,token,path,req,set};
}
test("valid short capability serves exact private bytes to Meta without Dashboard Bearer header",async()=>{
 const x=fixture();let r=await worker.fetch(x.req(),x.env);
 assert.equal(r.status,200);assert.equal(r.headers.get("content-type"),"video/mp4");
 assert.match(r.headers.get("cache-control"),/no-store/);
 assert.deepEqual(new Uint8Array(await r.arrayBuffer()),x.bytes);
 r=await worker.fetch(x.req(x.path,"HEAD"),x.env);
 assert.equal(r.status,200);assert.equal(r.headers.get("content-length"),String(x.bytes.length));
 assert.equal((await r.arrayBuffer()).byteLength,0);
});
test("unknown, forged, expired and reused foreign capability never leaks bytes",async()=>{
 const x=fixture();
 assert.equal((await worker.fetch(x.req("/api/meta-delivery?id="+x.id+"&token="+randomBytes(32).toString("base64url")),x.env)).status,404);
 assert.equal((await worker.fetch(x.req(x.path+"&key="+encodeURIComponent(x.key)),x.env)).status,404);
 assert.equal((await worker.fetch(x.req("/api/meta-delivery?id=../../etc&token="+x.token),x.env)).status,404);
 x.set(x.grantkey,{...x.grant,expires_at:new Date(Date.now()-1).toISOString()});
 assert.equal((await worker.fetch(x.req(),x.env)).status,410);
});
test("revoked owner approval, revised media and synthetic test cannot fetch",async()=>{
 const x=fixture();
 x.set(x.canonicalkey,{schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id:x.job.job_id,
   job:{...x.job,status:"changes_requested"},store_version:4});
 assert.equal((await worker.fetch(x.req(),x.env)).status,404);
 x.set(x.canonicalkey,{schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id:x.job.job_id,
   job:{...x.job,metadata:{...x.job.metadata,technical_test_only:true}},store_version:4});
 assert.equal((await worker.fetch(x.req(),x.env)).status,404);
 x.set(x.canonicalkey,{schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id:x.job.job_id,
   job:{...x.job,media:[{...x.job.media[0],sha256:"f".repeat(64)}]},store_version:4});
 assert.equal((await worker.fetch(x.req(),x.env)).status,404);
});
test("missing bytes, tampered media, metadata mismatch and stale approval fail shut",async()=>{
 const x=fixture();
 x.objects.delete(x.key);assert.equal((await worker.fetch(x.req(),x.env)).status,404);
 x.objects.set(x.key,record(enc.encode("tampered"),{contentType:"video/mp4",
   metadata:{sha256:x.grant.sha256,"media-id":x.grant.media_id}}));
 assert.equal((await worker.fetch(x.req(),x.env)).status,404);
 x.objects.set(x.key,record(x.bytes,{contentType:"video/mp4",metadata:{sha256:"f".repeat(64),
    "media-id":x.grant.media_id}}));
 assert.equal((await worker.fetch(x.req(),x.env)).status,404);
 x.set(x.canonicalkey,{schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id:x.job.job_id,
   job:{...x.job,human_approved_manifest:"b".repeat(64)},store_version:4});
 assert.equal((await worker.fetch(x.req(),x.env)).status,404);
});
test("POST and malformed grants cannot issue public URLs or publish",async()=>{
 const x=fixture();
 assert.equal((await worker.fetch(x.req(x.path,"POST"),x.env)).status,405);
 x.set(x.grantkey,{...x.grant,key:"../secret.mp4"});
 assert.equal((await worker.fetch(x.req(),x.env)).status,404);
 const y=fixture();
 y.set(y.grantkey,{...y.grant,size_bytes:80*1024*1024});
 assert.equal((await worker.fetch(y.req(),y.env)).status,404);
});
