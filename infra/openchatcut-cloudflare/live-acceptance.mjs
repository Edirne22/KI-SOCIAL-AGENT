import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand, HeadObjectCommand } from "@aws-sdk/client-s3";
import { createHash } from "node:crypto";
import { writeFile, readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";

const base=(process.env.OPENCHATCUT_BASE_URL||"").replace(/\/$/,"");
const token=process.env.OPENCHATCUT_MCP_TOKEN||"";
if(!base||!token) throw new Error("missing OPENCHATCUT_BASE_URL/OPENCHATCUT_MCP_TOKEN");
const auth={Authorization:`Bearer ${token}`};
const assert=(v,m)=>{if(!v)throw new Error(m)};
async function http(path,headers={}){return fetch(base+path,{headers:{...headers}})}
let r=await http("/_factory/health"); assert(r.status===401,`no-token expected 401 got ${r.status}`);
r=await http("/_factory/health",{Authorization:"Bearer definitely-wrong"}); assert(r.status===401,`wrong-token expected 401 got ${r.status}`);
r=await http("/_factory/health",auth); assert(r.ok,`health failed ${r.status}`); console.log("protected health:",await r.text());

const transport=new StreamableHTTPClientTransport(new URL(base+"/api/external-mcp/mcp"),{requestInit:{headers:auth}});
let client=new Client({name:"edirne22-live-acceptance",version:"1.0.0"});
await client.connect(transport);
let call=async(name,args={})=>{console.log("MCP",name);const x=await client.callTool({name,arguments:args});if(x.isError)throw new Error(`${name}: ${JSON.stringify(x.content)}`);return x};
const data=x=>x.structuredContent??Object.assign({},...(x.content||[]).filter(c=>c.type==="text").map(c=>{try{return JSON.parse(c.text)}catch{return {text:c.text}}}));
const status=await call("openchatcut_status"); console.log("status",JSON.stringify(data(status)));
const created=data(await call("create_project",{name:`Edirne22 LIVE acceptance ${new Date().toISOString()}`,compositionWidth:720,compositionHeight:1280,fps:30}));
const projectId=created.id||created.projectId; assert(projectId,"create_project returned no id");
await call("target_project",{projectId});
let tools=(await client.listTools()).tools; console.log("tool count",tools.length);
const has=n=>tools.some(t=>t.name===n);
for(const n of ["begin_edit_session","read_project","list_templates","add_motion_graphic","review_edit_session"]) assert(has(n),`required server-direct MCP tool missing: ${n}`);
let begun;
try {
  begun=data(await call("begin_edit_session",{approvalMode:"auto"}));
} catch (error) {
  console.error("BEGIN_EDIT_SESSION_DISCONNECT", error?.stack || error);
  // Upstream OpenChatCut deliberately persists a disconnected owner's draft.
  // Recover that orphan instead of re-targeting/re-beginning and colliding with
  // the ownership claim that the failed HTTP response may already have created.
  const hr=await http("/_factory/health",auth);
  assert(hr.ok,`post-disconnect health failed ${hr.status}`);
  const recoveryTransport=new StreamableHTTPClientTransport(new URL(base+"/api/external-mcp/mcp"),{requestInit:{headers:auth}});
  const recoveryClient=new Client({name:"edirne22-disconnect-recovery",version:"1.0.0"});
  await recoveryClient.connect(recoveryTransport);
  const recoveryCall=async(name,args={})=>{console.log("MCP RECOVERY",name);const x=await recoveryClient.callTool({name,arguments:args});if(x.isError)throw new Error(`${name}: ${JSON.stringify(x.content)}`);return x};
  const listed=data(await recoveryCall("list_edit_sessions",{}));
  console.log("RECOVERY_SESSIONS",JSON.stringify(listed));
  const sessions=Array.isArray(listed)?listed:(listed.sessions||listed.items||listed.result||[]);
  const orphan=sessions.find(s=>s.orphaned===true && (s.recoveryActions||[]).includes("resume"));
  assert(orphan,`begin_edit_session disconnected but no resumable orphan exists: ${JSON.stringify(listed)}`);
  const orphanId=orphan.editSessionId||orphan.id;
  assert(orphanId,"resumable orphan has no editSessionId");
  begun=data(await recoveryCall("recover_edit_session",{editSessionId:orphanId,action:"resume"}));
  begun={...begun,editSessionId:begun.editSessionId||begun.id||orphanId};
  console.log("RECOVERY_RESUMED",JSON.stringify({editSessionId:begun.editSessionId}));
  await client.close().catch(()=>{});
  // Continue all subsequent calls on the transport that now owns the resumed draft.
  client=recoveryClient;
  call=async(name,args={})=>{console.log("MCP",name);const x=await client.callTool({name,arguments:args});if(x.isError)throw new Error(`${name}: ${JSON.stringify(x.content)}`);return x};
}
const editSessionId=begun.editSessionId||begun.id; assert(editSessionId,"no editSessionId");
const templates=data(await call("list_templates",{})); console.log("templates",JSON.stringify(templates).slice(0,1500));
const templateList=Array.isArray(templates)?templates:(templates.templates||templates.items||[]);
assert(templateList.length,"OpenChatCut returned no built-in motion graphic templates");
const templateName=templateList[0].name||templateList[0].title; assert(templateName,"template has no name");
await call("add_motion_graphic",{editSessionId,templateName,track:"V1",startFrame:0});
await call("review_edit_session",{editSessionId,summary:"Edirne22 native headless acceptance"});
const committed=data(await call("read_project",{})); console.log("committed project",JSON.stringify(committed).slice(0,2000));
const projectDoc=committed.project||committed.document||committed;
const timelineId=projectDoc.activeTimelineId||(projectDoc.timelines&&projectDoc.timelines[0]&&projectDoc.timelines[0].id);
assert(timelineId,"read_project returned no active timeline");
console.log("HEADLESS_RENDER_PATH","OpenChatCut native /export -> Remotion/headless Chrome; no connected editor required");
const exportResponse=await fetch(base+"/export",{method:"POST",headers:{...auth,"content-type":"application/json"},body:JSON.stringify({project:projectDoc,timelineId,format:"video",codec:"h264",name:"edirne22-openchatcut-live-acceptance.mp4"})});
if(!exportResponse.ok) throw new Error(`native headless /export failed ${exportResponse.status}: ${await exportResponse.text()}`);
const bytes=Buffer.from(await exportResponse.arrayBuffer());
assert(bytes.length>1000,"native headless /export returned empty/tiny output");
await writeFile("/tmp/openchatcut-live.mp4",bytes);
const fp=spawnSync("ffprobe",["-v","error","-show_entries","format=duration,format_name:stream=codec_name,width,height","-of","json","/tmp/openchatcut-live.mp4"],{encoding:"utf8"});
assert(fp.status===0,`ffprobe failed: ${fp.stderr}`); const probe=JSON.parse(fp.stdout); console.log("ffprobe",JSON.stringify(probe)); assert((probe.streams||[]).some(s=>s.codec_name==="h264"||s.codec_name==="vp9"||s.codec_name==="av1"),"no video codec");
const sha=createHash("sha256").update(bytes).digest("hex");
const s3=new S3Client({region:"auto",endpoint:`https://${process.env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,credentials:{accessKeyId:process.env.R2_ACCESS_KEY_ID,secretAccessKey:process.env.R2_SECRET_ACCESS_KEY}});
const bucket=process.env.R2_BUCKET_NAME; const key=`acceptance/openchatcut/${Date.now()}-${sha.slice(0,16)}.mp4`;
await s3.send(new PutObjectCommand({Bucket:bucket,Key:key,Body:bytes,ContentType:"video/mp4",Metadata:{sha256:sha}}));
const got=await s3.send(new GetObjectCommand({Bucket:bucket,Key:key})); const round=Buffer.from(await got.Body.transformToByteArray()); const sha2=createHash("sha256").update(round).digest("hex"); assert(sha===sha2,"R2 SHA-256 mismatch");
let missing=false;try{await s3.send(new HeadObjectCommand({Bucket:bucket,Key:key+"-foreign"}))}catch{missing=true}assert(missing,"foreign/stale R2 key unexpectedly exists");
await writeFile("/tmp/corrupt.mp4",Buffer.from("not-a-video")); const bad=spawnSync("ffprobe",["-v","error","/tmp/corrupt.mp4"]); assert(bad.status!==0,"corrupt non-video negative control was accepted");
await s3.send(new DeleteObjectCommand({Bucket:bucket,Key:key}));
console.log(JSON.stringify({LIVE_ACCEPTANCE:"PASS",projectId,bytes:bytes.length,sha256:sha,r2Roundtrip:true,negativeControls:["no-token","wrong-token","foreign-r2-key","corrupt-non-video"]}));
await client.close();
