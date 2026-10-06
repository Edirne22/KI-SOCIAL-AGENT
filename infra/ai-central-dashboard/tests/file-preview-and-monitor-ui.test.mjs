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
test("dead telemetry cards are replaced by the persistent Claude CHAT surface",()=>{
  assert.doesNotMatch(html,/id="r2Occupied"/);
  assert.doesNotMatch(html,/id="containerState"/);
  assert.doesNotMatch(html,/id="measureSystem"/);
  assert.doesNotMatch(html,/id="checkContainer"/);
  assert.match(html,/aria-label="Claude CHAT über OpenCode"/);
  assert.match(html,/id="chatMessage"/);
  assert.match(html,/id="chatSend"/);
  assert.match(html,/id="chatResult"/);
  assert.match(html,/SESSION_KEYS=\{chat:"edirne22\.claude\.chat\.session\.v1",code:"edirne22\.claude\.code\.session\.v1"\}/);
  assert.match(html,/restoreClaudeSessions\(\)/);
});
test("existing private videostudio and selected-task conversation remain intact",()=>{
  assert.match(html,/id="tabStudio"/);
  assert.match(html,/async function refreshStudio\(\)/);
  assert.match(html,/id="privatePlayer"/);
  assert.match(html,/id="studioAutoRefresh"/);
  assert.match(html,/function paintConversation\(\)/);
});
test("10-second chat polling does not interrupt media when selected status is unchanged",()=>{
  assert.match(html,/if\(oldStatus!==current\.status\)paintConversation\(\)/);
  assert.match(html,/class="hero-layout"/);
  assert.match(html,/class="mission-summary"/);
  assert.match(html,/class="monitor-summary"/);
  assert.match(html,/grid-template-columns:minmax\(0,1\.05fr\)/);
});
