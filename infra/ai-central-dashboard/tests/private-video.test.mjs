import test from "node:test";
import assert from "node:assert/strict";
import {createHash,randomUUID} from "node:crypto";
import worker from "../src/index.js";

const TOKEN="unit-test-long-dashboard-token-xyz";
const enc=new TextEncoder();
function mockR2(){
 const objects=new Map();
 return {
  objects,
  async list({prefix}){return {objects:[...objects.keys()].filter(key=>key.startsWith(prefix)).map(key=>({key})),truncated:false}},
  async get(key){return objects.get(key)||null}
 };
}
function item(raw,{metadata={},mime="video/mp4"}={}){
 const body=raw instanceof Uint8Array?raw:enc.encode(raw);
 return {size:body.byteLength,httpMetadata:{contentType:mime},customMetadata:metadata,
   async arrayBuffer(){return body.slice().buffer},
   async json(){return JSON.parse(new TextDecoder().decode(body))}
 };
}
function env(){return {AI_DASHBOARD_TOKEN:TOKEN,AI_CENTRAL_R2:mockR2(),ASSETS:{fetch:async()=>new Response("ui")}}}
function req(url,token=TOKEN){return new Request("https://dashboard.example"+url,{headers:token?{authorization:"Bearer "+token}:{}})}
function seed(e,options={}){
 const id=randomUUID(),bytes=enc.encode("video binary stand-in");
 const sha=createHash("sha256").update(bytes).digest("hex");
 const key="content-factory/"+randomUUID()+"/approved.mp4";
 const doc={schema:"FACTORY-MEDIA-PREVIEW-V1",preview_id:id,state:"READY_FOR_HUMAN",qm_passed:true,
  expires_at:new Date(Date.now()+60*60*1000).toISOString(),
  job_id:randomUUID(),revision:1,manifest:"a".repeat(64),caption:"Buelent's private reel",
  media:{media_id:randomUUID(),key,mime_type:"video/mp4",size_bytes:bytes.length,sha256:sha},...options};
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/previews/"+id+".json",item(JSON.stringify(doc)));
 e.AI_CENTRAL_R2.objects.set(key,item(bytes,{metadata:{sha256:sha}}));
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/factory-jobs/"+doc.job_id+".json",
   item(JSON.stringify({schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id:doc.job_id,store_version:1,
     job:{job_id:doc.job_id,revision:doc.revision,status:"ready_for_human",
       publish_payload:{caption:doc.caption},media:[{...doc.media,uri:"r2://private-test/"+doc.media.key}]}})));
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/preview-state/"+doc.job_id+".json",item(JSON.stringify({
   schema:"FACTORY-PREVIEW-STATE-V1",job_id:doc.job_id,preview_id:id,
   revision:doc.revision,manifest:doc.manifest,state:"READY_FOR_HUMAN"
 })));
 return {id,doc,bytes,key};
}
test("anonymous cannot list or fetch private video",async()=>{
 const e=env(),{id}=seed(e);
 assert.equal((await worker.fetch(req("/api/previews",""),e)).status,401);
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id,"wrong"),e)).status,401);
});
test("authorized index and verified private bytes are playable",async()=>{
 const e=env(),{id,bytes}=seed(e);
 const list=await worker.fetch(req("/api/previews"),e);
 assert.equal(list.status,200);assert.equal((await list.json()).items[0].id,id);
 const response=await worker.fetch(req("/api/preview-video?id="+id),e);
 assert.equal(response.status,200);assert.equal(response.headers.get("content-type"),"video/mp4");
 assert.match(response.headers.get("cache-control"),/no-store/);
 assert.deepEqual(new Uint8Array(await response.arrayBuffer()),bytes);
});
test("tampered R2 body never leaves server",async()=>{
 const e=env(),{id,key}=seed(e);
 const correct=e.AI_CENTRAL_R2.objects.get(key);
 e.AI_CENTRAL_R2.objects.set(key,{...correct,async arrayBuffer(){return enc.encode("video binary stand-in altered").buffer}});
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,409);
});
test("missing/mismatched metadata blocks playback",async()=>{
 const e=env(),{id,key}=seed(e);
 const old=e.AI_CENTRAL_R2.objects.get(key);
 e.AI_CENTRAL_R2.objects.set(key,{...old,customMetadata:{sha256:"0".repeat(64)}});
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,409);
 e.AI_CENTRAL_R2.objects.delete(key);
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
});
test("unapproved manifest is hidden and direct R2 key cannot be requested",async()=>{
 const e=env(),{id,doc}=seed(e);
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/previews/"+id+".json",
   item(JSON.stringify({...doc,state:"RENDERING"})));
 assert.equal((await (await worker.fetch(req("/api/previews"),e)).json()).items.length,0);
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
 assert.equal((await worker.fetch(req("/api/preview-video?id=content-factory/foo.mp4"),e)).status,400);
});
test("oversized or fake MIME manifest never appears",async()=>{
 const e=env(),{id,doc}=seed(e);
 for(const media of [{...doc.media,size_bytes:64*1024*1024},{...doc.media,mime_type:"text/html"}]){
  e.AI_CENTRAL_R2.objects.set("ai-central/v1/previews/"+id+".json",
    item(JSON.stringify({...doc,media})));
  assert.equal((await (await worker.fetch(req("/api/previews"),e)).json()).items.length,0);
 }
});

test("revoked preview hidden and video cannot be replayed",async()=>{
 const e=env(),{id,doc}=seed(e);
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/preview-state/"+doc.job_id+".json",item(JSON.stringify({
   schema:"FACTORY-PREVIEW-STATE-V1",job_id:doc.job_id,preview_id:null,
   revision:doc.revision,manifest:doc.manifest,state:"REVOKED"
 })));
 assert.equal((await (await worker.fetch(req("/api/previews"),e)).json()).items.length,0);
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
});
test("superseded preview JSON cannot authorize an old video",async()=>{
 const e=env(),{id,doc}=seed(e);
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/preview-state/"+doc.job_id+".json",item(JSON.stringify({
   schema:"FACTORY-PREVIEW-STATE-V1",job_id:doc.job_id,preview_id:randomUUID(),
   revision:doc.revision+1,manifest:"b".repeat(64),state:"READY_FOR_HUMAN"
 })));
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
});
test("expired and missing state pointers fail closed",async()=>{
 const e=env(),{id,doc}=seed(e);
 const path="ai-central/v1/previews/"+id+".json";
 e.AI_CENTRAL_R2.objects.set(path,item(JSON.stringify({...doc,
   expires_at:new Date(Date.now()-1000).toISOString()})));
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
 e.AI_CENTRAL_R2.objects.set(path,item(JSON.stringify(doc)));
 e.AI_CENTRAL_R2.objects.delete("ai-central/v1/preview-state/"+doc.job_id+".json");
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
});

test("canonical job disappears: old preview pointer cannot show stale video",async()=>{
 const e=env(),{id,doc}=seed(e);
 e.AI_CENTRAL_R2.objects.delete("ai-central/v1/factory-jobs/"+doc.job_id+".json");
 assert.equal((await (await worker.fetch(req("/api/previews"),e)).json()).items.length,0);
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
});
test("canonical job rejected or revised: stale pointer never authorizes media",async()=>{
 const e=env(),{id,doc}=seed(e),key="ai-central/v1/factory-jobs/"+doc.job_id+".json";
 const saved=await e.AI_CENTRAL_R2.objects.get(key).json();
 for(const change of [{status:"rejected"},{revision:2}]){
   e.AI_CENTRAL_R2.objects.set(key,item(JSON.stringify({...saved,job:{...saved.job,...change}})));
   assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
 }
});
test("canonical media SHA, caption or media ID mismatch fail closed",async()=>{
 const e=env(),{id,doc}=seed(e),key="ai-central/v1/factory-jobs/"+doc.job_id+".json";
 const saved=await e.AI_CENTRAL_R2.objects.get(key).json();
 for(const change of [
   {media:[{...saved.job.media[0],sha256:"f".repeat(64)}]},
   {media:[{...saved.job.media[0],media_id:randomUUID()}]},
   {publish_payload:{caption:"silently edited caption"}}
 ]){
   e.AI_CENTRAL_R2.objects.set(key,item(JSON.stringify({...saved,job:{...saved.job,...change}})));
   assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
 }
});
test("unreadable canonical job is never treated as an authorized preview",async()=>{
 const e=env(),{id,doc}=seed(e);
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/factory-jobs/"+doc.job_id+".json",item("{broken json"));
 assert.equal((await worker.fetch(req("/api/preview-video?id="+id),e)).status,404);
});
