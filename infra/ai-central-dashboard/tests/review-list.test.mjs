import test from "node:test";
import assert from "node:assert/strict";
import {randomUUID} from "node:crypto";
import {readFileSync} from "node:fs";
import worker from "../src/index.js";

const TOKEN="review-status-owner-test-token-secure-123456", BASE="https://dashboard.example";
const prefix="ai-central/v1/preview-state/";
function setup(){
 const objects=new Map();
 const store={
   async get(k){const value=objects.get(k);return value?{json:async()=>value}:null},
   async list({prefix:head}){return {objects:[...objects.keys()].filter(k=>k.startsWith(head)).map(key=>({key})),truncated:false}}
 };
 const env={AI_DASHBOARD_TOKEN:TOKEN,AI_CENTRAL_R2:store,ASSETS:{fetch:async()=>new Response("ui")}};
 const get=(key,token=TOKEN)=>worker.fetch(new Request(BASE+key,{
   headers:token?{authorization:"Bearer "+token}:{}}),env);
 const add=(options={})=>{
   const job=randomUUID(),request=randomUUID(),revision=1,manifest="a".repeat(64);
   const review={schema:"FACTORY-REVIEW-INTENT-V1",request_id:request,
     job_id:job,revision,manifest,action:"change",actor:"authenticated_dashboard_owner",
     requested_at:new Date().toISOString(),status:"PENDING_FACTORY_APPLICATION",...options.review};
   const state={schema:"FACTORY-PREVIEW-STATE-V1",job_id:job,preview_id:null,
     revision,manifest,state:"REVIEW_REQUESTED",review,...options.state};
   objects.set(prefix+job+".json",state);
   return {job,request,state};
 };
 return {get,add,objects,store,env};
}
test("authenticated review statuses survive page reload and distinguish pending from applied",async()=>{
 const a=setup(),pending=a.add(),applied=a.add({
  state:{state:"REVIEW_APPLIED"},review:{action:"discard",status:"APPLIED_TO_FACTORY"}
 });
 const response=await a.get("/api/reviews");
 assert.equal(response.status,200);
 const doc=await response.json();
 assert.equal(doc.schema,"FACTORY-REVIEW-STATUS-LIST-V1");
 assert.equal(doc.items.length,2);
 assert.equal(doc.items.find(x=>x.job_id===pending.job).status,"PENDING_FACTORY_APPLICATION");
 assert.equal(doc.items.find(x=>x.job_id===applied.job).status,"APPLIED_TO_FACTORY");
 assert.equal((await (await a.get("/api/reviews")).json()).items.length,2);
});
test("anonymous cannot enumerate private review status",async()=>{
 const a=setup();a.add();
 assert.equal((await a.get("/api/reviews","")).status,401);
 assert.equal((await a.get("/api/reviews","invalid-token")).status,401);
});
test("forged actor, malformed request and invalid state never appear",async()=>{
 const a=setup();
 a.add({review:{actor:"unknown"}});
 a.add({review:{status:"APPLIED_TO_FACTORY"}});
 a.add({state:{preview_id:randomUUID()}});
 a.add({review:{request_id:"not-a-valid-uuid"}});
 assert.deepEqual((await (await a.get("/api/reviews")).json()).items,[]);
});
test("truncated list must fail rather than silently hide decisions",async()=>{
 const a=setup();
 a.store.list=async()=>({objects:[],truncated:true});
 assert.equal((await a.get("/api/reviews")).status,409);
});
test("real dashboard displays honest persistent status without post affordance",()=>{
 const ui=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
 assert.match(ui,/id="loadReviews"/);
 assert.match(ui,/api\("\/api\/reviews"\)/);
 assert.match(ui,/Sicher vorgemerkt – Verarbeitung steht aus/);
 assert.match(ui,/Von der Fabrik verbindlich verarbeitet/);
});
