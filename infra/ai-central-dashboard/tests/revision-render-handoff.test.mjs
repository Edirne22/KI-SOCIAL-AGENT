import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import worker from '../src/index.js';
const file=process.env.BLOCK8_SYNTHETIC_EVIDENCE;
test('actual Python revision output reaches the matching dashboard preview and rejects tampering',{skip:!file},async()=>{
 const evidence=JSON.parse(readFileSync(file,'utf8')),objects=evidence.objects;
 const env={AI_DASHBOARD_TOKEN:'synthetic-dashboard-token-at-least-24-chars',AI_CENTRAL_R2:{get:async key=>objects[key]?{json:async()=>structuredClone(objects[key])}:null}};
 const query='/api/edit-status?job_id='+evidence.job_id+'&request_id='+evidence.request_id;
 const fetch=()=>worker.fetch(new Request('https://dashboard.example'+query,{headers:{authorization:'Bearer '+env.AI_DASHBOARD_TOKEN}}),env);
 let response=await fetch();assert.equal(response.status,200);const data=await response.json();
 assert.equal(data.status,'READY_FOR_HUMAN');assert.equal(data.new_preview_verified,true);assert.equal(data.publishing_allowed,false);
 const key='ai-central/v1/factory-jobs/'+evidence.job_id+'.json',original=structuredClone(objects[key]);
 for(const corrupt of [j=>j.job.media[0].sha256='f'.repeat(64),j=>j.job.human_approved_revision=2,j=>j.job.metadata.revision_render.request_id='forged',j=>j.job.revision=3]){
  objects[key]=structuredClone(original);corrupt(objects[key]);assert.equal((await fetch()).status,409);
 }
});
