import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const server=readFileSync(new URL("../src/private-asr.js",import.meta.url),"utf8");
const ui=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
test("consent dispatch exposes bounded HTTP status without upstream body",()=>{
 assert.match(server,/upstream_http_status:code/);
 assert.match(server,/failure_stage:"private_asr_job"/);
 assert.doesNotMatch(server,/dispatched\\.text\\(/);
 assert.doesNotMatch(server,/dispatched\\.json\\(/);
});
test("consent button displays real dispatch status, GET remains read-only",()=>{
 assert.match(ui,/result\\.upstream_http_status/);
 assert.match(ui,/asrConsent"\\)\\.onclick=\\(\\)=>asrCall\\("POST"\\)/);
 assert.match(ui,/asrCheck"\\)\\.onclick=\\(\\)=>asrCall\\("GET"\\)/);
});
