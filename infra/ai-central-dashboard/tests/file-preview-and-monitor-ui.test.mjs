import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const html=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");

test("private selected-file preview is embedded within its own chat bubble",()=>{
  assert.match(html,/if\(entry.kind==="file"\)appendPrivateAttachment\(userBubble,entry\)/);
  assert.match(html,/\/api\/upload-preview\?id=/);
  assert.match(html,/headers:\{"authorization":"Bearer "\+token\},cache:"no-store"/);
  assert.match(html,/fileSummary\(entry\)/);
  assert.match(html,/KI-Verarbeitung nicht gestartet/);
});
test("image zoom, native media, PDF and metadata fallback are separate",()=>{
  assert.match(html,/id="imageZoom" class="image-dialog"/);
  assert.match(html,/img\.src=cached\.url/);
  assert.match(html,/zoom\.onclick=\(\)=>/);
  assert.match(html,/cached\.mime==="video\/mp4"/);
  assert.match(html,/media\.controls=true/);
  assert.match(html,/cached\.mime==="application\/pdf"/);
  assert.match(html,/frame\.src=cached\.url/);
  assert.match(html,/Keine integrierte Vorschau für diesen Dateityp/);
  assert.match(html,/clearAttachmentCache\(\)/);
});
test("system monitor labels inventory versus monthly billing, never claims live container CPU",()=>{
  assert.match(html,/id="r2Occupied"/);
  assert.match(html,/id="r2Quota"/);
  assert.match(html,/id="r2Meter"/);
  assert.match(html,/id="r2Measured"/);
  assert.match(html,/id="containerState"/);
  assert.match(html,/id="measureSystem"/);
  assert.match(html,/\/api\/system-monitor\?scope=manual/);
  assert.match(html,/Monatlicher GB-Monatsverbrauch nicht messbar/);
  assert.match(html,/kein HTTP-Probe, kein Aufwecken/);
  assert.doesNotMatch(html,/setInterval\([^]*?\/api\/system-monitor/);
});
test("existing private videostudio and selected-task conversation remain intact",()=>{
  assert.match(html,/id="tabStudio"/);
  assert.match(html,/async function refreshStudio\(\)/);
  assert.match(html,/id="privatePlayer"/);
  assert.match(html,/id="studioAutoRefresh"/);
  assert.match(html,/function paintConversation\(\)/);
});