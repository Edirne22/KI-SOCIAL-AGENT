// Cloudflare Worker gateway: R2-backed shared Telegram+Web inbox.
// No provider credentials, workflow tokens, auto-dispatch or approvals in this slice.
const PREFIX="ai-central/v1/inbox/";
const MAX_MESSAGE=2500;
const MAX_FILE=8*1024*1024;
const TYPES=new Set(["text/plain","text/markdown","application/json","image/png","image/jpeg","audio/webm","audio/mp4","audio/ogg","application/pdf"]);
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

// Private user-upload preview; the caller supplies only an opaque inbox UUID and
// original UTC day. The R2 object path is NEVER accepted from a browser.
const UPLOAD_ID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const PREVIEW_MIME=new Set(["image/png","image/jpeg","video/mp4","audio/webm","audio/mp4","audio/ogg","application/pdf"]);
async function privateUploadPreview(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const q=new URL(req.url).searchParams,id=q.get("id")||"",date=q.get("date")||"";
  if(!UPLOAD_ID.test(id)||!/^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/.test(date)||
    !Number.isFinite(Date.parse(date+"T00:00:00Z"))||
    new Date(date+"T00:00:00Z").toISOString().slice(0,10)!==date)
    return json({error:"invalid upload reference"},400);
  const listing=await env.AI_CENTRAL_R2.list({prefix:PREFIX+date+"/",limit:100});
  if(listing.truncated)return json({error:"inbox index exceeds safe scan limit"},409);
  let match=null;
  for(const item of listing.objects){
    if(!item.key.endsWith(".json"))continue;
    const raw=await env.AI_CENTRAL_R2.get(item.key);
    if(!raw)continue;
    let d;try{d=await raw.json()}catch{continue}
    if(d.id!==id)continue;
    if(match)return json({error:"ambiguous upload identity"},409);
    match=d;
  }
  if(!match||match.kind!=="file"||match.channel!=="web"||
    match.created_at?.slice(0,10)!==date||!match.file||
    match.file.r2_key!=="ai-central/v1/uploads/"+id+"/data"||
    !PREVIEW_MIME.has(match.file.mime)||!Number.isSafeInteger(match.file.size)||
    match.file.size<1||match.file.size>MAX_FILE)
    return json({error:"private preview unavailable"},404);
  const file=await env.AI_CENTRAL_R2.get(match.file.r2_key);
  if(!file)return json({error:"private bytes unavailable"},404);
  if(file.size!==match.file.size||file.httpMetadata?.contentType!==match.file.mime)
    return json({error:"file metadata mismatch"},409);
  const bytes=await file.arrayBuffer();
  if(bytes.byteLength!==match.file.size)return json({error:"file size mismatch"},409);
  return new Response(bytes,{headers:{
    "content-type":match.file.mime,"content-length":String(bytes.byteLength),
    "cache-control":"private, no-store, max-age=0","x-content-type-options":"nosniff",
    "content-security-policy":"default-src 'none'; sandbox",
    "content-disposition":"inline"
  }});
}
// R2 size is a bounded, manually invoked object inventory; not billing
// GB-month telemetry. Refuse to show a fabricated complete total when truncated.
async function passiveSystemMonitor(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const q=new URL(req.url).searchParams;
  if(q.get("scope")!=="manual")return json({error:"manual measurement required"},400);
  const measuredAt=new Date().toISOString();
  let cursor,bytes=0,count=0,complete=false;
  for(let page=0;page<10;page++){
    const result=await env.AI_CENTRAL_R2.list({limit:1000,...(cursor?{cursor}:{})});
    for(const item of result.objects){bytes+=item.size;count++}
    if(!result.truncated){complete=true;break}
    if(!result.cursor||result.cursor===cursor)break;
    cursor=result.cursor;
  }
  // Quota reference must be explicitly and independently configured; an
  // instantaneous bucket inventory cannot prove monthly billable GB-month.
  const configured=Number(env.R2_FREE_STORAGE_GB);
  const quota=typeof env.R2_FREE_STORAGE_GB==="string"&&
    env.R2_FREE_STORAGE_GB.trim()!==""&&Number.isFinite(configured)&&
    configured>0&&configured<=100000?configured:null;
  const ratio=complete&&quota!==null?bytes/(1e9*quota):null;
  return json({schema:"AI-CENTRAL-PASSIVE-MONITOR-V1",
    r2:{measurement:complete?"COMPLETE_BUCKET_INVENTORY":"UNAVAILABLE_INCOMPLETE_SCAN",
      occupied_bytes:complete?bytes:null,object_count:complete?count:null,
      measured_at:complete?measuredAt:null,
      allowance_reference_gb:quota,
      allowance_kind:quota!==null?"CONFIGURED_GB_REFERENCE_NOT_ACTUAL_GB_MONTH":"UNCONFIGURED",
      snapshot_ratio:ratio,
      snapshot_warning:ratio!==null&&ratio>=0.85,
      billing_usage_gb_month:null},
    container:{status:"UNKNOWN_NO_PASSIVE_TELEMETRY",
      measured_at:null,readiness_at:null,cpu_percent:null,memory_bytes:null,
      note:"No passive container state or CPU/RAM binding configured; no wake/probe performed."}});
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
  const id=body?.id,date=body?.date,mode=body?.mode||"free-only";
  if(!["free-only","free-team"].includes(mode))return json({error:"invalid inference mode"},400);
  if(!["date,id","date,id,mode"].includes(Object.keys(body||{}).sort().join(","))||
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
    found={key:entry.key,doc:v,etag:obj.etag};
  }
  if(!found)return json({error:"unknown task"},404);
  const d=found.doc;
  if(d.kind!=="message"||!["web","telegram"].includes(d.channel)||
    d.created_at?.slice(0,10)!==date||!validMessage(d.message)||
    d.status!=="DRAFT_REQUIRES_REVIEW"||d.auto_dispatch!==false)
    return json({error:"not an unprocessed text draft"},409);
  // Keep original message unchanged; state is an explicit user-approved intent.
  const queued={...d,status:"QUEUED_FREE_REVIEW",approved_at:new Date().toISOString(),
    dispatch_target:"ai-central-inbox-agent.yml",
    inference_scope:mode==="free-team"?"nvidia/free-team":"free-tier-opt-in-only"};
  if(typeof found.etag!=="string"||!found.etag)return json({error:"R2 optimistic locking unavailable"},503);
  const claimed=await env.AI_CENTRAL_R2.put(found.key,JSON.stringify(queued),{
    httpMetadata:{contentType:"application/json"},onlyIf:{etagMatches:found.etag}});
  if(!claimed)return json({error:"Another request already changed this task"},409);
  let response;
  try{
    response=await fetch("https://api.github.com/repos/Edirne22/KI-SOCIAL-AGENT/actions/workflows/ai-central-inbox-agent.yml/dispatches",{
      method:"POST",headers:{"authorization":"Bearer "+env.GITHUB_DISPATCH_TOKEN,
        "accept":"application/vnd.github+json","x-github-api-version":"2022-11-28",
        "user-agent":"Edirne22-Private-AI-Central"},
      body:JSON.stringify({ref:"main",inputs:{inbox_date:date,inbox_id:id,...(mode==="free-team"?{team_mode:"free-team"}:{})}})});
  }catch{
    // Network failure is ambiguous: GitHub may have accepted the job. NEVER
    // restore DRAFT or silently send a second potentially duplicated request.
    return json({error:"Dispatch outcome uncertain; inspect GitHub before retry",status:"DISPATCH_UNCERTAIN"},502);
  }
  if(response.status!==204){
    if(response.status>=500||response.status===429){
      return json({error:"Dispatch outcome uncertain; inspect GitHub before retry",status:"DISPATCH_UNCERTAIN",code:response.status},502);
    }
    // Explicit rejection can be rolled back, only if another actor has not
    // modified this claimed task in the meantime.
    const restored=await env.AI_CENTRAL_R2.put(found.key,JSON.stringify(d),{
      httpMetadata:{contentType:"application/json"},onlyIf:{etagMatches:claimed.etag}});
    if(!restored)return json({error:"Dispatch rejected but task changed concurrently; inspect current state",code:response.status},409);
    return json({error:"GitHub rejected request; original draft retained",code:response.status},502);
  }
  return json({id,status:"QUEUED_FREE_REVIEW",truth:"GITHUB_DISPATCH_ACCEPTED_NOT_EXECUTION_PROOF"},202);
}
async function taskStatus(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const id=new URL(req.url).searchParams.get("id");
  if(!id||!/^[A-Za-z0-9_-]{10,64}$/.test(id))return json({error:"invalid task id"},400);
  const base="ai-central/v1/tasks/"+id+"/";
  const state=await env.AI_CENTRAL_R2.get(base+"status.json");
  let current=null;
  if(state){
    const item=await state.json();
    if(item.schema!=="AI-CENTRAL-TASK-STATUS-V1"||item.task_id!==id)
      return json({error:"invalid lifecycle provenance"},502);
    if(!/^[0-9]{1,18}$/.test(item.github_run_id||""))
      return json({error:"invalid lifecycle run ID"},502);
    current=item;
  }
  const prefix=base+"runs/";
  const objects=await env.AI_CENTRAL_R2.list({prefix,limit:100});
  if(objects.truncated)return json({error:"report index exceeds safe scan limit"},409);
  // The lifecycle's run ID is authoritative for retry/resume. Never display
  // an old run's AI answer while a newer execution is running or failed.
  const keys=objects.objects.filter(x=>x.key.endsWith("/report.json")).map(x=>x.key);
  const latest=current?base+"runs/"+current.github_run_id+"/report.json":keys.sort().reverse()[0];
  if(!latest){
    return json({id,status:current?.status||"NO_REPORT_YET",
      truth:current?"R2_JOB_LIFECYCLE_NO_COMPLETED_REPORT":"R2_REPORT_NOT_FOUND",
      ...(current?{run_id:current.github_run_id,updated_at:current.updated_at}:{})});
  }
  const report=await env.AI_CENTRAL_R2.get(latest);
  if(!report){
    return json({id,status:current?.status||"NO_REPORT_YET",
      truth:current?"R2_JOB_LIFECYCLE_NO_COMPLETED_REPORT":"R2_REPORT_NOT_FOUND",
      ...(current?{run_id:current.github_run_id,updated_at:current.updated_at}:{})});
  }
  const data=await report.json();
  if(data.schema!=="CLOUD-AI-CENTRAL-V1"||data.task_id!==id||
     (current&&String(data.run_id)!==current.github_run_id))
    return json({error:"invalid stored report"},502);
  // Avoid exposing other task messages; show only reviewed result states and sanitized AI text.
  return json({id,status:data.status,truth:"R2_ARCHIVED_REPORT",run_id:data.run_id,
    utc:data.utc,roles:(data.results||[]).map(v=>({role:v.role,status:v.status,
      attempts:(v.attempts||[]).map(a=>({provider:a.provider,model:a.model||"",
        status:a.status,text:typeof a.text==="string"?a.text.slice(0,5500):undefined}))}))});
}


/* Block 6: server-owned, private R2 preview index. Only the factory may create
   manifests directly in R2, after media integrity + QM checks. The browser can
   only read authenticated previews, never specify arbitrary R2 keys. */
const PREVIEW_PREFIX="ai-central/v1/previews/";
const PREVIEW_STATE_PREFIX="ai-central/v1/preview-state/";
const MAX_PREVIEW_BYTES=32*1024*1024;
const PREVIEW_ID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
function validPreview(d,id){
  const m=d?.media;
  return d?.schema==="FACTORY-MEDIA-PREVIEW-V1"&&d?.preview_id===id&&
    d?.state==="READY_FOR_HUMAN"&&d?.qm_passed===true&&
    typeof d.expires_at==="string"&&Number.isFinite(Date.parse(d.expires_at))&&Date.parse(d.expires_at)>Date.now()&&
    typeof d.job_id==="string"&&d.job_id.length>=10&&Number.isSafeInteger(d.revision)&&d.revision>0&&
    typeof d.manifest==="string"&&/^[a-f0-9]{64}$/.test(d.manifest)&&
    typeof d.caption==="string"&&d.caption.length<=2500&&
    m&&m.mime_type==="video/mp4"&&
    typeof m.media_id==="string"&&m.media_id.length>=10&&
    typeof m.key==="string"&&(m.key.startsWith("content-factory/")||/^media\/[0-9a-f-]{36}\/[^/]+$/.test(m.key))&&
    !m.key.split("/").includes("..")&&!m.key.includes("\\")&&
    Number.isSafeInteger(m.size_bytes)&&m.size_bytes>0&&m.size_bytes<=MAX_PREVIEW_BYTES&&
    typeof m.sha256==="string"&&/^[a-f0-9]{64}$/.test(m.sha256);
}
async function previewManifest(env,id){
  const obj=await env.AI_CENTRAL_R2.get(PREVIEW_PREFIX+id+".json");
  if(!obj)return null;
  let d;
  try{d=await obj.json()}catch{return null}
    if(!validPreview(d,id))return null;
  // An older preview index must not authorize video access after revision.
  if(!PREVIEW_ID.test(d.job_id))return null;
  const stateObj=await env.AI_CENTRAL_R2.get(PREVIEW_STATE_PREFIX+d.job_id+".json");
  if(!stateObj)return null;
  let current;
  try{current=await stateObj.json()}catch{return null}
  if(current?.schema!=="FACTORY-PREVIEW-STATE-V1"||current?.job_id!==d.job_id||
     current?.preview_id!==id||current?.revision!==d.revision||
     current?.manifest!==d.manifest||current?.state!=="READY_FOR_HUMAN")return null;
  // The independent preview pointer is not sufficient authority: the
  // durable canonical job may have been revised, rejected, or superseded
  // before an older pointer is revoked. Never show stale media in that case.
  const canonicalObj=await env.AI_CENTRAL_R2.get("ai-central/v1/factory-jobs/"+d.job_id+".json");
  if(!canonicalObj)return null;
  let canonical;
  try{canonical=await canonicalObj.json()}catch{return null}
  const job=canonical?.job, media=job?.media;
  if(canonical?.schema!=="FACTORY-CANONICAL-R2-JOB-V1"||
     canonical.job_id!==d.job_id||!Number.isSafeInteger(canonical.store_version)||
     canonical.store_version<1||job?.job_id!==d.job_id||
     job.revision!==d.revision||job.status!=="ready_for_human"||
     job?.publish_payload?.caption!==d.caption||
     !Array.isArray(media)||media.length!==1||
     media[0]?.media_id!==d.media.media_id||
     media[0]?.sha256!==d.media.sha256||
     media[0]?.size_bytes!==d.media.size_bytes||
     media[0]?.mime_type!==d.media.mime_type||
     typeof media[0]?.uri!=="string"||
     !media[0].uri.startsWith("r2://")||
     !media[0].uri.endsWith("/"+d.media.key))
    return null;
  return d;
}
// Block 8: authenticated *review requests*, not a publisher or a forged
// ProductionJob approval. R2 etag CAS prevents duplicate/change races.
// The downstream canonical Factory must apply the request and perform its
// own persisted job/revision/manifest revalidation before any real action.
async function queuePreviewReview(req,env){
  if(req.method!=="POST")return json({error:"method"},405);
  if(!sameOrigin(req))return json({error:"origin rejected"},403);
  if(Number(req.headers.get("content-length")||0)>4000)return json({error:"review request too large"},413);
  let input;
  try{input=await req.json()}catch{return json({error:"invalid JSON"},400)}
  if(!input||Object.keys(input).sort().join(",")!=="action,manifest,preview_id,request_id,revision,text"||
     !PREVIEW_ID.test(input.preview_id)||!PREVIEW_ID.test(input.request_id)||
     !/^[a-f0-9]{64}$/.test(input.manifest)||!Number.isSafeInteger(input.revision)||
     !["change","discard","post"].includes(input.action)||
     typeof input.text!=="string"||input.text.length>2000||
     (input.action==="change"&&!input.text.trim())||
     (input.action!=="change"&&input.text!==""))
    return json({error:"invalid review request"},400);
  // Synthetic and unproven editorial jobs must never enter publish queue.
  // Post stays disabled until a canonical authenticated approval adapter
  // can prove real FINAL QM and restore the exact persisted ProductionJob.
  if(input.action==="post")
    return json({error:"canonical publishing approval not connected; post blocked"},409);
  const d=await previewManifest(env,input.preview_id);
  if(!d||d.manifest!==input.manifest||d.revision!==input.revision)
    return json({error:"stale, expired or unavailable preview"},409);
  // A preview generated on an ephemeral runner before canonical R2 job
  // storage existed may remain playable, but is NOT an actionable review.
  const canonicalObj=await env.AI_CENTRAL_R2.get("ai-central/v1/factory-jobs/"+d.job_id+".json");
  if(!canonicalObj)return json({error:"canonical Factory job not yet persisted"},409);
  let canonical;
  try{canonical=await canonicalObj.json()}catch{return json({error:"canonical Factory job unavailable"},502)}
  const job=canonical?.job;
  const matchingMedia=job?.media?.length===1&&job.media[0]?.media_id===d.media.media_id&&
      job.media[0]?.sha256===d.media.sha256&&job.media[0]?.size_bytes===d.media.size_bytes&&
      job.media[0]?.mime_type===d.media.mime_type&&
      job.media[0]?.uri?.endsWith("/"+d.media.key);
  if(canonical?.schema!=="FACTORY-CANONICAL-R2-JOB-V1"||
     canonical?.job_id!==d.job_id||!Number.isSafeInteger(canonical.store_version)||
     canonical.store_version<1||job?.job_id!==d.job_id||job?.revision!==d.revision||
     job?.status!=="ready_for_human"||!matchingMedia)
    return json({error:"review not bound to current canonical Factory media"},409);
  const stateKey=PREVIEW_STATE_PREFIX+d.job_id+".json";
  const currentObj=await env.AI_CENTRAL_R2.get(stateKey);
  if(!currentObj?.etag)return json({error:"atomic state claim unavailable"},503);
  let state;
  try{state=await currentObj.json()}catch{return json({error:"invalid state"},502)}
  if(state?.schema!=="FACTORY-PREVIEW-STATE-V1"||
     state.job_id!==d.job_id||state.preview_id!==d.preview_id||
     state.revision!==d.revision||state.manifest!==d.manifest||
     state.state!=="READY_FOR_HUMAN")
    return json({error:"preview state changed"},409);
  // Do not mutate the canonical job. Persist immutable reviewer intent and
  // revoke the preview atomically as ONE state object. A downstream consumer
  // is responsible for job-state transitions and reporting actual completion.
  const queued={...state,state:"REVIEW_REQUESTED",preview_id:null,
    review:{schema:"FACTORY-REVIEW-INTENT-V1",request_id:input.request_id,
      preview_id:d.preview_id,action:input.action,text:input.text.trim(),
      actor:"authenticated_dashboard_owner",requested_at:new Date().toISOString(),
      manifest:d.manifest,revision:d.revision,job_id:d.job_id,status:"PENDING_FACTORY_APPLICATION"}};
  let claimed;
  try{claimed=await env.AI_CENTRAL_R2.put(stateKey,JSON.stringify(queued),{
    httpMetadata:{contentType:"application/json"},onlyIf:{etagMatches:currentObj.etag}});
  }catch{return json({error:"review state storage failed"},503)}
  if(!claimed)return json({error:"review request changed concurrently"},409);
  // A real canonical review runs only after the R2 claim commits. A lost
  // dispatch response cannot justify restoring the old preview or sending
  // duplicate state transitions: the Factory deduplicates by request UUID.
  let dispatch="NOT_CONFIGURED";
  if(env.GITHUB_DISPATCH_TOKEN){
    try{
      const run=await fetch("https://api.github.com/repos/Edirne22/KI-SOCIAL-AGENT/actions/workflows/block8-dashboard-review-consumer.yml/dispatches",{
        method:"POST",headers:{"authorization":"Bearer "+env.GITHUB_DISPATCH_TOKEN,
          "accept":"application/vnd.github+json","x-github-api-version":"2022-11-28",
          "user-agent":"Edirne22-Private-Factory-Review"},
        body:JSON.stringify({ref:"main",inputs:{job_id:d.job_id}})});
      dispatch=run.status===204?"ACCEPTED":"PENDING_MANUAL_RECONCILIATION";
    }catch{dispatch="PENDING_MANUAL_RECONCILIATION"}
  }
  return json({schema:"FACTORY-REVIEW-INTENT-V1",request_id:input.request_id,
    job_id:d.job_id,status:"PENDING_FACTORY_APPLICATION",action:input.action,
    dispatch,truth:"REVIEW_INTENT_STORED_NOT_JOB_DECISION"},202);
}
// Persisted, authenticated read-only status across browser refreshes. Never
// infer approval from a queued intent; only the canonical Factory ACK counts.
async function listReviewStatuses(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const result=await env.AI_CENTRAL_R2.list({prefix:PREVIEW_STATE_PREFIX,limit:80});
  if(result.truncated)return json({error:"review index too large; pagination required"},409);
  const keys=result.objects.filter(o=>PREVIEW_ID.test(
    o.key.slice(PREVIEW_STATE_PREFIX.length,-5))&&o.key.endsWith(".json")).slice(-60);
  const items=[];
  for(const entry of keys){
    const job_id=entry.key.slice(PREVIEW_STATE_PREFIX.length,-5);
    const object=await env.AI_CENTRAL_R2.get(entry.key);
    if(!object)continue;
    let state;
    try{state=await object.json()}catch{continue}
    const review=state?.review;
    if(state?.schema!=="FACTORY-PREVIEW-STATE-V1"||state.job_id!==job_id||
       !["REVIEW_REQUESTED","REVIEW_APPLIED"].includes(state.state)||
       state.preview_id!==null||!review||
       review.schema!=="FACTORY-REVIEW-INTENT-V1"||
       review.job_id!==job_id||review.actor!=="authenticated_dashboard_owner"||
       !PREVIEW_ID.test(review.request_id||"")||
       !["change","discard"].includes(review.action)||
       review.manifest!==state.manifest||review.revision!==state.revision||
       !Number.isFinite(Date.parse(review.requested_at||"")))continue;
    const applied=state.state==="REVIEW_APPLIED"&&review.status==="APPLIED_TO_FACTORY";
    if(!applied&&!(state.state==="REVIEW_REQUESTED"&&
       review.status==="PENDING_FACTORY_APPLICATION"))continue;
    items.push({job_id,request_id:review.request_id,revision:review.revision,
      action:review.action,status:applied?"APPLIED_TO_FACTORY":"PENDING_FACTORY_APPLICATION",
      requested_at:review.requested_at});
  }
  items.sort((a,b)=>b.requested_at.localeCompare(a.requested_at));
  return json({schema:"FACTORY-REVIEW-STATUS-LIST-V1",items:items.slice(0,30)});
}
async function reviewStatus(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const query=new URL(req.url).searchParams;
  const job_id=query.get("job_id"),request_id=query.get("request_id");
  if(!PREVIEW_ID.test(job_id||"")||!PREVIEW_ID.test(request_id||""))
    return json({error:"invalid review reference"},400);
  const object=await env.AI_CENTRAL_R2.get(PREVIEW_STATE_PREFIX+job_id+".json");
  if(!object)return json({error:"review not found"},404);
  let state;try{state=await object.json()}catch{return json({error:"review unavailable"},502)}
  const review=state?.review;
  if(state?.job_id!==job_id||review?.request_id!==request_id||
     !["REVIEW_REQUESTED","REVIEW_APPLIED"].includes(state?.state))
    return json({error:"review no longer current"},404);
  return json({schema:"FACTORY-REVIEW-STATUS-V1",job_id,request_id,
    status:state.state==="REVIEW_APPLIED"&&review.status==="APPLIED_TO_FACTORY"?
      "APPLIED_TO_FACTORY":"PENDING_FACTORY_APPLICATION",
    action:review.action,truth:"READ_FROM_PRIVATE_R2_REVIEW_STATE"});
}
async function listPreviews(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const result=await env.AI_CENTRAL_R2.list({prefix:PREVIEW_PREFIX,limit:80});
  if(result.truncated)return json({error:"preview index too large; use pagination"},409);
  const keys=result.objects.filter(x=>/^[0-9a-f-]{36}\.json$/.test(x.key.slice(PREVIEW_PREFIX.length))).slice(-30).reverse();
  const items=[];
  for(const k of keys){
    const id=k.key.slice(PREVIEW_PREFIX.length,-5);
    if(!PREVIEW_ID.test(id))continue;
    const d=await previewManifest(env,id);
    if(d)items.push({id,job_id:d.job_id,revision:d.revision,caption:d.caption,
      mime_type:d.media.mime_type,size_bytes:d.media.size_bytes,manifest:d.manifest});
  }
  return json({schema:"FACTORY-PREVIEW-LIST-V1",items});
}
async function getPreviewVideo(req,env){
  if(req.method!=="GET")return json({error:"method"},405);
  const id=new URL(req.url).searchParams.get("id")||"";
  if(!PREVIEW_ID.test(id))return json({error:"invalid preview"},400);
  const d=await previewManifest(env,id);
  if(!d)return json({error:"preview not ready or unavailable"},404);
  // Require an independent R2-stored SHA marker as well as the verified
  // factory manifest. Never stream bytes solely because a JSON key says so.
  const obj=await env.AI_CENTRAL_R2.get(d.media.key);
  if(!obj)return json({error:"media unavailable"},404);
  if(obj.size!==d.media.size_bytes||obj.httpMetadata?.contentType!=="video/mp4"||
    obj.customMetadata?.sha256!==d.media.sha256)
    return json({error:"media metadata mismatch"},409);
  const data=await obj.arrayBuffer();
  if(data.byteLength!==d.media.size_bytes)return json({error:"media size mismatch"},409);
  const hash=[...new Uint8Array(await crypto.subtle.digest("SHA-256",data))]
    .map(v=>v.toString(16).padStart(2,"0")).join("");
  if(hash!==d.media.sha256)return json({error:"media integrity mismatch"},409);
  return new Response(data,{headers:{
    "content-type":"video/mp4","content-length":String(data.byteLength),
    "cache-control":"private, no-store, max-age=0","x-content-type-options":"nosniff",
    "content-disposition":"inline; filename=\"factory-preview.mp4\"",
    "accept-ranges":"none"
  }});
}

export default {async fetch(req,env){
  const path=new URL(req.url).pathname;
  if(!path.startsWith("/api/"))return env.ASSETS.fetch(req);
  if(!env.AI_CENTRAL_R2)return json({error:"storage unavailable"},503);
  if(!authenticated(req,env))return json({error:"unauthorized"},401);
  try{
    if(path==="/api/previews")return await listPreviews(req,env);
    if(path==="/api/preview-review")return await queuePreviewReview(req,env);
    if(path==="/api/reviews")return await listReviewStatuses(req,env);
    if(path==="/api/review-status")return await reviewStatus(req,env);
    if(path==="/api/preview-video")return await getPreviewVideo(req,env);
    if(path==="/api/inbox")return await inbox(req,env);
    if(path==="/api/upload")return await upload(req,env);
    if(path==="/api/upload-preview")return await privateUploadPreview(req,env);
    if(path==="/api/system-monitor")return await passiveSystemMonitor(req,env);
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
