import { chromium } from "playwright";

// REQUIRE_DASHBOARD_RESEARCH=false proves the core Dashboard->Claude path; Groq source proof stays in the dedicated Block-9 gate.
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

  if(process.env.REQUIRE_CURRENT_DATE_TRUTH==="true"){
    const expectedUtcDate=new Date().toISOString().slice(0,10);
    await page.locator("#chatMessage").fill("Welches Datum ist heute? Suche im Web und nenne eine Quelle.");
    const dateResponsePromise=page.waitForResponse(r=>r.url().endsWith("/api/chat/message")&&r.request().method()==="POST");
    await page.locator("#chatSend").click();
    const dateResponse=await dateResponsePromise;
    if(!dateResponse.ok())throw new Error("dashboard current-date API response not OK");
    const datePayload=await dateResponse.json();
    const dateText=String(datePayload?.text||"");
    if(!dateText.includes(expectedUtcDate))throw new Error("trusted current UTC date missing from dashboard answer");
    if(/8\.\s*Mai\s*2026/i.test(dateText))throw new Error("stale May 8 2026 regression escaped");
    if(datePayload?.research?.used!==true)throw new Error("dashboard current-date research not used");
    if(datePayload?.research?.provider!=="Groq-BrowserSearch")throw new Error("dashboard current-date provider mismatch");
    const dateSources=Array.isArray(datePayload?.research?.sources)?datePayload.research.sources:[];
    if(!dateSources.some(x=>/^https?:\/\//.test(String(x?.url||""))))throw new Error("dashboard current-date source proof missing");
    await page.waitForFunction(expected=>document.querySelector("#chatResult")?.value?.includes(expected),expectedUtcDate);
    const dateStatus=await page.locator("#chatStatus").textContent();
    if(!dateStatus?.includes("Web: USED:Groq-BrowserSearch"))throw new Error("dashboard current-date Groq UI marker missing");
    console.log("DASHBOARD_CURRENT_DATE_TRUTH_E2E_OK "+expectedUtcDate);
  }

  if(process.env.REQUIRE_DASHBOARD_RESEARCH==="false"){
    console.log("DASHBOARD_RESEARCH_POST_DEPLOY_REQUIRED");
  }else{
    await page.locator("#chatMessage").fill("What is the current date? Return current public web sources.");
  const researchResponsePromise=page.waitForResponse(r=>r.url().endsWith("/api/chat/message")&&r.request().method()==="POST");
  await page.locator("#chatSend").click();
  const researchResponse=await researchResponsePromise;
  if(!researchResponse.ok())throw new Error("dashboard research API response not OK");
  const researchPayload=await researchResponse.json();
  const researchUsed=researchPayload?.research?.used===true;
  const researchProvider=String(researchPayload?.research?.provider||"none");
  const researchSources=Array.isArray(researchPayload?.research?.sources)?researchPayload.research.sources:[];
  const routeResearch=String(researchPayload?.route?.tools?.web_research||"unknown");
  if(!researchUsed){
    console.error("DASHBOARD_RESEARCH_DIAG used=false provider="+researchProvider+" sources="+researchSources.length+" route="+routeResearch);
    throw new Error("dashboard research not used");
  }
  if(researchProvider!=="Groq-BrowserSearch")throw new Error("unexpected dashboard research provider");
  if(!researchSources.some(x=>/^https?:\/\//.test(String(x?.url||""))))throw new Error("dashboard research source proof missing");
  await page.waitForFunction(()=>document.querySelector("#chatResult")?.value?.trim().length>0);
  const researchStatus=await page.locator("#chatStatus").textContent();
  if(!researchStatus?.includes("Web: USED:Groq-BrowserSearch"))throw new Error("dashboard Groq UI marker missing");
    console.log("DASHBOARD_RESEARCH_VISIBLE_E2E_OK");
  }
}finally{
  await browser.close();
}
