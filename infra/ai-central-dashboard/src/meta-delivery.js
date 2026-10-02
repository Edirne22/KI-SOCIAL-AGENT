// Block 9: short-lived capability URL for Meta's fetcher ONLY.
// No public R2 bucket, no listing, no way to issue a grant from this Worker.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const SECRET=/^[a-zA-Z0-9_-]{43}$/;
const DIGEST=/^[0-9a-f]{64}$/;
const MAX_BYTES=32*1024*1024;
const GRANT_PREFIX="ai-central/v1/meta-delivery/grants/";
const JOB_PREFIX="ai-central/v1/factory-jobs/";
const encoder=new TextEncoder();
function reject(code){return new Response(null,{status:code,headers:{"cache-control":"private, no-store"}})}
function equal(a,b){
  const left=encoder.encode(a),right=encoder.encode(b);
  let mismatch=left.length^right.length;
  for(let i=0;i<Math.max(left.length,right.length);i++)mismatch|=(left[i]||0)^(right[i]||0);
  return mismatch===0;
}
function validEvidence(job){
  const e=job?.publish_payload?.editorial_evidence;
  const human=job?.metadata?.[`human_post:r${job?.revision}`];
  return job?.status==="publish_queued" &&
    job?.human_approved_revision===job?.revision &&
    DIGEST.test(job?.human_approved_manifest||"") &&
    job?.publish_handoff_key===`${job.job_id}:r${job.revision}:${job.human_approved_manifest.slice(0,16)}` &&
    job.instruction!=="block6-verified-source" &&
    job.metadata?.technical_test_only!==true &&
    job.metadata?.synthetic_test_only!==true &&
    e?.source_fact_contract===true && e?.human_writing===true &&
    e?.media_rights===true && e?.synthetic===false &&
    typeof e.final_qm_report_id==="string" && e.final_qm_report_id.trim().length>0 &&
    human?.actor==="authenticated_dashboard_owner" &&
    human.revision===job.revision &&
    human.manifest===job.human_approved_manifest &&
    UUID.test(human?.request_id||"");
}
export async function serveMetaDelivery(req,env){
  // Not the dashboard's Bearer auth: Meta cannot attach headers. A high-entropy
  // ephemeral capability, stored only as a hash, is the sole fetch authority.
  if(req.method!=="GET"&&req.method!=="HEAD")return reject(405);
  const url=new URL(req.url);
  const id=url.searchParams.get("id")||"",token=url.searchParams.get("token")||"";
  if(!UUID.test(id)||!SECRET.test(token)||[...url.searchParams.keys()].sort().join(",")!=="id,token")
    return reject(404);
  const obj=await env.AI_CENTRAL_R2.get(GRANT_PREFIX+id+".json");
  if(!obj||obj.size>4096)return reject(404);
  let grant;try{grant=await obj.json()}catch{return reject(404)}
  if(grant?.schema!=="META-PRIVATE-R2-DELIVERY-V1"||grant.id!==id||
    !UUID.test(grant.job_id||"")||!UUID.test(grant.media_id||"")||
    !DIGEST.test(grant.sha256||"")||!DIGEST.test(grant.token_sha256||"")||
    !DIGEST.test(grant.approval_manifest||"")||
    !Number.isInteger(grant.size_bytes)||grant.size_bytes<1||grant.size_bytes>MAX_BYTES||
    grant.mime_type!=="video/mp4"||
    typeof grant.key!=="string"||!grant.key.startsWith("media/"+grant.media_id+"/")||
    grant.key.includes("..")||!/^media\/[0-9a-f-]+\/[A-Za-z0-9._-]+\.mp4$/.test(grant.key))
    return reject(404);
  const expire=Date.parse(grant.expires_at||""),issued=Date.parse(grant.issued_at||"");
  if(!Number.isFinite(expire)||!Number.isFinite(issued)||issued>Date.now()+60000||
    expire<=Date.now()||expire-issued>2*60*60*1000||expire-issued<=0)
    return reject(410);
  const hash=[...new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(token)))]
    .map(x=>x.toString(16).padStart(2,"0")).join("");
  if(!equal(hash,grant.token_sha256))return reject(404);
  const canonical=await env.AI_CENTRAL_R2.get(JOB_PREFIX+grant.job_id+".json");
  if(!canonical||canonical.size>512*1024)return reject(404);
  let stored;try{stored=await canonical.json()}catch{return reject(404)}
  const job=stored?.job;
  if(stored.schema!=="FACTORY-CANONICAL-R2-JOB-V1"||
    stored.job_id!==grant.job_id||job?.job_id!==grant.job_id||
    !validEvidence(job)||!equal(job.human_approved_manifest,grant.approval_manifest)||
    !equal(job.publish_handoff_key,grant.handoff_key)||
    !Array.isArray(job.media)||job.media.length!==1)
    return reject(404);
  const m=job.media[0];
  if(m.media_id!==grant.media_id||m.sha256!==grant.sha256||
    m.size_bytes!==grant.size_bytes||m.mime_type!=="video/mp4"||
    typeof m.uri!=="string"||!m.uri.startsWith("r2://")||
    !m.uri.endsWith("/"+grant.key))
    return reject(404);
  const media=await env.AI_CENTRAL_R2.get(grant.key);
  if(!media||media.size!==m.size_bytes||
    media.httpMetadata?.contentType!=="video/mp4"||
    media.customMetadata?.sha256!==m.sha256||
    media.customMetadata?.["media-id"]!==m.media_id)
    return reject(404);
  const raw=await media.arrayBuffer();
  if(raw.byteLength!==m.size_bytes)return reject(404);
  const bytesHash=[...new Uint8Array(await crypto.subtle.digest("SHA-256",raw))]
    .map(x=>x.toString(16).padStart(2,"0")).join("");
  if(!equal(bytesHash,m.sha256))return reject(404);
  // HEAD is useful for provider preflight, but is held to the SAME checks.
  return new Response(req.method==="HEAD"?null:raw,{headers:{
    "content-type":"video/mp4","content-length":String(raw.byteLength),
    "cache-control":"private, no-store, max-age=0",
    "x-content-type-options":"nosniff",
    "content-disposition":"inline; filename=\"approved-reel.mp4\"",
    "accept-ranges":"none"
  }});
}
