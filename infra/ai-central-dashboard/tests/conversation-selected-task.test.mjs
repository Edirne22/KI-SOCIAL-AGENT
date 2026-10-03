import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";
const html=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
test("inline dashboard JavaScript compiles in the supported browser syntax",()=>{
 assert.ok(script);
 assert.doesNotThrow(()=>new vm.Script(script));
});
test("user sees a selected task with the matching archived replies in the left conversation",()=>{
 assert.match(html,/id="conversationBody" aria-live="polite"/);
 assert.match(html,/selectedTask\?\.id!==item\.id/);
 assert.match(script,/api\("\/api\/task\?id="\+encodeURIComponent\(item\.id\)\)/);
 assert.match(script,/result\.id!==item\.id/);
 assert.match(script,/chatBubble\(role\.role\+" · "\+a\.provider/);
 assert.match(script,/a\.status==="ANSWER"/);
});
test("one selected inbox entry, not a request for every item",()=>{
 assert.match(script,/select\.textContent="↗ Im Gespräch öffnen"/);
 assert.match(script,/select\.onclick=\(\)=>selectInboxTask\(v\)/);
 assert.match(script,/check\.onclick=\(\)=>selectInboxTask\(v\)/);
 assert.match(script,/selectedTask\?\.kind==="message"\)await checkSelectedTask/);
 assert.doesNotMatch(script,/for\(const v of d\.items\)[\s\S]*?api\("\/api\/task\?id="\+encodeURIComponent\(v\.id\)/);
});
test("draft or file upload never fabricates AI completion or dispatch",()=>{
 assert.match(script,/Ein gespeicherter Entwurf löst keinen Modelllauf aus/);
 assert.match(script,/Privat als Datei im R2-Posteingang gespeichert/);
 assert.match(script,/selectedTask=\{id:data\.id,created_at:data\.created_at/);
 assert.match(script,/selectedTask=\{id:d\.id,created_at:d\.created_at/);
 assert.match(script,/if\(item\.kind==="message"\)checkSelectedTask\(\)/);
});
test("selection works on responsive chat tab and stays separate from live operations",()=>{
 assert.match(html,/setTab\("chat"\)/);
 assert.match(html,/@media\(max-width:840px\)/);
 assert.match(html,/id="taskReport"/);
 assert.match(html,/selected-inbox/);
});

test("mobile private ASR form follows only the selected audio and never grants consent",()=>{
 assert.match(script,/item\.kind==="file"&&\["audio\/webm","audio\/mp4","audio\/x-m4a","audio\/m4a","audio\/ogg"\]\.includes\(item\.file\?\.mime\)/);
 assert.match(script,/\$\("asrId"\)\.value=item\.id/);
 assert.match(script,/\$\("asrDate"\)\.value=item\.created_at\.slice\(0,10\)/);
 assert.match(script,/\$\("asrId"\)\.value="";\$\("asrDate"\)\.value=""/);
 const select=script.slice(script.indexOf("function selectInboxTask("),script.indexOf('\n$("clearSelection").onclick'));
 assert.doesNotMatch(select,/\/api\/private-asr|\/api\/asr|asrConsent\.click|fetch\(/);
});
