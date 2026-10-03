import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const page=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
test("mobile preview has revision text field bound to existing canonical endpoint",()=>{
  assert.match(page,/feedback\.maxLength=2000/);
  assert.match(page,/feedback\.value\.trim\(\)/);
  assert.match(page,/await requestReview\("change",text\)/);
  assert.match(page,/api\("\/api\/preview-review"/);
  assert.doesNotMatch(page,/window\.prompt\("Welche Änderung/);
});
test("discard remains separate and posting is still explicitly blocked",()=>{
  assert.match(page,/requestReview\("discard",""\)/);
  assert.match(page,/Posten bleibt gesperrt/);
});
