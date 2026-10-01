// Isolated local reproduction of SDK streamable-http server session close;
// deliberately no Cloudflare/no OpenChatCut filesystem.
import { createServer } from "node:http";
import { randomUUID } from "node:crypto";
import { once } from "node:events";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
const sessions=new Map(),events=[];
const srv=createServer(async(req,res)=>{
 try {
   const sid=req.headers["mcp-session-id"];
   let body;
   if(req.method==="POST"){
      const chunks=[];for await(const chunk of req)chunks.push(chunk);
      body=JSON.parse(Buffer.concat(chunks).toString());
   }
   if(sid){
      if(!sessions.has(sid)){res.writeHead(404,{"content-type":"application/json"});res.end(JSON.stringify({error:"session absent"}));return;}
      await sessions.get(sid).handleRequest(req,res,body);
   }else if(req.method==="POST"){
      const t=new StreamableHTTPServerTransport({sessionIdGenerator:randomUUID,
       onsessioninitialized(id){sessions.set(id,t);events.push("initialized");}});
      const server=new McpServer({name:"sdk-session-repro",version:"1"});
      server.registerTool("ping",{description:"read-only ping",inputSchema:{}},async()=>({content:[{type:"text",text:"pong"}]}));
      t.onclose=()=>{sessions.delete(t.sessionId);events.push("transport-onclose");};
      await server.connect(t);await t.handleRequest(req,res,body);
      if(!t.sessionId)await server.close();
   }else{res.writeHead(400);res.end("missing session");}
 }catch(e){events.push("exception:"+e.constructor.name);if(!res.headersSent){res.writeHead(500);res.end("error");}}
});
srv.listen(0,"127.0.0.1");await once(srv,"listening");
const url="http://127.0.0.1:"+srv.address().port;
const content={"accept":"application/json, text/event-stream","content-type":"application/json"};
const init={jsonrpc:"2.0",id:1,method:"initialize",params:{protocolVersion:"2025-06-18",capabilities:{},clientInfo:{name:"raw-client",version:"1"}}};
async function probe(label,headers){
 let r=await fetch(url,{method:"POST",headers:{...content,...headers},body:JSON.stringify(init)});
 const id=r.headers.get("mcp-session-id");await r.text();
 if(!r.ok||!id){console.log(label,"INIT_FAIL",r.status);return false;}
 const notification=await fetch(url,{method:"POST",headers:{...content,...headers,"mcp-session-id":id},body:JSON.stringify({jsonrpc:"2.0",method:"notifications/initialized"})});
 await notification.text();
 const response=await fetch(url,{method:"POST",headers:{...content,...headers,"mcp-session-id":id},body:JSON.stringify({jsonrpc:"2.0",id:2,method:"tools/call",params:{name:"ping",arguments:{}}})});
 const data=await response.text();let ok=response.ok&&data.includes("pong");
 console.log("MCP_LOCAL",JSON.stringify({label,initialize:"ok",notification:notification.status,status:response.status,callOk:ok,sessionPersisted:sessions.has(id),events:[...events]}));
 return ok;
}
try{
 const keep=await probe("keepalive",{});
 const close=await probe("http_connection_close",{"connection":"close"});
 if(!keep||!close)process.exitCode=1;
}catch(e){console.error("MCP_LOCAL_ERROR",String(e));process.exitCode=1;}
finally{await new Promise(resolve=>srv.close(resolve));}
