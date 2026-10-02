import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const html=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");

test("dictation is distinct from private audio upload",()=>{
  assert.match(html,/id="dictate"[^>]*>🎙 Diktieren ins Auftragsfeld/);
  assert.match(html,/id="mic"[^>]*>◉ Audiodatei aufnehmen/);
  assert.match(html,/id="dictateStop"/);
  assert.match(html,/id="stop"[^>]*>Audioaufnahme stoppen/);
  assert.match(html,/dictation\.onresult=event=>/);
  assert.match(html,/\$\("message"\)\.value=original\+separator\+dictatedFinal\.trim\(\)/);
});
test("explicit privacy consent before enabling browser vendor STT",()=>{
  const confirm=html.indexOf('window.confirm("Browser-Diktat einschalten?');
  const start=html.indexOf("dictation.start()");
  assert.ok(confirm>=0&&start>confirm);
  assert.match(html,/Browser kann die Sprache an den Browseranbieter/);
  assert.match(html,/\["de-DE","tr-TR"\]/);
});
test("no automatic submission or false whisper implementation",()=>{
  const begin=html.indexOf('let dictation=null');
  const end=html.indexOf('$("mic").onclick',begin);
  const section=html.slice(begin,end);
  assert.ok(begin>0&&end>begin);
  assert.doesNotMatch(section,/\/api\/inbox|\/api\/upload|faster_whisper|faster-whisper.*?\.transcribe\(/);
  assert.match(html,/noch ohne faster-whisper-Transkription/);
  assert.match(html,/kein Textauftrag/);
});
test("unsupported browser gives an honest fallback",()=>{
  assert.match(html,/window\.SpeechRecognition\|\|window\.webkitSpeechRecognition/);
  assert.match(html,/Dieser Browser unterstützt keine direkte Diktierfunktion/);
  assert.match(html,/Erkannter Text steht im Auftragsfeld/);
});
