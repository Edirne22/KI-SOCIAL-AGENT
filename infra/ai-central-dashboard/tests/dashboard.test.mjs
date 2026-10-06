import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
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


test("retry with newer lifecycle must not leak previous run report",async()=>{
 const e=env(),id="safe-retry-task-2026";
 const oldKey="ai-central/v1/tasks/"+id+"/runs/100/report.json";
 await e.AI_CENTRAL_R2.put(oldKey,JSON.stringify({schema:"CLOUD-AI-CENTRAL-V1",task_id:id,run_id:"100",status:"PENDING_REVIEW",
    results:[{role:"diagnosis",status:"ANSWER",attempts:[{provider:"openrouter",text:"OUTDATED-ANSWER"}]}]}));
 const lifecycleKey="ai-central/v1/tasks/"+id+"/status.json";
 await e.AI_CENTRAL_R2.put(lifecycleKey,JSON.stringify({schema:"AI-CENTRAL-TASK-STATUS-V1",task_id:id,
    github_run_id:"101",status:"RUNNING",updated_at:"2026-10-01T15:00:00Z"}));
 let response=await worker.fetch(request("/api/task?id="+id),e);
 assert.equal(response.status,200);
 let body=await response.json();
 assert.equal(body.status,"RUNNING");
 assert.equal(body.run_id,"101");
 assert.equal(body.roles,undefined);
 assert.equal(body.truth,"R2_JOB_LIFECYCLE_NO_COMPLETED_REPORT");
 await e.AI_CENTRAL_R2.put(lifecycleKey,JSON.stringify({schema:"AI-CENTRAL-TASK-STATUS-V1",task_id:id,
    github_run_id:"101",status:"FAILED",updated_at:"2026-10-01T15:01:00Z"}));
 response=await worker.fetch(request("/api/task?id="+id),e);
 body=await response.json();
 assert.equal(body.status,"FAILED");
 assert.equal(body.roles,undefined);
 await e.AI_CENTRAL_R2.put("ai-central/v1/tasks/"+id+"/runs/101/report.json",
   JSON.stringify({schema:"CLOUD-AI-CENTRAL-V1",task_id:id,run_id:"101",status:"PENDING_REVIEW",
   results:[{role:"research",status:"ANSWER",attempts:[]}]}));
 response=await worker.fetch(request("/api/task?id="+id),e);
 body=await response.json();
 assert.equal(body.truth,"R2_ARCHIVED_REPORT");
 assert.equal(body.run_id,"101");
 assert.equal(body.roles.length,1);
});
test("reject task report with mismatched current run",async()=>{
 const e=env(),id="safe-retry-task-2027",base="ai-central/v1/tasks/"+id+"/";
 await e.AI_CENTRAL_R2.put(base+"status.json",JSON.stringify({
   schema:"AI-CENTRAL-TASK-STATUS-V1",task_id:id,github_run_id:"101",status:"PENDING_REVIEW"}));
 await e.AI_CENTRAL_R2.put(base+"runs/101/report.json",JSON.stringify({
   schema:"CLOUD-AI-CENTRAL-V1",task_id:id,run_id:"999",results:[]}));
 const response=await worker.fetch(request("/api/task?id="+id),e);
 assert.equal(response.status,502);
});

test("NVIDIA free-team is explicitly selected and cannot be double-dispatched",async()=>{
 const e=env();e.AI_CENTRAL_FREE_TIER_VERIFIED="true";e.GITHUB_DISPATCH_TOKEN="fake";
 const p=await worker.fetch(request("/api/inbox",{method:"POST",body:JSON.stringify({message:"Inspect actual MCP root cause"}),headers:{"content-type":"application/json"}}),e);
 const id=(await p.json()).id,date=new Date().toISOString().slice(0,10);
 const old=globalThis.fetch;let calls=[];
 globalThis.fetch=async(url,opts)=>{calls.push(JSON.parse(opts.body));return {status:204}};
 try{
  const bad=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id,date,mode:"paid"}),headers:{"content-type":"application/json"}}),e);
  assert.equal(bad.status,400);assert.equal(calls.length,0);
  const result=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id,date,mode:"free-team"}),headers:{"content-type":"application/json"}}),e);
  assert.equal(result.status,202);
  assert.equal(calls.length,1);assert.equal(calls[0].inputs.team_mode,"free-team");
  const item=JSON.parse([...e.AI_CENTRAL_R2.items.values()][0]);
  assert.equal(item.inference_scope,"nvidia/free-team");
  const retry=await worker.fetch(request("/api/dispatch",{method:"POST",body:JSON.stringify({id,date,mode:"free-only"}),headers:{"content-type":"application/json"}}),e);
  assert.equal(retry.status,409);assert.equal(calls.length,1);
 }finally{globalThis.fetch=old}
});

test("MP4 selected by the dashboard is accepted as a private draft",async()=>{
 const e=env();const r=await worker.fetch(request("/api/upload",{method:"POST",body:new Uint8Array([0,0,0,24,102,116,121,112]),headers:{"content-type":"video/mp4","x-upload-name":"synthetic.mp4"}}),e);
 assert.equal(r.status,202);assert.equal((await r.json()).status,"DRAFT_REQUIRES_REVIEW");
 const entries=await (await worker.fetch(request("/api/inbox"),e)).json();assert.equal(entries.items[0].file.mime,"video/mp4");
});
test('inbox never labels a truncated old page as the latest jobs',async()=>{
 const e=env();let limit;e.AI_CENTRAL_R2.list=async options=>{limit=options.limit;return {objects:[],truncated:true,cursor:'next'}};
 const response=await worker.fetch(request('/api/inbox'),e);
 assert.equal(response.status,409);assert.equal(limit,1000);assert.match((await response.json()).error,/no incomplete latest list/);
});


test("CODE session routes one bounded message through private OpenCode service and stores exact exchange",async()=>{
 const e=env(),calls=[];e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";
 e.PRIVATE_ASR_SERVICE={fetch:async(url,opts)=>{
   calls.push({url:String(url),method:opts.method,authorization:opts.headers.authorization,body:JSON.parse(opts.body)});
   return new Response(JSON.stringify({text:"OPENCODE_DASHBOARD_OK",workspace:"repo-readonly-v1",tools_used:["bash"]}),{status:200,headers:{"content-type":"application/json"}});
 }};
 const origin={"content-type":"application/json","origin":"https://dashboard.example"};
 const created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"code"}),headers:origin}),e);
 assert.equal(created.status,201);const session=await created.json();assert.equal(session.mode,"code");
 const response=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:session.id,message:"Hallo Claude"}),headers:origin}),e);
 assert.equal(response.status,200);const result=await response.json();
 assert.deepEqual({text:result.text,stored:result.stored},{text:"OPENCODE_DASHBOARD_OK",stored:true});
 assert.equal(calls.length,1);assert.equal(calls[0].url,"https://private-asr/opencode/code");
 assert.equal(calls[0].method,"POST");assert.equal(calls[0].authorization,"Bearer internal-test-token");
 assert.deepEqual(calls[0].body,{message:"Hallo Claude"});
 const saved=await worker.fetch(request("/api/chat/session?id="+session.id),e);
 const history=(await saved.json()).messages;
 assert.deepEqual(history.map(x=>[x.role,x.text]),[["user","Hallo Claude"],["assistant","OPENCODE_DASHBOARD_OK"]]);
});

test("CODE transport fails closed for auth origin missing runtime and malformed upstream without storing messages",async()=>{
 const origin={"content-type":"application/json","origin":"https://dashboard.example"};
 const make=async e=>{
   const r=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"code"}),headers:origin}),e);
   assert.equal(r.status,201);return (await r.json()).id;
 };
 let e=env(),id=await make(e);
 let r=await worker.fetch(request("/api/chat/message",{method:"POST",token:"wrong",body:JSON.stringify({session_id:id,message:"Hallo Claude"}),headers:origin}),e);
 assert.equal(r.status,401);
 r=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Hallo Claude"}),headers:{"content-type":"application/json","origin":"https://attacker.example"}}),e);
 assert.equal(r.status,403);
 r=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Hallo Claude"}),headers:origin}),e);
 assert.equal(r.status,503);assert.equal((await r.json()).stored,false);
 let s=await worker.fetch(request("/api/chat/session?id="+id),e);assert.equal((await s.json()).messages.length,0);
 e=env();id=await make(e);e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";
 e.PRIVATE_ASR_SERVICE={fetch:async()=>new Response(JSON.stringify({unexpected:"raw-event"}),{status:200,headers:{"content-type":"application/json"}})};
 r=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Hallo Claude"}),headers:origin}),e);
 assert.equal(r.status,502);assert.equal((await r.json()).stored,false);
 s=await worker.fetch(request("/api/chat/session?id="+id),e);assert.equal((await s.json()).messages.length,0);
});

test("CHAT session uses the same private Claude transport while secret-shaped prompts still fail closed",async()=>{
 const e=env(),origin={"content-type":"application/json","origin":"https://dashboard.example"};let calls=0;
 e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";e.PRIVATE_ASR_SERVICE={fetch:async()=>{calls++;return new Response(JSON.stringify({text:"CHAT_DASHBOARD_OK"}),{status:200,headers:{"content-type":"application/json"}})}};
 let created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"chat"}),headers:origin}),e);
 let id=(await created.json()).id;
 let r=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Hallo Claude"}),headers:origin}),e);
 assert.equal(r.status,200);assert.equal((await r.json()).text,"CHAT_DASHBOARD_OK");assert.equal(calls,1);
 let saved=await worker.fetch(request("/api/chat/session?id="+id),e);assert.deepEqual((await saved.json()).messages.map(x=>[x.role,x.text]),[["user","Hallo Claude"],["assistant","CHAT_DASHBOARD_OK"]]);
 created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"code"}),headers:origin}),e);id=(await created.json()).id;
 r=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Authorization: Bearer should-never-leave-dashboard"}),headers:origin}),e);
 assert.equal(r.status,400);assert.equal(calls,1);
});


test("CHAT replays bounded saved conversation context while CODE remains single-turn",async()=>{
 const e=env(),origin={"content-type":"application/json","origin":"https://dashboard.example"},bodies=[];
 e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";e.PRIVATE_ASR_SERVICE={fetch:async(url,opts)=>{bodies.push(JSON.parse(opts.body));const isCode=String(url).endsWith("/opencode/code");return new Response(JSON.stringify({text:bodies.length===1?"GEMERKT":"2210",...(isCode?{workspace:"repo-readonly-v1",tools_used:[]}:{})}),{status:200,headers:{"content-type":"application/json"}})}};
 let created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"chat"}),headers:origin}),e),id=(await created.json()).id;
 await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Merke dir die Zahl 2210."}),headers:origin}),e);
 await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Welche Zahl solltest du dir merken?"}),headers:origin}),e);
 assert.equal(bodies[0].message,"User: Merke dir die Zahl 2210.\\n\\nAssistant:");
 assert.match(bodies[1].message,/User: Merke dir die Zahl 2210\./);assert.match(bodies[1].message,/Assistant: GEMERKT/);assert.match(bodies[1].message,/User: Welche Zahl solltest du dir merken\?/);
 created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"code"}),headers:origin}),e);id=(await created.json()).id;
 await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"CODE_SINGLE_TURN"}),headers:origin}),e);
 assert.equal(bodies.at(-1).message,"CODE_SINGLE_TURN");
});



test("CODE uses dedicated repo executor and fails closed without verified workspace contract",async()=>{
 const e=env(),origin={"content-type":"application/json","origin":"https://dashboard.example"},urls=[];
 e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";
 e.PRIVATE_ASR_SERVICE={fetch:async(url)=>{urls.push(String(url));return new Response(JSON.stringify({text:"UNVERIFIED_CODE"}),{status:200,headers:{"content-type":"application/json"}})}};
 const created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"code"}),headers:origin}),e);
 const id=(await created.json()).id;
 const response=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"inspect repo"}),headers:origin}),e);
 assert.equal(response.status,502);const out=await response.json();
 assert.equal(out.status,"CODE_WORKSPACE_UNVERIFIED");assert.equal(out.stored,false);
 assert.deepEqual(urls,["https://private-asr/opencode/code"]);
 const saved=await worker.fetch(request("/api/chat/session?id="+id),e);
 assert.equal((await saved.json()).messages.length,0);
});

test("secure HttpOnly dashboard session survives refresh without resending bearer key",async()=>{
 const e=env(),origin={"origin":"https://dashboard.example"};
 const login=await worker.fetch(request("/api/auth/session",{method:"POST",headers:origin}),e);
 assert.equal(login.status,200);const cookie=login.headers.get("set-cookie");
 assert.match(cookie,/edirne22_session=/);assert.match(cookie,/HttpOnly/);assert.match(cookie,/Secure/);assert.match(cookie,/SameSite=Strict/);
 const pair=cookie.split(";")[0];
 const resumed=await worker.fetch(new Request("https://dashboard.example/api/inbox",{headers:{cookie:pair,origin:"https://dashboard.example"}}),e);
 assert.equal(resumed.status,200);
 const bad=await worker.fetch(new Request("https://dashboard.example/api/inbox",{headers:{cookie:"edirne22_session=invalid",origin:"https://dashboard.example"}}),e);
 assert.equal(bad.status,401);
});


test("CHAT and universal CODE expose truthful fail-closed route metadata",async()=>{
  const e=env();
  e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";
  e.PRIVATE_ASR_SERVICE={fetch:async(url)=>new Response(JSON.stringify({text:"ROUTE_OK",...(String(url).endsWith("/opencode/code")?{workspace:"repo-readonly-v1",tools_used:["bash"]}:{})}),{status:200,headers:{"content-type":"application/json"}})};
  const origin={"content-type":"application/json","origin":"https://dashboard.example"};
  const start=async mode=>await (await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode}),headers:origin}),e)).json();
  const send=async(session_id,message)=>worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id,message}),headers:origin}),e);
  const chat=await start("chat"),code=await start("code");
  const cr=await send(chat.id,"normal conversation"),dr=await send(code.id,"inspect repository safely");
  assert.equal(cr.status,200);assert.equal(dr.status,200);
  const c=await cr.json(),d=await dr.json();
  assert.equal(c.route.mode,"CHAT");assert.equal(c.route.gate,"CONVERSATION");
  assert.equal(c.route.tools.agent21,false);assert.equal(c.route.tools.github,false);
  assert.equal(c.route.tools.web_research,"AVAILABLE_ON_DEMAND");
  assert.equal(d.route.mode,"CODE");assert.equal(d.route.workspace,"REPO_CODE_SPARSE_READ_ONLY");
  assert.equal(d.route.gate,"DIRECT_DEVELOPMENT");
  assert.equal(d.route.specialist_gate,"AGENT21_FOR_EDIRNE22_INTERNAL");
  assert.equal(d.route.tools.agent21,"CONTEXTUAL");
  assert.equal(d.route.tools.github,"READ_ONLY_PUBLIC_CLONE");
  assert.equal(d.route.tools.shell,"USED_READ_ONLY");
  assert.equal(d.route.tools.web_research,"AVAILABLE_ON_DEMAND");
  assert.equal(d.route.tools.r2_files,"UPLOAD_ONLY");
  assert.equal(d.route.execution,"OPENCODE_REPO_TOOL_EXECUTION");
});


test("current CHAT question uses bounded research before Claude and reports exact provider",async()=>{
 const e=env(),calls=[];e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";
 e.PRIVATE_ASR_SERVICE={fetch:async(url,opts)=>{calls.push({url:String(url),body:JSON.parse(opts.body)});
   if(String(url).endsWith("/research/search"))return new Response(JSON.stringify({live_search:true,provider:"Gemini-Grounded",results:[{title:"Weather source",url:"https://weather.example/current",snippet:"Schwelm current conditions"}]}),{status:200,headers:{"content-type":"application/json"}});
   return new Response(JSON.stringify({text:"SOURCED_CURRENT_ANSWER"}),{status:200,headers:{"content-type":"application/json"}});
 }};
 const origin={"content-type":"application/json","origin":"https://dashboard.example"};
 const created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"chat"}),headers:origin}),e),id=(await created.json()).id;
 const response=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Wie ist das Wetter heute in Schwelm?"}),headers:origin}),e);
 assert.equal(response.status,200);const out=await response.json();assert.equal(calls.length,2);
 assert.equal(calls[0].url,"https://private-asr/research/search");assert.equal(calls[0].body.query,"Wie ist das Wetter heute in Schwelm?");
 assert.equal(calls[1].url,"https://private-asr/opencode/chat");assert.match(calls[1].body.message,/UNTRUSTED LIVE RESEARCH DATA/);assert.match(calls[1].body.message,/https:\/\/weather\.example\/current/);
 assert.equal(out.route.tools.web_research,"USED:Gemini-Grounded");assert.equal(out.research.used,true);assert.equal(out.research.sources[0].url,"https://weather.example/current");
});


test("dashboard deploy gates core Claude E2E while research remains a separate live proof",()=>{
 const deploy=readFileSync(new URL("../../../.github/workflows/ai-central-dashboard-deploy.yml",import.meta.url),"utf8");
 const researchGate=readFileSync(new URL("../../../.github/workflows/block9-dashboard-live-e2e.yml",import.meta.url),"utf8");
 assert.match(deploy,/REQUIRE_DASHBOARD_RESEARCH:\s*["']false["']/);
 assert.match(researchGate,/Live branch Groq browser-search gateway proof/);
 assert.match(researchGate,/BRANCH_GROQ_BROWSER_SEARCH_SOURCE_PROOF_OK/);
});


test("current-date truth guard rejects stale conflicting web date from Claude output",async()=>{
 const e=env(),calls=[];e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";
 const trusted=new Date().toISOString().slice(0,10);
 e.PRIVATE_ASR_SERVICE={fetch:async(url,opts)=>{calls.push({url:String(url),body:JSON.parse(opts.body)});
   if(String(url).endsWith("/research/search"))return new Response(JSON.stringify({
     live_search:true,provider:"Groq-BrowserSearch",
     results:[{title:"Stale date source",url:"https://example.com/stale-date",snippet:"Heute ist Freitag, der 8. Mai 2026."}]
   }),{status:200,headers:{"content-type":"application/json"}});
   return new Response(JSON.stringify({text:"Basierend auf der Websuche ist heute Freitag, der 8. Mai 2026."}),{status:200,headers:{"content-type":"application/json"}});
 }};
 const origin={"content-type":"application/json","origin":"https://dashboard.example"};
 const created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"chat"}),headers:origin}),e),id=(await created.json()).id;
 const response=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Welches Datum ist heute? Suche im Web und nenne eine Quelle."}),headers:origin}),e);
 assert.equal(response.status,200);const out=await response.json();
 assert.match(calls[1].body.message,new RegExp("TRUSTED RUNTIME CURRENT DATE \\(UTC\\): "+trusted.replaceAll("-","\\-")));
 assert.match(calls[1].body.message,new RegExp(trusted.replaceAll("-","\\-")));
 assert.match(out.text,new RegExp(trusted.replaceAll("-","\\-")));
 assert.doesNotMatch(out.text,/8\. Mai 2026/);
 assert.match(out.text,/nicht als Datumsautorität verwendet/);
 const saved=await worker.fetch(request("/api/chat/session?id="+id),e);
 const history=(await saved.json()).messages;
 assert.match(history.at(-1).text,new RegExp(trusted.replaceAll("-","\\-")));
 assert.doesNotMatch(history.at(-1).text,/8\. Mai 2026/);
});

test("current-date truth guard preserves a correct Claude date answer",async()=>{
 const e=env();e.PRIVATE_ASR_INTERNAL_TOKEN="internal-test-token";
 const trusted=new Date().toISOString().slice(0,10);
 e.PRIVATE_ASR_SERVICE={fetch:async(url)=>{
   if(String(url).endsWith("/research/search"))return new Response(JSON.stringify({
     live_search:true,provider:"Groq-BrowserSearch",
     results:[{title:"Current source",url:"https://example.com/current",snippet:"Current date reference"}]
   }),{status:200,headers:{"content-type":"application/json"}});
   return new Response(JSON.stringify({text:"Heute ist "+trusted+". Quelle: https://example.com/current"}),{status:200,headers:{"content-type":"application/json"}});
 }};
 const origin={"content-type":"application/json","origin":"https://dashboard.example"};
 const created=await worker.fetch(request("/api/chat/session",{method:"POST",body:JSON.stringify({mode:"chat"}),headers:origin}),e),id=(await created.json()).id;
 const response=await worker.fetch(request("/api/chat/message",{method:"POST",body:JSON.stringify({session_id:id,message:"Welches Datum ist heute? Suche im Web."}),headers:origin}),e);
 assert.equal(response.status,200);const out=await response.json();
 assert.equal(out.text,"Heute ist "+trusted+". Quelle: https://example.com/current");
 assert.equal(out.research.used,true);
 assert.equal(out.research.provider,"Groq-BrowserSearch");
});
