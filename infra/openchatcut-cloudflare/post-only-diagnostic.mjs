// Isolated, read-only POST-only MCP continuity probe against existing deployment.
// Never creates projects, renders, uploads, or uses personal data.
const base=(process.env.OPENCHATCUT_BASE_URL||'').replace(/\/$/,'');
const token=process.env.OPENCHATCUT_MCP_TOKEN;
if(!base||!token) throw Error('Missing endpoint or secret');
const endpoint=base+'/api/external-mcp/mcp';
const headers={Authorization:'Bearer '+token,'Content-Type':'application/json',Accept:'application/json, text/event-stream'};
async function post(body,session){const start=Date.now();const response=await fetch(endpoint,{method:'POST',headers:{...headers,...(session?{'Mcp-Session-Id':session}:{})},body:JSON.stringify(body),signal:AbortSignal.timeout(20000)});const text=await response.text();const result={status:response.status,elapsedMs:Date.now()-start,sessionId:response.headers.get('mcp-session-id'),body:text.slice(0,600)};return result;}
const init=await post({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'edirne22-post-only-diag',version:'1.0'}}});
console.log('POST_ONLY_INIT',JSON.stringify(init));if(init.status!==200||!init.sessionId)process.exit(1);
const id=init.sessionId;
const notification=await post({jsonrpc:'2.0',method:'notifications/initialized'},id);console.log('POST_ONLY_READY',JSON.stringify({...notification,sessionId:'[redacted]'}));
let pass=0;for(let i=0;i<12;i++){try{const result=await post({jsonrpc:'2.0',id:i+2,method:'tools/call',params:{name:'openchatcut_status',arguments:{}}},id);console.log('POST_ONLY_ROUND',JSON.stringify({round:i+1,status:result.status,elapsedMs:result.elapsedMs,body:result.status===200?'ok':result.body}));if(result.status!==200)process.exitCode=1;else pass++;if(result.status!==200)break;}catch(error){console.error('POST_ONLY_NETWORK_ERROR',JSON.stringify({round:i+1,error:String(error)}));process.exitCode=1;break;}await new Promise(r=>setTimeout(r,250));}console.log('POST_ONLY_SUMMARY',JSON.stringify({pass,expected:12}));if(pass!==12)process.exitCode=1;
