import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";
const token="a".repeat(36);
function fakeR2(){
 const stored=new Map();
 return {stored, async put(key,body){stored.set(key,body);},
   async get(key){const body=stored.get(key);return body===undefined?null:{json:async()=>JSON.parse(body)};},
   async list({prefix}){return {objects:[...stored.keys()].filter(k=>k.startsWith(prefix)).map(key=>({key}))}}};
}
const req=(path,method="GET",headers={},body)=>new Request("https://control.example"+path,{method,headers,body});
test("API rejects absent or wrong token and external origin",async()=>{
 const env={CONTROL_CENTER_TOKEN:token,AI_CENTRAL_R2:fakeR2()};
 assert.equal((await worker.fetch(req("/api/tasks"),env)).status,401);
 assert.equal((await worker.fetch(req("/api/tasks","GET",{"x-control-center-token":token,"origin":"https://evil.example"}),env)).status,403);
 const env2={...env,CONTROL_CENTER_TOKEN:""};
 assert.equal((await worker.fetch(req("/api/tasks","GET",{"x-control-center-token":token}),env2)).status,401);
});
test("web creates a pending task visible in same inbox",async()=>{
 const env={CONTROL_CENTER_TOKEN:token,AI_CENTRAL_R2:fakeR2()};
 const headers={"x-control-center-token":token,"content-type":"application/json","origin":"https://control.example"};
 const created=await worker.fetch(req("/api/tasks","POST",headers,JSON.stringify({text:"Prüfe OpenChatCut"})),env);
 assert.equal(created.status,201);
 const data=await created.json();
 assert.equal(data.status,"PENDING_REVIEW");
 const got=await worker.fetch(req("/api/tasks","GET",headers),env);
 const result=await got.json();
 assert.equal(result.items.length,1);
 assert.equal(result.items[0].text,"Prüfe OpenChatCut");
});
test("telegram document appears next to web documents in dashboard feed",async()=>{
 const r2=fakeR2(),env={CONTROL_CENTER_TOKEN:token,AI_CENTRAL_R2:r2};
 await r2.put("ai-central/v1/telegram-updates/123.json",JSON.stringify({schema:"EDIRNE22-CONTROL-INBOX-V1",request_id:"123",channel:"telegram",source_id:"123",status:"PENDING_REVIEW",text:"Zentrale Auftrag",created_at:"2026-10-01T12:00:00Z"}));
 const result=await (await worker.fetch(req("/api/tasks","GET",{"x-control-center-token":token}),env)).json();
 assert.equal(result.items[0].channel,"telegram");
});
test("oversized commands and uploads are rejected without R2 writes",async()=>{
 const r2=fakeR2(),env={CONTROL_CENTER_TOKEN:token,AI_CENTRAL_R2:r2};
 const h={"x-control-center-token":token,"content-type":"application/json"};
 assert.equal((await worker.fetch(req("/api/tasks","POST",h,JSON.stringify({text:"x".repeat(2501)})),env)).status,400);
 assert.equal((await worker.fetch(req("/api/uploads","POST",{"x-control-center-token":token,"content-type":"application/x-msdownload"},new Uint8Array([1])),env)).status,415);
 assert.equal(r2.stored.size,0);
});
