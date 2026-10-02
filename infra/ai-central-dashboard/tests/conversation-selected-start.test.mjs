import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";
const html=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
test("dashboard inline JavaScript still compiles",()=>{
 assert.ok(script);assert.doesNotThrow(()=>new vm.Script(script));
});
test("explicitly confirms only selected task before existing guarded dispatch",()=>{
 assert.match(script,/entry\.status==="DRAFT_REQUIRES_REVIEW"/);
 assert.match(script,/start\.textContent="▶ Diesen Auftrag mit der kostenlosen KI prüfen"/);
 assert.match(script,/window\.confirm\("Nur diesen ausgewählten Textauftrag/);
 assert.match(script,/api\("\/api\/dispatch",\{method:"POST"/);
 assert.match(script,/body:JSON\.stringify\(\{id:entry\.id,date\}\)/);
 assert.match(script,/selectedTask=\{\.\.\.entry,status:queued\.status\}/);
});
test("a draft does not auto-launch a model on send or when selecting",()=>{
 const selection=script.slice(script.indexOf("function selectInboxTask(item)"),
   script.indexOf('$("clearSelection").onclick'));
 assert.doesNotMatch(selection,/\/api\/dispatch/);
 const send=script.slice(script.indexOf('$("send").onclick'),script.indexOf("async function upload("));
 assert.doesNotMatch(send,/\/api\/dispatch/);
 assert.match(html,/Ein gespeicherter Entwurf löst keinen Modelllauf aus/);
});
test("inbox reconciliation updates only currently selected visible entry",()=>{
 assert.match(script,/const current=d\.items\.find\(v=>v\.id===selectedTask\?\.id\)/);
 assert.match(script,/if\(current\)\{const oldStatus=selectedTask\?\.status;selectedTask=current;if\(oldStatus!==current\.status\)paintConversation\(\)\}/);
 // An unchanged selected file's video element must not be destroyed every 10s.
 assert.doesNotMatch(script,/if\(current\)\{selectedTask=current;paintConversation\(\)\}/);
});
