import { chromium } from "playwright";

const dashboardUrl=process.env.DASHBOARD_URL;
const token=process.env.AI_DASHBOARD_TOKEN;
if(!dashboardUrl||!token)throw new Error("missing dashboard live-test configuration");

const browser=await chromium.launch({headless:true});
const page=await browser.newPage();
page.setDefaultTimeout(120000);

try{
  await page.goto(dashboardUrl,{waitUntil:"domcontentloaded"});
  await page.locator("#token").fill(token);
  await page.locator("#connect").click();
  await page.locator("#conn").waitFor({state:"visible"});
  await page.waitForFunction(()=>document.querySelector("#conn")?.textContent?.includes("R2 verbunden"));
  console.log("DASHBOARD_BROWSER_AUTH_OK");

  await page.locator("#chatStart").click();
  await page.waitForFunction(()=>!document.querySelector("#chatSend")?.disabled);
  console.log("DASHBOARD_CHAT_SESSION_OK");

  await page.locator("#chatMessage").fill("Reply with exactly DASHBOARD_E2E_CLAUDE_OK and nothing else.");
  const claudeResponsePromise=page.waitForResponse(r=>r.url().endsWith("/api/chat/message")&&r.request().method()==="POST");
  await page.locator("#chatSend").click();
  const claudeResponse=await claudeResponsePromise;
  if(!claudeResponse.ok())throw new Error("dashboard Claude API response not OK");
  const claudePayload=await claudeResponse.json();
  if(claudePayload?.text?.trim()!=="DASHBOARD_E2E_CLAUDE_OK")throw new Error("unexpected Claude E2E response");
  await page.waitForFunction(()=>document.querySelector("#chatResult")?.value?.trim()==="DASHBOARD_E2E_CLAUDE_OK");
  const claudeStatus=await page.locator("#chatStatus").textContent();
  if(!claudeStatus?.includes("OpenCode -> OpenRouter -> Anthropic"))throw new Error("dashboard route marker missing");
  console.log("DASHBOARD_CLAUDE_VISIBLE_E2E_OK");

  await page.locator("#chatMessage").fill("Aktuell: Recherchiere das heutige Datum im Web und nenne mindestens eine aktuelle Quellen-URL.");
  const researchResponsePromise=page.waitForResponse(r=>r.url().endsWith("/api/chat/message")&&r.request().method()==="POST");
  await page.locator("#chatSend").click();
  const researchResponse=await researchResponsePromise;
  if(!researchResponse.ok())throw new Error("dashboard research API response not OK");
  const researchPayload=await researchResponse.json();
  if(researchPayload?.research?.used!==true)throw new Error("dashboard research not used");
  if(researchPayload?.research?.provider!=="Groq-BrowserSearch")throw new Error("unexpected dashboard research provider");
  if(!Array.isArray(researchPayload?.research?.sources)||!researchPayload.research.sources.some(x=>/^https?:\/\//.test(String(x?.url||""))))throw new Error("dashboard research source proof missing");
  await page.waitForFunction(()=>document.querySelector("#chatResult")?.value?.trim().length>0);
  const researchStatus=await page.locator("#chatStatus").textContent();
  if(!researchStatus?.includes("Web: USED:Groq-BrowserSearch"))throw new Error("dashboard Groq UI marker missing");
  console.log("DASHBOARD_RESEARCH_VISIBLE_E2E_OK");
}finally{
  await browser.close();
}
