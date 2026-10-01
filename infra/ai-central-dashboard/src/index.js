// Cloudflare Worker: private, bounded control inbox for web and Telegram.
// R2 is object storage; no model output or uploaded file is ever executed.
const ROOT = "ai-central/v1/";
const SCHEMA = "EDIRNE22-CONTROL-INBOX-V1";
const ID = /^[0-9a-f]{8}-[0-9a-f-]{27,28}$/i;
function respond(value, status=200) {
  return new Response(JSON.stringify(value), {status, headers: {"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}});
}
function equal(a,b) {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  if (!x.length || x.length !== y.length) return false;
  let diff=0;for(let i=0;i<x.length;i++) diff|=x[i]^y[i];
  return diff===0;
}
function originOK(request) {
  // Same-origin only: browser requests must provide Origin matching this host.
  const o=request.headers.get("origin");
  return !o || o===new URL(request.url).origin;
}
function auth(request, env) {
  const token=env.CONTROL_CENTER_TOKEN || "";
  const submitted=request.headers.get("x-control-center-token") || "";
  return token.length >= 24 && equal(token, submitted);
}
function clean(entry) {
  if (!entry || entry.schema!==SCHEMA || typeof entry.text!=="string")return null;
  return {request_id:entry.request_id,channel:entry.channel,created_at:entry.created_at,
    status:entry.status,text:entry.text,source_id:entry.source_id};
}
export default {
  async fetch(request,env) {
    const url=new URL(request.url);
    if (!url.pathname.startsWith("/api/"))return new Response("not found",{status:404});
    if (!originOK(request))return respond({error:"origin denied"},403);
    if (!auth(request,env))return respond({error:"unauthorized"},401);
    if (!env.AI_CENTRAL_R2)return respond({error:"R2 binding missing"},503);
    if (url.pathname==="/api/ping" && request.method==="GET")
      return respond({ok:true,service:"edirne22-control-center",mode:"inbox-only"});
    if (url.pathname==="/api/tasks" && request.method==="POST") {
      const len=Number(request.headers.get("content-length")||0);
      if (len>4096)return respond({error:"payload too large"},413);
      let input;try{input=await request.json()}catch{return respond({error:"invalid json"},400)}
      if (!input || typeof input.text!=="string" || !input.text.trim() || input.text.length>2500 ||
          /[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]/.test(input.text))
        return respond({error:"invalid text"},400);
      const request_id=crypto.randomUUID();
      const data={schema:SCHEMA,request_id,channel:"web",source_id:null,
        created_at:new Date().toISOString(),status:"PENDING_REVIEW",text:input.text.trim(),approval:null};
      await env.AI_CENTRAL_R2.put(ROOT+"inbox/"+request_id+".json",JSON.stringify(data),{
        httpMetadata:{contentType:"application/json"}});
      return respond(clean(data),201);
    }
    if (url.pathname==="/api/tasks" && request.method==="GET") {
      // Bounded listing of both sources (last 25 objects from each prefix).
      const names=[ROOT+"inbox/",ROOT+"telegram-updates/"];
      const found=await Promise.all(names.map(prefix=>env.AI_CENTRAL_R2.list({prefix,limit:50})));
      const keys=found.flatMap(x=>x.objects.map(o=>o.key)).slice(0,100);
      const items=await Promise.all(keys.map(async key=>{
        try {const o=await env.AI_CENTRAL_R2.get(key);return o?clean(await o.json()):null} catch{return null}
      }));
      const sorted=items.filter(Boolean).sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at))).slice(0,30);
      return respond({items:sorted,mode:"inbox-only",updated_at:new Date().toISOString()});
    }
    if (url.pathname==="/api/uploads" && request.method==="POST") {
      const limit=8*1024*1024;
      const len=Number(request.headers.get("content-length")||0);
      if (len>limit || len<1)return respond({error:"file must be 1B–8MB"},413);
      const type=(request.headers.get("content-type")||"").split(";")[0].toLowerCase();
      const allow=["image/png","image/jpeg","image/webp","audio/webm","audio/mp4","audio/mpeg",
        "application/pdf","text/plain"];
      if(!allow.includes(type))return respond({error:"file type not allowed"},415);
      const content=await request.arrayBuffer();
      if(content.byteLength<1 || content.byteLength>limit)return respond({error:"invalid file size"},413);
      const file_id=crypto.randomUUID();
      const key=ROOT+"uploads/"+file_id;
      await env.AI_CENTRAL_R2.put(key,content,{httpMetadata:{contentType:type},
        customMetadata:{source:"web",review:"pending",created:new Date().toISOString()}});
      return respond({file_id,size:content.byteLength,type,status:"PENDING_REVIEW",
        note:"Private upload only; attach to a reviewed task separately."},201);
    }
    return respond({error:"not found"},404);
  }
};
