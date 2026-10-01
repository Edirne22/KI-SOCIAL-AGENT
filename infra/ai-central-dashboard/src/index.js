// Cloudflare Worker gateway: R2-backed shared Telegram+Web inbox.
// No provider credentials, workflow tokens, auto-dispatch or approvals in this slice.
const PREFIX="ai-central/v1/inbox/";
const MAX_MESSAGE=2500;
const MAX_FILE=8*1024*1024;
const TYPES=new Set(["text/plain","text/markdown","application/json","image/png","image/jpeg","audio/webm","audio/mp4","audio/ogg"]);
const DENY=/(?:authorization\s*:\s*bearer|api[_-]?key\s*[=:]|secret\s*[=:]|password\s*[=:])\s*\S+/i;
function json(body,status=200){return new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}})}
function authenticated(req,env){
  const token=env.AI_DASHBOARD_TOKEN;
  if(typeof token!=="string"||token.length<24)return false;
  const header=req.headers.get("authorization")||"";
  if(!header.startsWith("Bearer "))return false;
  const candidate=header.slice(7);
  // Compare full bytes without timing short circuits.
  const enc=new TextEncoder(),a=enc.encode(candidate),b=enc.encode(token);
  let diff=a.length^b.length;
  const n=Math.max(a.length,b.length);
  for(let i=0;i<n;i++)diff|=(a[i]||0)^(b[i]||0);
  return diff===0;
}
function sameOrigin(req){
  const origin=req.headers.get("origin");
  return !origin||origin===new URL(req.url).origin;
}
function validMessage(s){return typeof s==="string"&&s.trim().length>=3&&s.length<=MAX_MESSAGE&&!DENY.test(s)&&!/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(s)}
function objectKey(){const stamp=new Date().toISOString();return PREFIX+stamp.slice(0,10)+"/"+stamp.slice(11).replace(/[:.]/g,"-")+"-"+crypto.randomUUID()+".json"}
async function inbox(req,env){
  if(req.method==="GET"){
    // Timestamp-prefixed keys; R2 lists lexicographically in most buckets.
    const result=await env.AI_CENTRAL_R2.list({prefix:PREFIX,limit:100});
    const keys=result.objects.map(x=>x.key).filter(k=>k.endsWith(".json")).sort().reverse().slice(0,30);
    const items=await Promise.all(keys.map(async key=>{
      const obj=await env.AI_CENTRAL_R2.get(key);
      if(!obj)return null;
      const body=await obj.json();
      return {id:body.id,created_at:body.created_at,channel:body.channel,status:body.status,kind:body.kind,
        message:body.message||"",file:body.file?{name:body.file.name,mime:body.file.mime,size:body.file.size}:null};
    }));
    return json({schema:"AI-INBOX-V1",items:items.filter(Boolean)});
  }
  if(req.method==="POST"){
    if(!sameOrigin(req))return json({error:"origin rejected"},403);
    const length=Number(req.headers.get("content-length")||0);
    if(length>12000)return json({error:"too large"},413);
    let body;
    try{body=await req.json()}catch{return json({error:"invalid json"},400)}
    if(!body||Object.keys(body).sort().join(",")!=="message"||!validMessage(body.message))return json({error:"invalid message"},400);
    const id=crypto.randomUUID(),created_at=new Date().toISOString(),key=objectKey();
    const task={schema:"AI-INBOX-V1",id,created_at,channel:"web",kind:"message",
      message:body.message.trim(),status:"DRAFT_REQUIRES_REVIEW",auto_dispatch:false};
    await env.AI_CENTRAL_R2.put(key,JSON.stringify(task),{httpMetadata:{contentType:"application/json"}});
    return json({id,created_at,status:task.status},202);
  }
  return json({error:"method"},405);
}
async function upload(req,env){
  if(req.method!=="POST")return json({error:"method"},405);
  if(!sameOrigin(req))return json({error:"origin rejected"},403);
  const mime=(req.headers.get("content-type")||"").split(";")[0].trim().toLowerCase();
  if(!TYPES.has(mime))return json({error:"unsupported file type"},415);
  const len=Number(req.headers.get("content-length")||0);
  if(len>MAX_FILE)return json({error:"file too large"},413);
  const bytes=await req.arrayBuffer();
  if(!bytes.byteLength||bytes.byteLength>MAX_FILE)return json({error:"invalid file size"},413);
  const rawName=req.headers.get("x-upload-name")||"upload";
  const name=rawName.replace(/[^a-zA-Z0-9._-]/g,"_").slice(0,85);
  const id=crypto.randomUUID(),created_at=new Date().toISOString();
  const key="ai-central/v1/uploads/"+id+"/data";
  await env.AI_CENTRAL_R2.put(key,bytes,{httpMetadata:{contentType:mime}});
  const task={schema:"AI-INBOX-V1",id,created_at,channel:"web",kind:"file",message:"",
    file:{name,mime,size:bytes.byteLength,r2_key:key},status:"DRAFT_REQUIRES_REVIEW",auto_dispatch:false};
  await env.AI_CENTRAL_R2.put(objectKey(),JSON.stringify(task),{httpMetadata:{contentType:"application/json"}});
  return json({id,created_at,status:task.status,name},202);
}

// An explicit human click may queue ONE reviewed text task. No provider billing is
// possible unless an independent admin has verified the free account/limit.
async function queueReviewed(req,env){
  if(req.method!=="POST")return json({error:"method"},405);
  if(!sameOrigin(req))return json({error:"origin rejected"},403);
  if(env.AI_CENTRAL_FREE_TIER_VERIFIED!=="true")
    return json({error:"No verified free-tier inference budget: dispatch disabled"},409);
  if(!env.GITHUB_DISPATCH_TOKEN)
    return json({error:"GitHub dispatch not configured"},503);
  let body;try{body=await req.json()}catch{return json({error:"invalid json"},400)}
  const id=body?.id,date=body?.date;
  if(Object.keys(body||{}).sort().join(",")!=="date,id"||
    typeof id!=="string"||!/^[A-Za-z0-9_-]{10,64}$/.test(id)||
    typeof date!=="string"||!/^20\d{2}-\d\d-\d\d$/.test(date)||
    !Number.isFinite(Date.parse(date+"T00:00:00Z"))||
    new Date(date+"T00:00:00Z").toISOString().slice(0,10)!==date)
    return json({error:"invalid task reference"},400);
  const listing=await env.AI_CENTRAL_R2.list({prefix:PREFIX+date+"/",limit:100});
  if(listing.truncated)return json({error:"inbox scan limit reached"},409);
  let found=null;
  for(const entry of listing.objects){
    if(!entry.key.endsWith(".json"))continue;
    const obj=await env.AI_CENTRAL_R2.get(entry.key);
    if(!obj)continue;
    const v=await obj.json();
    if(v.id!==id)continue;
    if(found)return json({error:"ambiguous task reference"},409);
    found={key:entry.key,doc:v};
  }
  if(!found)return json({error:"unknown task"},404);
  const d=found.doc;
  if(d.kind!=="message"||d.status!=="DRAFT_REQUIRES_REVIEW"||d.auto_dispatch!==false)
    return json({error:"not an unprocessed text draft"},409);
  // Keep original message unchanged; state is an explicit user-approved intent.
  const queued={...d,status:"QUEUED_FREE_REVIEW",approved_at:new Date().toISOString(),
    dispatch_target:"ai-central-inbox-agent.yml",inference_scope:"free-tier-opt-in-only"};
  await env.AI_CENTRAL_R2.put(found.key,JSON.stringify(queued),{httpMetadata:{contentType:"application/json"}});
  let response;
  try{
    response=await fetch("https://api.github.com/repos/Edirne22/KI-SOCIAL-AGENT/actions/workflows/ai-central-inbox-agent.yml/dispatches",{
      method:"POST",headers:{"authorization":"Bearer "+env.GITHUB_DISPATCH_TOKEN,
        "accept":"application/vnd.github+json","x-github-api-version":"2022-11-28",
        "user-agent":"Edirne22-Private-AI-Central"},
      body:JSON.stringify({ref:"main",inputs:{inbox_date:date,inbox_id:id}})});
  }catch{
    await env.AI_CENTRAL_R2.put(found.key,JSON.stringify(d),{httpMetadata:{contentType:"application/json"}});
    return json({error:"GitHub dispatch unavailable; original draft retained"},502);
  }
  if(response.status!==204){
    await env.AI_CENTRAL_R2.put(found.key,JSON.stringify(d),{httpMetadata:{contentType:"application/json"}});
    return json({error:"GitHub did not accept request; original draft retained",code:response.status},502);
  }
  return json({id,status:"QUEUED_FREE_REVIEW",truth:"GITHUB_DISPATCH_ACCEPTED_NOT_EXECUTION_PROOF"},202);
}
async function taskStatus(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const id=new URL(req.url).searchParams.get("id");
  if(!id||!/^[A-Za-z0-9_-]{10,64}$/.test(id))return json({error:"invalid task id"},400);
  const prefix="ai-central/v1/tasks/"+id+"/runs/";
  const objects=await env.AI_CENTRAL_R2.list({prefix,limit:100});
  const keys=objects.objects.filter(x=>x.key.endsWith("/report.json")).map(x=>x.key).sort().reverse();
  if(!keys.length)return json({id,status:"NO_REPORT_YET",truth:"R2_REPORT_NOT_FOUND"});
  const report=await env.AI_CENTRAL_R2.get(keys[0]);
  if(!report)return json({id,status:"NO_REPORT_YET",truth:"R2_REPORT_NOT_FOUND"});
  const data=await report.json();
  if(data.schema!=="CLOUD-AI-CENTRAL-V1"||data.task_id!==id)
    return json({error:"invalid stored report"},502);
  // Avoid exposing other task messages; show only reviewed result states and sanitized AI text.
  return json({id,status:data.status,truth:"R2_ARCHIVED_REPORT",run_id:data.run_id,
    utc:data.utc,roles:(data.results||[]).map(v=>({role:v.role,status:v.status,
      attempts:(v.attempts||[]).map(a=>({provider:a.provider,model:a.model||"",
        status:a.status,text:typeof a.text==="string"?a.text.slice(0,5500):undefined}))}))});
}

export default {async fetch(req,env){
  const path=new URL(req.url).pathname;
  if(!path.startsWith("/api/"))return env.ASSETS.fetch(req);
  if(!env.AI_CENTRAL_R2)return json({error:"storage unavailable"},503);
  if(!authenticated(req,env))return json({error:"unauthorized"},401);
  try{
    if(path==="/api/inbox")return await inbox(req,env);
    if(path==="/api/upload")return await upload(req,env);
    if(path==="/api/dispatch")return await queueReviewed(req,env);
    if(path==="/api/task")return await taskStatus(req,env);
    if(path==="/api/runs"){
      const response=await fetch("https://api.github.com/repos/Edirne22/KI-SOCIAL-AGENT/actions/runs?per_page=15",{
        headers:{"accept":"application/vnd.github+json","user-agent":"Edirne22-AI-Central-Dashboard",
          ...(env.GITHUB_STATUS_TOKEN?{"authorization":"Bearer "+env.GITHUB_STATUS_TOKEN}:{})}});
      if(!response.ok)return json({error:"GitHub status unavailable",code:response.status},502);
      const data=await response.json();
      const allowed=["Cloud AI Central","OpenChatCut"];
      const runs=(data.workflow_runs||[]).filter(r=>allowed.some(n=>(r.name||"").includes(n)))
        .slice(0,8).map(r=>({id:r.id,name:r.name,status:r.status,conclusion:r.conclusion,
          started_at:r.run_started_at,updated_at:r.updated_at,url:r.html_url}));
      return json({truth:"GITHUB_RUN_STATUS",runs,logged_at:new Date().toISOString()});
    }
    if(path==="/api/health")return json({ok:true,truth:"WORKER_AND_R2_BINDING_PRESENT",live_models:false});
    return json({error:"not found"},404);
  }catch(err){console.error("dashboard_api",err instanceof Error?err.name:"unknown");return json({error:"request failed"},500)}
}};
