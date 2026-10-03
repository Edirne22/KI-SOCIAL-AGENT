import test from "node:test";
import assert from "node:assert/strict";
import {randomUUID} from "node:crypto";
import {readFileSync} from "node:fs";
import vm from "node:vm";
import worker from "../src/index.js";

const TOKEN="block8-owner-edit-status-verified-test-token";
const BASE="https://dashboard.example";
const R2="private-factory-test";
function fixture(){
  const objects=new Map();
  const store={
    async get(key){const body=objects.get(key);return body?{json:async()=>structuredClone(body)}:null}
  };
  const env={AI_DASHBOARD_TOKEN:TOKEN,AI_CENTRAL_R2:store,
    ASSETS:{fetch:async()=>new Response("ui")}};
  const jobId=randomUUID(),requestId=randomUUID(),previewId=randomUUID(),
    mediaId=randomUUID(),manifest="a".repeat(64),sha="b".repeat(64),
    text="Ersetze den Titel im vorhandenen Video";
  const media={media_id:mediaId,uri:`r2://${R2}/media/${mediaId}/source.mp4`,
    sha256:sha,size_bytes:4000,mime_type:"video/mp4",version:1,provenance:"verified-original"};
  const expected={request_id:requestId,preview_id:previewId,job_id:jobId,
    revision:1,manifest,action:"change",text};
  const state={schema:"FACTORY-PREVIEW-STATE-V1",job_id:jobId,revision:1,
    manifest,preview_id:null,state:"REVIEW_APPLIED",
    review:{schema:"FACTORY-REVIEW-INTENT-V1",job_id:jobId,request_id:requestId,
      preview_id:previewId,revision:1,manifest,action:"change",text,
      actor:"authenticated_dashboard_owner",status:"APPLIED_TO_FACTORY",
      canonical_store_version:2}};
  const stored={schema:"FACTORY-CANONICAL-R2-JOB-V1",job_id:jobId,store_version:2,
    job:{job_id:jobId,revision:2,status:"changes_requested",
      metadata:{["dashboard_review:"+requestId]:expected,"human_change:r1":text},
      human_approved_revision:null,human_approved_manifest:null,publish_handoff_key:null,
      media:[structuredClone(media)]}};
  const ticket={schema:"FACTORY-EDIT-INTAKE-V1",job_id:jobId,revision:2,
    source_revision:1,request_id:requestId,preview_id:previewId,
    source_approval_manifest:manifest,human_request:text,
    source_media:structuredClone(media),state:"AWAITING_CREATIVE_PLAN",render_approved:false,
    publish_approved:false};
  const stateKey="ai-central/v1/preview-state/"+jobId+".json";
  const jobKey="ai-central/v1/factory-jobs/"+jobId+".json";
  const ticketKey="ai-central/v1/factory-edit-requests/"+jobId+"/r2-"+requestId+".json";
  objects.set(stateKey,state);objects.set(jobKey,stored);objects.set(ticketKey,ticket);
  const url="/api/edit-status?job_id="+jobId+"&request_id="+requestId;
  const fetchIt=(u=url,token=TOKEN)=>worker.fetch(new Request(BASE+u,{
    headers:token?{"authorization":"Bearer "+token}:{}}),env);
  return {objects,state,stored,ticket,stateKey,jobKey,ticketKey,fetchIt,url};
}
test("exact prior human ACK plus matching canonical revision and immutable ticket yields honest awaiting-creative status",async()=>{
  const f=fixture(),resp=await f.fetchIt();
  assert.equal(resp.status,200);
  assert.deepEqual(await resp.json(),{schema:"FACTORY-EDIT-STATUS-V1",
    job_id:f.state.job_id,request_id:f.state.review.request_id,revision:2,
    status:"AWAITING_CREATIVE_PLAN",render_completed:false,
    new_preview_verified:false,publishing_allowed:false,
    truth:"PRIVATE_IMMUTABLE_TICKET_VERIFIED_NO_RENDER_EVIDENCE"});
  // Refreshing later always loads from R2, never browser-local optimistic state.
  assert.equal((await (await f.fetchIt()).json()).status,"AWAITING_CREATIVE_PLAN");
});
test("owner authentication, canonical UUIDs and unavailable request are enforced",async()=>{
  const f=fixture();
  assert.equal((await f.fetchIt(f.url,"")).status,401);
  assert.equal((await f.fetchIt(f.url,"bad-token")).status,401);
  assert.equal((await f.fetchIt("/api/edit-status?job_id=../fake&request_id="+f.state.review.request_id)).status,400);
  assert.equal((await f.fetchIt("/api/edit-status?job_id="+f.state.job_id+"&request_id="+randomUUID())).status,409);
  f.objects.delete(f.stateKey);
  assert.equal((await f.fetchIt()).status,404);
});
test("pending, forged and changed reviews cannot impersonate a created ticket",async()=>{
  for(const corrupt of [
    s=>{s.state="REVIEW_REQUESTED";s.review.status="PENDING_FACTORY_APPLICATION"},
    s=>{s.review.actor="attacker"},
    s=>{s.review.action="discard"},
    s=>{s.review.canonical_store_version=999},
    s=>{s.review.text="tampered"},
  ]){
    const f=fixture();corrupt(f.state);
    f.objects.set(f.stateKey,f.state);
    const resp=await f.fetchIt();
    assert.notEqual(resp.status,200);
  }
});
test("only an exact authoritative canonical revised job can prove creative intake",async()=>{
  for(const corrupt of [
    j=>{j.job.revision=3},j=>{j.job.status="publish_queued"},
    j=>{j.job.publish_handoff_key="fake"},j=>{j.store_version=1},
    j=>{j.job.metadata["human_change:r1"]="injected"},
    j=>{j.job.media[0].sha256="c".repeat(64)},
  ]){
    const f=fixture();corrupt(f.stored);f.objects.set(f.jobKey,f.stored);
    assert.equal((await f.fetchIt()).status,409);
  }
});
test("lost-intake gap returns genuine pending-ticket status, not a fictitious render",async()=>{
  const f=fixture();f.objects.delete(f.ticketKey);
  const resp=await f.fetchIt();assert.equal(resp.status,200);
  const data=await resp.json();
  assert.equal(data.status,"AWAITING_IMMUTABLE_TICKET");
  assert.equal(data.new_preview_verified,false);
  assert.equal(data.publishing_allowed,false);
});
test("altered tickets cannot claim render or posting approval",async()=>{
  for(const corrupt of [
    t=>{t.schema="FORGED"},t=>{t.human_request="different"},
    t=>{t.request_id=randomUUID()},t=>{t.source_media.sha256="d".repeat(64)},
    t=>{t.state="RENDERING"},t=>{t.render_approved=true},
    t=>{t.publish_approved=true},
  ]){
    const f=fixture();corrupt(f.ticket);f.objects.set(f.ticketKey,f.ticket);
    const resp=await f.fetchIt();assert.equal(resp.status,409);
  }
});
test("browser selected-review status is truthful and old studio/preview surfaces remain",()=>{
  const ui=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
  const script=ui.match(/<script>([\s\S]*?)<\/script>/)?.[1];
  assert.ok(script);assert.doesNotThrow(()=>new vm.Script(script));
  assert.match(ui,/textContent="Produktionsauftrag prüfen"/);
  assert.match(ui,/\/api\/edit-status\?job_id=/);
  assert.match(ui,/Kreative Planung ausstehend; noch kein neues Video/);
  assert.match(ui,/Änderung verbindlich bestätigt; neuer Produktionsauftrag ist noch nicht nachgewiesen/);
  assert.match(ui,/id="tabStudio"/);
  assert.match(ui,/id="privatePlayer"/);
  assert.doesNotMatch(script,/\/api\/edit-status[^\n]*method:"POST"/);
});
test("Python sorted canonical JSON is semantically equal regardless of field order",async()=>{
 const f=fixture(),key="dashboard_review:"+f.state.review.request_id;
 f.stored.job.metadata[key]=Object.fromEntries(Object.entries(f.stored.job.metadata[key]).sort());
 assert.equal((await f.fetchIt()).status,200);
 f.stored.job.metadata[key].unexpected=true;assert.equal((await f.fetchIt()).status,409);
});
