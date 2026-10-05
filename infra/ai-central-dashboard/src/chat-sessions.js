const CHAT_PREFIX="ai-central/v1/chat/sessions/";
const ID=/^[0-9a-f-]{36}$/;
const MODES=new Set(["chat","code"]);
const CHAT_CAPABILITIES=Object.freeze(["read","chat","analyse"]);

export function capabilitiesForMode(mode){
  if(mode==="chat")return [...CHAT_CAPABILITIES];
  if(mode==="code")return ["read","chat","analyse","code"]; // execution still requires the existing guarded code path.
  throw new Error("SESSION_MODE_INVALID");
}
function key(id){return CHAT_PREFIX+id+"/session.json"}
export async function createSession(env,mode="chat"){
  if(!MODES.has(mode))throw new Error("SESSION_MODE_INVALID");
  const id=crypto.randomUUID(),now=new Date().toISOString();
  const value={schema:"AI-CENTRAL-SESSION-V1",id,mode,capabilities:capabilitiesForMode(mode),
    created_at:now,updated_at:now,messages:[]};
  await env.AI_CENTRAL_R2.put(key(id),JSON.stringify(value),{httpMetadata:{contentType:"application/json"}});
  return value;
}
export async function loadSession(env,id,requiredMode){
  if(!ID.test(id))throw new Error("SESSION_ID_INVALID");
  const obj=await env.AI_CENTRAL_R2.get(key(id));if(!obj)throw new Error("SESSION_NOT_FOUND");
  const s=await obj.json();
  if(s?.schema!=="AI-CENTRAL-SESSION-V1"||s.id!==id||!MODES.has(s.mode)||
     JSON.stringify(s.capabilities)!==JSON.stringify(capabilitiesForMode(s.mode))||!Array.isArray(s.messages))
    throw new Error("SESSION_RECORD_INVALID");
  if(requiredMode&&s.mode!==requiredMode)throw new Error("SESSION_MODE_MISMATCH");
  return s;
}
export async function appendChatMessage(env,id,role,text){
  const s=await loadSession(env,id,"chat");
  if(!["user","assistant"].includes(role)||typeof text!=="string"||text.length<1||text.length>12000)
    throw new Error("SESSION_MESSAGE_INVALID");
  s.messages.push({role,text,at:new Date().toISOString()});
  if(s.messages.length>80)s.messages=s.messages.slice(-80);
  s.updated_at=new Date().toISOString();
  await env.AI_CENTRAL_R2.put(key(id),JSON.stringify(s),{httpMetadata:{contentType:"application/json"}});
  return s;
}
