// Same upstream Docker image, direct TCP without Cloudflare. Read-only local MCP acceptance.
const endpoint=(process.env.OCC_LOCAL_URL||"http://127.0.0.1:5199")+"/api/external-mcp/mcp";
const token=process.env.OPENCHATCUT_MCP_TOKEN||"occ-local-test-only";
const init={jsonrpc:"2.0",id:"init",method:"initialize",params:{protocolVersion:"2025-06-18",capabilities:{},clientInfo:{name:"occ-direct-docker",version:"1"}}};
const common={"authorization":"Bearer "+token,"accept":"application/json, text/event-stream"};
let forceClose=false;
function safe(response){return {status:response.status,contentType:response.headers.get("content-type")};}
async function post(payload,sid,timeout=14000){
 const headers={...common,"content-type":"application/json"};if(sid)headers["mcp-session-id"]=sid;
 if(forceClose)headers["connection"]="close";
 return fetch(endpoint,{method:"POST",headers,body:JSON.stringify(payload),signal:AbortSignal.timeout(timeout)});
}
async function attempt(i){
 let id;const started=Date.now();forceClose=i%2===0;
 const mode=forceClose?"connection-close":"default";
 try{
   const r=await post(init,null,20000);id=r.headers.get("mcp-session-id");const body=await r.text();
   if(!r.ok||!id||!body.includes("protocolVersion")){console.log("LOCAL_MCP",JSON.stringify({i,mode,phase:"initialize",ok:false,...safe(r),bodySample:body.slice(0,130)}));return false;}
   const n=await post({jsonrpc:"2.0",method:"notifications/initialized"},id);await n.text();
   if(!n.ok){console.log("LOCAL_MCP",JSON.stringify({i,mode,phase:"initialized",ok:false,...safe(n)}));return false;}
   const t=await post({jsonrpc:"2.0",id:"status",method:"tools/call",params:{name:"openchatcut_status",arguments:{}}},id);
   const result=await t.text();const ok=t.ok&&result.includes('"result"');
   console.log("LOCAL_MCP",JSON.stringify({i,mode,phase:"status",ok,code:t.status,elapsedMs:Date.now()-started,...(!ok?{bodySample:result.slice(0,130)}:{})}));
   return ok;
 }catch(e){console.log("LOCAL_MCP",JSON.stringify({i,mode,phase:"exception",ok:false,error:e?.name||"Error",message:String(e).slice(0,240),cause:e?.cause?{code:String(e.cause.code||""),message:String(e.cause.message||"").slice(0,240)}:null,elapsedMs:Date.now()-started}));return false;}
 finally{if(id){try{await fetch(endpoint,{method:"DELETE",headers:{...common,"mcp-session-id":id},signal:AbortSignal.timeout(3000)});}catch{}}}
}
let successes=0;for(let i=1;i<=12;i++{if(await attempt(i))successes++;if(i<12)await new Promise(r=>setTimeout(r,1000));}
console.log("LOCAL_MCP_SUMMARY",JSON.stringify({attempts:12,successes,failures:12-successes}));
if(successes!==12)process.exitCode=1;
