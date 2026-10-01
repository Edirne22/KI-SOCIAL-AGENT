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
function objectKey(){return PREFIX+new Date().toISOString().replace(/[:.]/g,"-")+"/"+crypto.randomUUID()+".json"}
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
export default {async fetch(req,env){
  const path=new URL(req.url).pathname;
  if(!path.startsWith("/api/"))return env.ASSETS.fetch(req);
  if(!env.AI_CENTRAL_R2)return json({error:"storage unavailable"},503);
  if(!authenticated(req,env))return json({error:"unauthorized"},401);
  try{
    if(path==="/api/inbox")return await inbox(req,env);
    if(path==="/api/upload")return await upload(req,env);
    if(path==="/api/health")return json({ok:true,truth:"WORKER_AND_R2_BINDING_PRESENT",live_models:false});
    return json({error:"not found"},404);
  }catch(err){console.error("dashboard_api",err instanceof Error?err.name:"unknown");return json({error:"request failed"},500)}
}};
