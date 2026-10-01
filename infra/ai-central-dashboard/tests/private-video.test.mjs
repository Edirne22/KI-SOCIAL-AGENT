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
  job_id:randomUUID(),revision:1,manifest:"a".repeat(64),caption:"Buelent's private reel",
  media:{media_id:randomUUID(),key,mime_type:"video/mp4",size_bytes:bytes.length,sha256:sha},...options};
 e.AI_CENTRAL_R2.objects.set("ai-central/v1/previews/"+id+".json",item(JSON.stringify(doc)));
 e.AI_CENTRAL_R2.objects.set(key,item(bytes,{metadata:{sha256:sha}}));
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
