import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";
const TOKEN="unit-test-long-dashboard-token-xyz";
function storage(){const items=new Map();return {
 items,async put(k,v){items.set(k,typeof v==="string"?v:new Uint8Array(v))},
 async list({prefix}){return {objects:[...items.keys()].filter(k=>k.startsWith(prefix)).map(key=>({key}))}},
 async get(k){if(!items.has(k))return null;return {json:async()=>JSON.parse(items.get(k))}}}}
function env(){return {AI_DASHBOARD_TOKEN:TOKEN,AI_CENTRAL_R2:storage(),ASSETS:{fetch:async()=>new Response("ui")}}}
function request(path,{method="GET",token=TOKEN,body,headers={}}={}){return new Request("https://dashboard.example"+path,{method,headers:{...(token?{authorization:"Bearer "+token}:{}),...headers},body})}
test("unauthorized must not access R2 or GitHub",async()=>{
 let e=env();assert.equal((await worker.fetch(request("/api/inbox",{token:"wrong"}),e)).status,401);
 assert.equal((await worker.fetch(request("/api/inbox",{token:""}),e)).status,401);
});
test("valid Web chat draft appears in shared R2 inbox, never auto-dispatched",async()=>{
 let e=env(),body=JSON.stringify({message:"Bitte Container untersuchen"});
 let post=await worker.fetch(request("/api/inbox",{method:"POST",body,headers:{"content-type":"application/json","origin":"https://dashboard.example"}}),e);
 assert.equal(post.status,202);let get=await worker.fetch(request("/api/inbox"),e);
 let data=await get.json();assert.equal(data.items.length,1);assert.equal(data.items[0].channel,"web");
 assert.equal(data.items[0].status,"DRAFT_REQUIRES_REVIEW");
 assert.equal(JSON.parse([...e.AI_CENTRAL_R2.items.values()][0]).auto_dispatch,false);
});
test("reject origin, secrets and oversized inputs",async()=>{
 let e=env();const put=async(message,origin="https://dashboard.example")=>worker.fetch(request("/api/inbox",{method:"POST",body:JSON.stringify({message}),headers:{"content-type":"application/json",origin}}),e);
 assert.equal((await put("Do something","https://attacker.example")).status,403);
 assert.equal((await put("Authorization: Bearer secret-value")).status,400);
 assert.equal((await put("x".repeat(2501))).status,400);
 assert.equal(e.AI_CENTRAL_R2.items.size,0);
});
test("R2 file upload bounded and private",async()=>{
 let e=env();let a=await worker.fetch(request("/api/upload",{method:"POST",body:"hello",headers:{"content-type":"text/plain","x-upload-name":"../../sample.txt","origin":"https://dashboard.example"}}),e);
 assert.equal(a.status,202);assert.equal(e.AI_CENTRAL_R2.items.size,2);
 let b=await worker.fetch(request("/api/upload",{method:"POST",body:"hello",headers:{"content-type":"application/x-executable"}}),e);
 assert.equal(b.status,415);
});
test("only explicit API routes",async()=>{
 let e=env();assert.equal((await worker.fetch(request("/api/unknown"),e)).status,404);
 assert.equal((await worker.fetch(request("/"),e)).status,200);
});
