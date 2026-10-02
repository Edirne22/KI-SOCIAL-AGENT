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
 const preview={
  schema:"FACTORY-MEDIA-PREVIEW-V1",preview_id:id,job_id:job,revision:1,manifest,
  expires_at:new Date(Date.now()+3600000).toISOString(),state:"READY_FOR_HUMAN",
  qm_passed:true,caption:"Test",media:{media_id:randomUUID(),key:"media/"+randomUUID()+"/video.mp4",
  size_bytes:19,mime_type:"video/mp4",sha256:"b".repeat(64)}
 };
 seed("ai-central/v1/previews/"+id+".json",preview);
 seed("ai-central/v1/factory-jobs/"+job+".json",{
   schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id:job,store_version:1,
   job:{job_id:job,revision:1,status:"ready_for_human",publish_payload:{caption:preview.caption},
        media:[{...preview.media,uri:"r2://private-test/"+preview.media.key}]}
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
 return {submit,current,stateKey,env,job};
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

test("review status reports pending until the real Factory persists completion",async()=>{
 const t=setup(),r=await t.submit();
 assert.equal(r.status,202);
 const result=await r.json();
 const check=await worker.fetch(new Request(
   "https://test.invalid/api/review-status?job_id="+result.job_id+"&request_id="+result.request_id,
   {headers:{authorization:"Bearer "+token}}),t.env);
 assert.equal(check.status,200);
 assert.equal((await check.json()).status,"PENDING_FACTORY_APPLICATION");
});
test("review requires a matching canonical private R2 job",async()=>{
 const t=setup();
 t.current.delete("ai-central/v1/factory-jobs/"+t.job+".json");
 assert.equal((await t.submit()).status,409);
 assert.equal((await t.current.get(t.stateKey).json()).state,"READY_FOR_HUMAN");
});
test("authenticated click dispatches only the exact trusted review workflow",async()=>{
 const t=setup();t.env.GITHUB_DISPATCH_TOKEN="test-dispatch-secret";
 const previous=globalThis.fetch;
 let requests=[];
 globalThis.fetch=async(url,opts)=>{
   requests.push({url,opts});
   return new Response(null,{status:204});
 };
 try{
   const res=await t.submit();
   assert.equal(res.status,202);
   assert.equal((await res.json()).dispatch,"ACCEPTED");
   assert.equal(requests.length,1);
   assert.match(requests[0].url,/block8-dashboard-review-consumer.yml\/dispatches$/);
   const data=JSON.parse(requests[0].opts.body);
   assert.equal(data.inputs.job_id,t.job);
   assert.equal(data.ref,"main");
 }finally{globalThis.fetch=previous}
});
test("lost GitHub dispatch result preserves private pending decision without double queue",async()=>{
 const t=setup();t.env.GITHUB_DISPATCH_TOKEN="test-dispatch-secret";
 const previous=globalThis.fetch;
 globalThis.fetch=async()=>{throw new Error("network lost")};
 try{
   const res=await t.submit();
   assert.equal(res.status,202);
   assert.equal((await res.json()).dispatch,"PENDING_MANUAL_RECONCILIATION");
   assert.equal((await t.current.get(t.stateKey).json()).state,"REVIEW_REQUESTED");
   assert.equal((await t.submit()).status,409);
 }finally{globalThis.fetch=previous}
});
