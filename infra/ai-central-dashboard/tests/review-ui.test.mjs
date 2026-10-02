import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const html=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
test("human review controls are present and require explicit user confirmation",()=>{
 assert.match(html,/Änderung anfordern/);
 assert.match(html,/Verwerfen anfordern/);
 assert.match(html,/window.confirm\("Änderungswunsch verbindlich vormerken/);
 assert.match(html,/window.confirm\("Dieses Video wirklich zur Verwerfung/);
});
test("browser requests carry current server manifest revision and fresh request ID",()=>{
 assert.match(html,/preview_id:item.id,request_id:crypto.randomUUID\(\)/);
 assert.match(html,/manifest:item.manifest,revision:item.revision,text/);
 assert.match(html,/api\("\/api\/preview-review"/);
});
test("review request is not represented as completed Factory work",()=>{
 assert.match(html,/result.status!=="PENDING_FACTORY_APPLICATION"/);
 assert.match(html,/Fabrik muss ihn noch anwenden/);
 assert.match(html,/Posten bleibt gesperrt/);
 assert.doesNotMatch(html,/api\("\/api\/preview-review"[\s\S]*?action:"post"/);
});
