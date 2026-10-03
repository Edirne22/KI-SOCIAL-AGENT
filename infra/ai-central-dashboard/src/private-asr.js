// Authenticated dashboard-only private ASR consent and draft reader.
// Route registration must remain BEHIND the existing bearer-auth gate.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const SHA=/^[0-9a-f]{64}$/;
const AUDIO=new Set(["audio/webm","audio/mp4","audio/ogg"]);
const PREFIX="ai-central/v1/private-asr/";
const MAX=8*1024*1024;
const reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json","cache-control":"private, no-store"}});
async function source(req,env){
  const q=new URL(req.url).searchParams,id=q.get("id")||"",date=q.get("date")||"";
  if(!UUID.test(id)||!/^20\d\d-\d\d-\d\d$/.test(date)||
    Number.isNaN(Date.parse(date+"T00:00:00Z"))||
    new Date(date+"T00:00:00Z").toISOString().slice(0,10)!==date)return null;
  const listing=await env.AI_CENTRAL_R2.list({prefix:"ai-central/v1/inbox/"+date+"/",limit:1000});
  if(listing.truncated)return null;
  const matches=[];
  for(const obj of listing.objects){
    if(!obj.key.endsWith(".json"))continue;
    const raw=await env.AI_CENTRAL_R2.get(obj.key);
    if(!raw)continue;
    let item;try{item=await raw.json()}catch{continue}
    if(item.id===id)matches.push(item);
  }
  if(matches.length!==1)return null;
  const item=matches[0],f=item.file||{};
  if(item.schema!=="AI-INBOX-V1"||item.kind!=="file"||item.channel!=="web"||
     item.created_at?.slice(0,10)!==date||f.r2_key!=="ai-central/v1/uploads/"+id+"/data"||
     !AUDIO.has(f.mime)||!Number.isSafeInteger(f.size)||f.size<1||f.size>MAX)return null;
  const original=await env.AI_CENTRAL_R2.get(f.r2_key);
  if(!original||original.size!==f.size||original.httpMetadata?.contentType!==f.mime)return null;
  const bytes=await original.arrayBuffer();
  if(bytes.byteLength!==f.size)return null;
  const digest=[...new Uint8Array(await crypto.subtle.digest("SHA-256",bytes))]
    .map(x=>x.toString(16).padStart(2,"0")).join("");
  return {id,digest};
}
export async function privateASR(req,env){
  const src=await source(req,env);
  if(!src)return reply({error:"canonical private audio unavailable"},404);
  const root=PREFIX+src.id+"/",consentKey=root+"consent.json";
  if(req.method==="POST"){
    if(req.headers.get("origin")!==new URL(req.url).origin)return reply({error:"origin required"},403);
    let body;try{body=await req.json()}catch{return reply({error:"invalid request"},400)}
    if(!body||Object.keys(body).sort().join(",")!=="language"||!["de","tr"].includes(body.language))
      return reply({error:"explicit language required"},400);
    // Human action in UI; no existing audio is automatically consented.
    await env.AI_CENTRAL_R2.put(consentKey,JSON.stringify({
      schema:"PRIVATE-ASR-CONSENT-V1",inbox_id:src.id,source_sha256:src.digest,
      scope:"transcription",status:"granted",language:body.language,
      granted_at:new Date().toISOString()
    }),{httpMetadata:{contentType:"application/json"}});
    // Dispatch only after explicit user consent. No audio or secrets enter GitHub.
    if(!env.PRIVATE_ASR_SERVICE||!env.PRIVATE_ASR_INTERNAL_TOKEN)
      return reply({status:"CONSENT_SAVED_AWAITING_CONTAINER_CONFIGURATION",language:body.language},202);
    try {
      const dispatched=await env.PRIVATE_ASR_SERVICE.fetch("https://edirne22-private-asr.internal/jobs",{
        method:"POST",headers:{"Authorization":"Bearer "+env.PRIVATE_ASR_INTERNAL_TOKEN,"Content-Type":"application/json"},
        body:JSON.stringify({inbox_id:src.id,date:new URL(req.url).searchParams.get("date"),language:body.language})
      });
      if(dispatched.ok)return reply({status:"PRIVATE_DRAFT_REQUESTED",language:body.language},202);
      return reply({status:"CONSENT_SAVED_CONTAINER_UNAVAILABLE",language:body.language},202);
    }catch{
      return reply({status:"CONSENT_SAVED_CONTAINER_UNAVAILABLE",language:body.language},202);
    }
  }
  if(req.method==="DELETE"){
    if(req.headers.get("origin")!==new URL(req.url).origin)return reply({error:"origin required"},403);
    // Revocation overrides any in-flight transcription. Existing transcript
    // remains inaccessible; delete both language variants as best effort.
    await env.AI_CENTRAL_R2.put(consentKey,JSON.stringify({
      schema:"PRIVATE-ASR-CONSENT-V1",inbox_id:src.id,source_sha256:src.digest,
      scope:"transcription",status:"revoked",revoked_at:new Date().toISOString()
    }),{httpMetadata:{contentType:"application/json"}});
    await Promise.all(["de","tr"].map(lang=>env.AI_CENTRAL_R2.delete(root+src.digest+"/"+lang+".json")));
    return reply({status:"REVOKED"},200);
  }
  if(req.method!=="GET")return reply({error:"method"},405);
  const consentObj=await env.AI_CENTRAL_R2.get(consentKey);
  if(!consentObj)return reply({status:"CONSENT_REQUIRED"},200);
  let consent;try{consent=await consentObj.json()}catch{return reply({error:"invalid consent record"},409)}
  if(consent.schema!=="PRIVATE-ASR-CONSENT-V1"||consent.status!=="granted"||
    consent.scope!=="transcription"||consent.inbox_id!==src.id||
    consent.source_sha256!==src.digest||!["de","tr"].includes(consent.language))
    return reply({status:"CONSENT_REQUIRED"},200);
  const key=root+src.digest+"/"+consent.language+".json";
  const obj=await env.AI_CENTRAL_R2.get(key);
  if(!obj)return reply({status:"AWAITING_PRIVATE_CONTAINER_ASR",language:consent.language},200);
  let t;try{t=await obj.json()}catch{return reply({error:"invalid transcript"},409)}
  if(t.schema!=="PRIVATE-ASR-TRANSCRIPT-V1"||t.inbox_id!==src.id||
    t.source_sha256!==src.digest||t.language!==consent.language||
    t.status!=="DRAFT_REQUIRES_HUMAN_REVIEW"||
    typeof t.text!=="string"||!t.text.trim()||t.text.length>2500)
    return reply({error:"transcript source mismatch"},409);
  return reply({status:"PRIVATE_DRAFT_REQUIRES_REVIEW",language:t.language,text:t.text},200);
}
