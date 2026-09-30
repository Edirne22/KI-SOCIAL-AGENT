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
const client=new Client({name:"edirne22-live-acceptance",version:"1.0.0"});
await client.connect(transport);
const call=async(name,args={})=>{console.log("MCP",name);const x=await client.callTool({name,arguments:args});if(x.isError)throw new Error(`${name}: ${JSON.stringify(x.content)}`);return x};
const data=x=>x.structuredContent??Object.assign({},...(x.content||[]).filter(c=>c.type==="text").map(c=>{try{return JSON.parse(c.text)}catch{return {text:c.text}}}));
const status=await call("openchatcut_status"); console.log("status",JSON.stringify(data(status)));
const created=data(await call("create_project",{name:`Edirne22 LIVE acceptance ${new Date().toISOString()}`,compositionWidth:720,compositionHeight:1280,fps:30}));
const projectId=created.id||created.projectId; assert(projectId,"create_project returned no id");
await call("target_project",{projectId});
for(const skill of ["create-motion-graphics","export","verification"]){try{await call("load_skill",{name:skill})}catch(e){console.log("skill optional:",skill,String(e))}}
let tools=(await client.listTools()).tools; console.log("tool count",tools.length);
const has=n=>tools.some(t=>t.name===n); for(const n of ["begin_edit_session","read_project","create_motion_graphic_from_code","edit_item","review_edit_session","submit_export"]) assert(has(n),`required MCP tool missing: ${n}`);
const schema=n=>tools.find(t=>t.name===n)?.inputSchema||{};
console.log("schemas",JSON.stringify(Object.fromEntries(["begin_edit_session","edit_item","submit_export"].map(n=>[n,schema(n)]))));
const begun=data(await call("begin_edit_session",{approvalMode:"auto"})); const editSessionId=begun.editSessionId||begun.id; assert(editSessionId,"no editSessionId");
const project=data(await call("read_project",{editSessionId})); console.log("project read ok",JSON.stringify(project).slice(0,1000));
const mg=data(await call("create_motion_graphic_from_code",{editSessionId,name:"Edirne22 acceptance card",width:720,height:1280,durationInSeconds:7,code:`export default function Composition(){return <div style={{width:'100%',height:'100%',background:'#111',display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontSize:72,fontFamily:'sans-serif'}}><div>EDIRNE 22 · LIVE</div></div>}`}));
const assetId=mg.assetId||mg.id; assert(assetId,`MG returned no asset id: ${JSON.stringify(mg)}`);
let editArgs={editSessionId,adds:[{kind:"motion-graphic",assetId,startFrame:0,durationInFrames:210}]};
try{await call("edit_item",editArgs)}catch(e){console.log("first edit shape failed",String(e)); await call("edit_item",{editSessionId,action:"add",kind:"motion-graphic",assetId,startFrame:0,durationInFrames:210})}
await call("review_edit_session",{editSessionId});
for(let i=0;i<20;i++){const s=data(await call("get_edit_session",{editSessionId})); if(s.status==="applied")break;if(["rejected","discarded"].includes(s.status))throw new Error("edit session "+s.status);await new Promise(q=>setTimeout(q,1000));if(i===19)throw new Error("edit session did not become applied")}
const exp=data(await call("submit_export",{format:"video",codec:"h264",name:"edirne22-openchatcut-live-acceptance"})); console.log("export",JSON.stringify(exp));
function strings(o,out=[]){if(typeof o==="string")out.push(o);else if(Array.isArray(o))o.forEach(v=>strings(v,out));else if(o&&typeof o==="object")Object.values(o).forEach(v=>strings(v,out));return out}
const urls=strings(exp).filter(s=>/^https?:\/\//.test(s)); let bytes=null;
for(const u of urls){try{const q=await fetch(u,{headers:auth});if(q.ok){const b=Buffer.from(await q.arrayBuffer());if(b.length>1000){bytes=b;break}}}catch{}}
if(!bytes && exp.path){const q=await fetch(base+`/api/result-download?path=${encodeURIComponent(exp.path)}`,{headers:auth});if(q.ok)bytes=Buffer.from(await q.arrayBuffer())}
assert(bytes&&bytes.length>1000,"could not retrieve rendered MP4 from OpenChatCut export");
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
