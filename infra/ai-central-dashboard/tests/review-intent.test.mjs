import test from "node:test";
import assert from "node:assert/strict";
import {randomUUID} from "node:crypto";
import worker from "../src/index.js";
const token="test-dashboard-owner-secret-key-long-enough";
function setup() {
 const id=randomUUID(),job=randomUUID(),manifest="a".repeat(64);
 const current=new Map();
 let serial=0;
 const store={
   async get(k){return current.get(k)||null},
   async put(k,data,{onlyIf}={}){
     if(!onlyIf?.etagMatches||onlyIf.etagMatches!==current.get(k)?.etag)return null;
     const entry={etag:"v"+(++serial),json:async()=>JSON.parse(data)};
     current.set(k,entry);return entry;
   }
 };
 function seed(k,d){current.set(k,{etag:"v"+(++serial),json:async()=>d});}
 seed("ai-central/v1/previews/"+id+".json",{
  schema:"FACTORY-MEDIA-PREVIEW-V1",preview_id:id,job_id:job,revision:1,manifest,
  expires_at:new Date(Date.now()+3600000).toISOString(),state:"READY_FOR_HUMAN",
  qm_passed:true,caption:"Test",media:{media_id:randomUUID(),key:"media/"+randomUUID()+"/video.mp4",
  size_bytes:19,mime_type:"video/mp4",sha256:"b".repeat(64)}
 });
 const stateKey="ai-central/v1/preview-state/"+job+".json";
 seed(stateKey,{schema:"FACTORY-PREVIEW-STATE-V1",job_id:job,preview_id:id,revision:1,manifest,state:"READY_FOR_HUMAN"});
 const env={AI_DASHBOARD_TOKEN:token,AI_CENTRAL_R2:store,ASSETS:{fetch:async()=>new Response("static")}};
 async function submit(overrides={},auth=token){
  return worker.fetch(new Request("https://test.invalid/api/preview-review",{
   method:"POST",headers:{authorization:"Bearer "+auth,"content-type":"application/json"},
   body:JSON.stringify({action:"change",preview_id:id,request_id:randomUUID(),
    manifest,revision:1,text:"Change caption please",...overrides})}),env);
 }
 return {submit,current,stateKey};
}
test("owner change stages a review intent and revokes preview",async()=>{
 const t=setup(),res=await t.submit();assert.equal(res.status,202);
 assert.equal((await res.json()).status,"PENDING_FACTORY_APPLICATION");
 const state=await t.current.get(t.stateKey).json();
 assert.equal(state.state,"REVIEW_REQUESTED");assert.equal(state.preview_id,null);
});
test("post never publishes without canonical factory authority",async()=>{
 const t=setup();assert.equal((await t.submit({action:"post",text:""})).status,409);
 assert.equal((await t.current.get(t.stateKey).json()).state,"READY_FOR_HUMAN");
});
test("stale, invalid actor or tampered preview never mutates state",async()=>{
 const t=setup();
 assert.equal((await t.submit({revision:5})).status,409);
 assert.equal((await t.submit({manifest:"f".repeat(64)})).status,409);
 assert.equal((await t.submit({},"not-valid-owner")).status,401);
 assert.equal((await t.current.get(t.stateKey).json()).state,"READY_FOR_HUMAN");
});
test("concurrent decisions: exactly one recorded",async()=>{
 const t=setup(),results=await Promise.all([t.submit(),t.submit({action:"discard",text:""})]);
 assert.deepEqual(results.map(v=>v.status).sort(),[202,409]);
});
