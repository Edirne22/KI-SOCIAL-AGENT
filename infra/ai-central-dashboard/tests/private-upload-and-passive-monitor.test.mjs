import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

const TOKEN="unit-test-long-dashboard-token-xyz";
const ORIGIN="https://dashboard.example";
function mockBucket(){
  const items=new Map(),flags={forceTruncated:false,lists:0};
  return {
    items,flags,
    async put(key,value,opt={}){
      const bytes=typeof value==="string"?new TextEncoder().encode(value):new Uint8Array(value);
      items.set(key,{bytes,contentType:opt.httpMetadata?.contentType||""});
      return {etag:"mock"};
    },
    async get(key){
      const o=items.get(key);
      if(!o)return null;
      return {
        size:o.bytes.byteLength,httpMetadata:{contentType:o.contentType},
        json:async()=>JSON.parse(new TextDecoder().decode(o.bytes)),
        arrayBuffer:async()=>o.bytes.slice().buffer
      };
    },
    async list({prefix="",limit=1000,cursor}={}){
      flags.lists++;
      if(flags.forceTruncated)return {objects:[{key:"incomplete",size:4}],truncated:true,cursor:"cannot-progress"};
      const keys=[...items.keys()].filter(k=>k.startsWith(prefix)).sort();
      const start=cursor?Number(cursor):0;
      const page=keys.slice(start,start+limit);
      return {objects:page.map(key=>({key,size:items.get(key).bytes.byteLength})),
        truncated:start+limit<keys.length,
        cursor:start+limit<keys.length?String(start+limit):undefined};
    }
  };
}
function env(){return {AI_DASHBOARD_TOKEN:TOKEN,AI_CENTRAL_R2:mockBucket(),
  ASSETS:{fetch:async()=>new Response("ui")}}}
function request(path,{token=TOKEN,method="GET",body,headers={}}={}){
  return new Request(ORIGIN+path,{method,body,headers:{
    ...(token?{authorization:"Bearer "+token}:{}),...headers}});
}
async function upload(e,mime,bytes){
  const response=await worker.fetch(request("/api/upload",{
    method:"POST",body:bytes,headers:{"content-type":mime,
      "x-upload-name":mime==="application/pdf"?"proof.pdf":"photo.png",origin:ORIGIN}}),e);
  assert.equal(response.status,202);
  return response.json();
}
test("authenticated private image and PDF bytes work after a fresh independent request",async()=>{
  const e=env();
  const original=Uint8Array.from([137,80,78,71,13,10,26,10,1,2]);
  const item=await upload(e,"image/png",original);
  const date=item.created_at.slice(0,10);
  const url="/api/upload-preview?id="+item.id+"&date="+date;
  const response=await worker.fetch(request(url),e);
  assert.equal(response.status,200);
  assert.equal(response.headers.get("content-type"),"image/png");
  assert.equal(response.headers.get("cache-control"),"private, no-store, max-age=0");
  assert.equal(response.headers.get("x-content-type-options"),"nosniff");
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()),original);
  assert.equal((await worker.fetch(request(url,{token:"wrong"}),e)).status,401);
  const pdf=await upload(e,"application/pdf",new TextEncoder().encode("%PDF-1.4 mock test"));
  const document=await worker.fetch(request("/api/upload-preview?id="+pdf.id+"&date="+date),e);
  assert.equal(document.status,200);
  assert.equal(document.headers.get("content-type"),"application/pdf");
});
test("forged references, invalid date, old key and tampered stored metadata fail closed",async()=>{
  const e=env(),item=await upload(e,"image/png",Uint8Array.from([1,2,3]));
  const date=item.created_at.slice(0,10),url="/api/upload-preview?id="+item.id+"&date="+date;
  assert.equal((await worker.fetch(request("/api/upload-preview?id=../../etc&date="+date),e)).status,400);
  assert.equal((await worker.fetch(request("/api/upload-preview?id="+item.id+"&date=2026-99-99"),e)).status,400);
  assert.equal((await worker.fetch(request("/api/upload-preview?id="+crypto.randomUUID()+"&date="+date),e)).status,404);
  assert.equal((await worker.fetch(request("/api/upload-preview?id="+item.id+"&date=2026-01-01"),e)).status,404);
  const saved=e.AI_CENTRAL_R2.items.get("ai-central/v1/uploads/"+item.id+"/data");
  saved.contentType="text/html";
  assert.equal((await worker.fetch(request(url),e)).status,409);
  saved.contentType="image/png";saved.bytes=Uint8Array.from([1]);
  assert.equal((await worker.fetch(request(url),e)).status,409);
});
test("R2 bucket measurement only upon authenticated manual action and never wakes container",async()=>{
  const e=env();e.R2_FREE_STORAGE_GB="10";
  const old=globalThis.fetch;let externalCalls=0;
  globalThis.fetch=async()=>{externalCalls++;throw Error("must never ping a sleeping container")};
  try{
    assert.equal((await worker.fetch(request("/api/system-monitor?scope=manual",{token:"wrong"}),e)).status,401);
    assert.equal((await worker.fetch(request("/api/system-monitor"),e)).status,400);
    assert.equal(e.AI_CENTRAL_R2.flags.lists,0);
    await e.AI_CENTRAL_R2.put("one",new Uint8Array(100),{httpMetadata:{contentType:"application/octet-stream"}});
    await e.AI_CENTRAL_R2.put("two",new Uint8Array(200),{httpMetadata:{contentType:"application/octet-stream"}});
    const result=await worker.fetch(request("/api/system-monitor?scope=manual"),e);
    assert.equal(result.status,200);
    const d=await result.json();
    assert.equal(d.r2.measurement,"COMPLETE_BUCKET_INVENTORY");
    assert.equal(d.r2.occupied_bytes,300);
    assert.equal(d.r2.object_count,2);
    assert.equal(d.r2.snapshot_ratio,300/(10*1e9));
    assert.equal(d.r2.billing_usage_gb_month,null);
    assert.equal(d.container.status,"UNKNOWN_NO_PASSIVE_TELEMETRY");
    assert.equal(d.container.cpu_percent,null);
    assert.equal(externalCalls,0);
  }finally{globalThis.fetch=old}
});
test("incomplete R2 inventory and unset monthly allowance refuse invented values",async()=>{
  const e=env();
  let d=await (await worker.fetch(request("/api/system-monitor?scope=manual"),e)).json();
  assert.equal(d.r2.allowance_reference_gb,null);
  assert.equal(d.r2.snapshot_ratio,null);
  e.AI_CENTRAL_R2.flags.forceTruncated=true;
  d=await (await worker.fetch(request("/api/system-monitor?scope=manual"),e)).json();
  assert.equal(d.r2.measurement,"UNAVAILABLE_INCOMPLETE_SCAN");
  assert.equal(d.r2.occupied_bytes,null);
  assert.equal(d.r2.measured_at,null);
  assert.equal(d.container.readiness_at,null);
});
test("container passive GET never probes; manual POST explicitly checks configured approved URL",async()=>{
 const e=env(),old=globalThis.fetch;
 let calls=0;
 globalThis.fetch=async()=>{calls++;return {ok:true,status:200}};
 try{
   let response=await worker.fetch(request("/api/container-readiness"),e);
   assert.equal(response.status,200);
   assert.equal((await response.json()).state,"UNAVAILABLE");
   assert.equal(calls,0);
   response=await worker.fetch(request("/api/container-readiness",{method:"POST",headers:{origin:ORIGIN}}),e);
   assert.equal(response.status,503);assert.equal(calls,0);
   e.AI_CONTAINER_READINESS_URL="http://external.invalid/health";
   response=await worker.fetch(request("/api/container-readiness",{method:"POST",headers:{origin:ORIGIN}}),e);
   assert.equal(response.status,503);assert.equal(calls,0);
   e.AI_CONTAINER_READINESS_URL="https://approved.butupeli.workers.dev/health";
   response=await worker.fetch(request("/api/container-readiness",{method:"POST",headers:{origin:"https://attacker.example"}}),e);
   assert.equal(response.status,403);assert.equal(calls,0);
   response=await worker.fetch(request("/api/container-readiness",{method:"POST",token:"invalid",headers:{origin:ORIGIN}}),e);
   assert.equal(response.status,401);assert.equal(calls,0);
   response=await worker.fetch(request("/api/container-readiness",{method:"POST",headers:{origin:ORIGIN}}),e);
   assert.equal(response.status,200);assert.equal((await response.json()).state,"HTTP_REACHABLE_ONLY");
   assert.equal(calls,1);
   response=await worker.fetch(request("/api/container-readiness"),e);
   const last=await response.json();
   assert.equal(last.state,"LAST_KNOWN_HTTP_REACHABLE_NOT_CURRENT");
   assert.ok(Number.isFinite(Date.parse(last.last_success_at)));
   assert.equal(last.cpu_percent,null);
   assert.equal(calls,1);
 }finally{globalThis.fetch=old}
});
test("manual failure never overwrites previously successful last known status",async()=>{
 const e=env(),old=globalThis.fetch;
 e.AI_CONTAINER_READINESS_URL="https://approved.workers.dev/ready";
 let succeed=true;
 globalThis.fetch=async()=>succeed?{ok:true,status:200}:{ok:false,status:503};
 try{
   let response=await worker.fetch(request("/api/container-readiness",{method:"POST",headers:{origin:ORIGIN}}),e);
   assert.equal((await response.json()).state,"HTTP_REACHABLE_ONLY");
   succeed=false;
   response=await worker.fetch(request("/api/container-readiness",{method:"POST",headers:{origin:ORIGIN}}),e);
   assert.equal((await response.json()).state,"HTTP_NOT_READY_OR_UNAVAILABLE");
   response=await worker.fetch(request("/api/container-readiness"),e);
   assert.equal((await response.json()).state,"LAST_KNOWN_HTTP_REACHABLE_NOT_CURRENT");
 }finally{globalThis.fetch=old}
});
