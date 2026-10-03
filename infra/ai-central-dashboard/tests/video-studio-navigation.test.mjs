import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
const html=readFileSync(new URL("../public/index.html",import.meta.url),"utf8");
test("studio is explicit responsive area, no duplicate unsafe preview controls",()=>{
 assert.match(html,/id="tabStudio"[^>]*>▶ Videostudio/);
 assert.match(html,/<section class="panel studio" aria-label="Privates Videostudio">/);
 assert.equal((html.match(/id="privatePlayer"/g)||[]).length,1);
 assert.equal((html.match(/id="loadReviews"/g)||[]).length,1);
 assert.equal((html.match(/id="loadPreviews"/g)||[]).length,1);
 assert.match(html,/wrap\[data-tab="studio"\]/);
});
test("studio bounds supported edits and does not promise Telegram or auto-posts",()=>{
 assert.match(html,/Automatisch ausführbar/);
 assert.match(html,/Andere kreative Änderungen bleiben zur Planung offen/);
 assert.match(html,/Telegram-Fertigmeldung ist noch nicht angebunden/);
 assert.match(html,/Ein abgeschlossener Änderungsauftrag ist noch kein neues Video/);
 assert.match(html,/Keine neue geprüfte Vorschau seit der letzten Prüfung/);
});
test("refresh only reads actual authenticated server previews and durable reviews",()=>{
 assert.match(html,/async function refreshStudio\(\)/);
 assert.match(html,/await loadPreviews\(\);await loadReviewStatuses\(\)/);
 assert.match(html,/await api\("\/api\/previews"\)/);
 assert.match(html,/await api\("\/api\/reviews"\)/);
 assert.match(html,/const current=new Set\(list.items.map\(item=>item.id\)\)/);
 assert.match(html,/if\(studioBaseline!==null\)/);
 assert.match(html,/studioBaseline=current/);
 assert.match(html,/if\(token&&\$\("workspace"\).dataset.tab==="studio"&&\$\("studioAutoRefresh"\).checked\)/);
});
test("UI preserves manual only explicit per-video review and posting gate",()=>{
 assert.match(html,/Änderung anfordern/);
 assert.match(html,/Verwerfen anfordern/);
 assert.match(html,/window.confirm\("Änderungswunsch verbindlich vormerken/);
 assert.match(html,/Posten bleibt gesperrt/);
});
