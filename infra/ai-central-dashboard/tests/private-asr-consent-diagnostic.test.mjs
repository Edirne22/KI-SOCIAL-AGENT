import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const server=readFileSync(new URL("../src/private-asr.js",import.meta.url),"utf8");
const ui=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
test("consent dispatch exposes bounded HTTP status without upstream body",()=>{
 assert.ok(server.includes("upstream_http_status:code"));
 assert.ok(server.includes('failure_stage:"private_asr_job"'));
 assert.ok(!server.includes("dispatched.text("));
 assert.ok(server.includes("safeReasons.has(diagnostic.reason)"));
 assert.ok(server.includes("if(code===422)"));
 assert.ok(!server.includes("failure_reason:diagnostic.reason"));
 assert.ok(ui.includes("result.failure_reason"));
});
test("consent button displays real dispatch status, GET remains read-only",()=>{
 assert.ok(ui.includes("result.upstream_http_status"));
 assert.ok(ui.includes('asrConsent").onclick=()=>asrCall("POST")'));
 assert.ok(ui.includes('asrCheck").onclick=()=>asrCall("GET")'));
});

test("local transcript polish is opt-in and original is restorable",()=>{
 assert.ok(ui.includes('id="asrPolish"'));
 assert.ok(ui.includes('id="asrOriginal"'));
 assert.ok(ui.includes('const polishTranscript=(raw,language)=>'));
 assert.ok(ui.includes('asrOriginalText=result.text'));
 assert.ok(ui.includes('$("asrText").value=asrOriginalText'));
 assert.ok(ui.includes('asrOriginalText=""'));
 assert.ok(!ui.includes('fetch("https://api.openai.com'));
});
