import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {due, tick, CRON} from './worker.mjs';
const time = Date.parse('2026-10-27T10:02:00Z');
const event = {cron: CRON, scheduledTime: time};
const env = {SCHEDULER_ENABLED:'true', GITHUB_DISPATCH_TOKEN:'synthetic'};
const response = (status, data) => ({status, ok: status < 300, json:async()=>data});
const empty = () => response(200,{workflow_runs:[]});
test('full day has 288 telegram and 96 starts per publisher, staggered',()=>{
 const counts={};
 for(let i=0;i<1440;i++) for(const w of due(Date.parse('2026-10-27T00:00:00Z')+i*60000)) counts[w]=(counts[w]||0)+1;
 assert.deepEqual(counts,{'telegram-receive.yml':288,'facebook-publish.yml':96,'instagram-publish.yml':96});
 assert.deepEqual(due(time+300000),['telegram-receive.yml','instagram-publish.yml']);
});
test('disabled requires no credential and sends nothing',async()=>{
 assert.deepEqual(await tick(event,{},()=>assert.fail()),[{status:'disabled'}]);
});
test('missing credential fails closed',async()=>{
 await assert.rejects(tick(event,{SCHEDULER_ENABLED:'true'},()=>assert.fail()),/credential_missing/);
});
test('stale, future and wrong cron events send nothing',async()=>{
 for(const e of [{...event,scheduledTime:time-360000},{...event,scheduledTime:time+120000},{...event,cron:'* * * * *'}])
 assert.equal((await tick(e,env,()=>assert.fail(),time))[0].status,'stale_or_invalid_tick');
});
test('only allowlisted main dispatches; no credentials in result',async()=>{
 const calls=[];
 const r=await tick(event,env,async(url,opts)=>{calls.push({url,...opts});return opts.method==='POST'?response(204):empty();},time);
 assert.equal(calls.length,4);
 assert.ok(r.every(x=>x.status==='accepted'));
 for(const c of calls){ assert.equal(c.redirect,'error'); assert.ok(c.url.startsWith('https://api.github.com/repos/Edirne22/KI-SOCIAL-AGENT/actions/workflows/'));if(c.method==='POST')assert.equal(c.body,'{"ref":"main"}'); }
 assert.ok(!JSON.stringify(r).includes('synthetic'));
});
test('active jobs and same-slot completed runs are skipped',async()=>{
 for(const run of [{status:'queued'},{status:'in_progress'},{status:'completed',created_at:new Date(time).toISOString()}]){
 const r=await tick(event,env,async(_,opts)=>{assert.notEqual(opts.method,'POST');return response(200,{workflow_runs:[run]});},time);
 assert.ok(r.every(x=>['active','already_started'].includes(x.status)));
 }
});
test('lookup failures never dispatch',async()=>{
 for(const res of [response(403),response(429),response(200,{bad:true})]){
 const r=await tick(event,env,async(_,opts)=>{assert.notEqual(opts.method,'POST');return res;},time);
 assert.ok(r.every(x=>['lookup_failed','invalid_response'].includes(x.status)));
 }
});
test('ambiguous POST is not retried, other workflow still runs',async()=>{
 let posts=0;
 const r=await tick(event,env,async(_,opts)=>{if(opts.method==='POST'){posts++;if(posts===1)throw Error('private upstream body');return response(204);}return empty();},time);
 assert.equal(posts,2);assert.deepEqual(r.map(x=>x.status),['request_failed','accepted']);
 assert.ok(!JSON.stringify(r).includes('private'));
});
test('GitHub rejection is not reported as accepted',async()=>{
 const r=await tick(event,env,async(_,opts)=>opts.method==='POST'?response(422):empty(),time);
 assert.ok(r.every(x=>x.status==='dispatch_failed'));
});
test('public endpoint cannot start jobs',async()=>{assert.equal((await worker.fetch(new Request('https://example.com/dispatch'))).status,404);});
