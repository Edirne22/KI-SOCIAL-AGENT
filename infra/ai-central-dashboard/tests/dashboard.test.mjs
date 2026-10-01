import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";
const TOKEN="unit-test-long-dashboard-token-xyz";
function storage(){const items=new Map(),etags=new Map();let serial=0;return {
 items,etags,async put(k,v,opts={}){
   if(opts.onlyIf?.etagMatches && etags.get(k)!==opts.onlyIf.etagMatches)return null;
   items.set(k,typeof v==="string"?v:new Uint8Array(v));
   let etag="etag-"+(++serial);etags.set(k,etag);return {etag};
 },
 async list({prefix}){return {objects:[...items.keys()].filter(k=>k.startsWith(prefix)).map(key=>({key})),truncated:false}},
 async get(k){if(!items.has(k))return null;return {etag:etags.get(k),json:async()=>JSON.parse(items.get(k))}}}}
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


test("dispatch rejected before verified free-tier flag without touching GitHub",async()=>{
 let e=env(),calls=0; e.AI_CENTRAL_FREE_TIER_VERIFIED="false";e.GITHUB_DISPATCH_TOKEN="fake";
 const old=globalThis.fetch;globalThis.fetch=async()=>{calls++;throw Error("must not call")};
 try{
  const res=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id:"1234567890abcdef",date:"2026-10-01"}),headers:{"content-type":"application/json","origin":"https://dashboard.example"}}),e);
  assert.equal(res.status,409);assert.equal(calls,0);
 }finally{globalThis.fetch=old}
});
test("exact approved draft starts only once and never claims task completion",async()=>{
 let e=env();e.AI_CENTRAL_FREE_TIER_VERIFIED="true";e.GITHUB_DISPATCH_TOKEN="fake-dispatch-test-token";
 const posted=await worker.fetch(request("/api/inbox",{method:"POST",body:JSON.stringify({message:"Review OpenChatCut startup logs"}),headers:{"content-type":"application/json","origin":"https://dashboard.example"}}),e);
 const {id}=await posted.json();const date=new Date().toISOString().slice(0,10);let calls=0;
 const old=globalThis.fetch;
 globalThis.fetch=async(url,opts)=>{calls++;assert.match(url,/ai-central-inbox-agent.yml\/dispatches$/);const b=JSON.parse(opts.body);assert.equal(b.inputs.inbox_id,id);assert.equal(b.ref,"main");return {status:204}};
 try{
  let res=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id,date}),headers:{"content-type":"application/json","origin":"https://dashboard.example"}}),e);
  assert.equal(res.status,202);
  assert.equal((await res.json()).truth,"GITHUB_DISPATCH_ACCEPTED_NOT_EXECUTION_PROOF");
  assert.equal(calls,1);
  assert.equal(JSON.parse([...e.AI_CENTRAL_R2.items.values()][0]).status,"QUEUED_FREE_REVIEW");
  res=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id,date}),headers:{"content-type":"application/json"}}),e);
  assert.equal(res.status,409);assert.equal(calls,1);
  const poll=await worker.fetch(request("/api/task?id="+id),e);
  assert.equal((await poll.json()).status,"NO_REPORT_YET");
 }finally{globalThis.fetch=old}
});
test("failed upstream dispatch restores the draft",async()=>{
 let e=env();e.AI_CENTRAL_FREE_TIER_VERIFIED="true";e.GITHUB_DISPATCH_TOKEN="fake-dispatch-test-token";
 const d=await worker.fetch(request("/api/inbox",{method:"POST",body:JSON.stringify({message:"Review safe container logs"}),headers:{"content-type":"application/json"}}),e);
 const id=(await d.json()).id;const old=globalThis.fetch;
 globalThis.fetch=async()=>({status:403});
 try{
  const res=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id,date:new Date().toISOString().slice(0,10)}),headers:{"content-type":"application/json"}}),e);
  assert.equal(res.status,502);
  assert.equal(JSON.parse([...e.AI_CENTRAL_R2.items.values()][0]).status,"DRAFT_REQUIRES_REVIEW");
 }finally{globalThis.fetch=old}
});


test("simultaneous approval race permits exactly one GitHub dispatch",async()=>{
  let e=env();e.AI_CENTRAL_FREE_TIER_VERIFIED="true";e.GITHUB_DISPATCH_TOKEN="fake";
  const p=await worker.fetch(request("/api/inbox",{method:"POST",body:JSON.stringify({message:"Diagnose startup race"}),headers:{"content-type":"application/json"}}),e);
  const id=(await p.json()).id,date=new Date().toISOString().slice(0,10);let calls=0;
  const old=globalThis.fetch;
  globalThis.fetch=async()=>{calls++;return {status:204}};
  try{
    let [a,b]=await Promise.all([1,2].map(()=>worker.fetch(request("/api/dispatch",{method:"POST",
      body:JSON.stringify({id,date}),headers:{"content-type":"application/json"}}),e)));
    assert.deepEqual([a.status,b.status].sort(),[202,409]);
    assert.equal(calls,1);
  }finally{globalThis.fetch=old}
});
test("ambiguous timeout keeps queued task to prevent duplicate charge or run",async()=>{
  let e=env();e.AI_CENTRAL_FREE_TIER_VERIFIED="true";e.GITHUB_DISPATCH_TOKEN="fake";
  const p=await worker.fetch(request("/api/inbox",{method:"POST",body:JSON.stringify({message:"Diagnose GitHub timeout"}),headers:{"content-type":"application/json"}}),e);
  const id=(await p.json()).id,date=new Date().toISOString().slice(0,10);
  const old=globalThis.fetch;
  globalThis.fetch=async()=>{throw Error("transport reset after acceptance uncertain")};
  try{
    const response=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id,date}),headers:{"content-type":"application/json"}}),e);
    assert.equal(response.status,502);
    assert.equal((await response.json()).status,"DISPATCH_UNCERTAIN");
    assert.equal(JSON.parse([...e.AI_CENTRAL_R2.items.values()][0]).status,"QUEUED_FREE_REVIEW");
  }finally{globalThis.fetch=old}
});
