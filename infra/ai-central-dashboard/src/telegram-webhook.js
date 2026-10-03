// Staged Telegram webhook intake. Do not register the live bot until cutover tests pass.
// The legacy GitHub poller remains the only active consumer during development.
const MAX_BYTES=32768;
export async function telegramWebhook(request,env){
  if(request.method!=="POST")return new Response("method not allowed",{status:405});
  const secret=env.TELEGRAM_WEBHOOK_SECRET;
  if(typeof secret!=="string"||secret.length<24)return new Response("not configured",{status:503});
  if(request.headers.get("X-Telegram-Bot-Api-Secret-Token")!==secret)return new Response("forbidden",{status:403});
  const size=Number(request.headers.get("content-length"));
  if(Number.isFinite(size)&&size>MAX_BYTES)return new Response("too large",{status:413});
  const body=await request.text();
  if(new TextEncoder().encode(body).length>MAX_BYTES)return new Response("too large",{status:413});
  let update;
  try{update=JSON.parse(body)}catch{return new Response("invalid json",{status:400})}
  if(!Number.isSafeInteger(update?.update_id)||update.update_id<0)return new Response("invalid update",{status:400});
  const message=update.message;
  const chat=message?.chat?.id;
  if(!Number.isSafeInteger(chat)||String(chat)!==String(env.TELEGRAM_CHAT_ID))return new Response("accepted",{status:200});
  if(!env.TELEGRAM_WEBHOOK_INBOX||typeof env.TELEGRAM_WEBHOOK_INBOX.put!=="function")return new Response("inbox unavailable",{status:503});
  // Durable, deterministic inbox key. Consumer must perform its own deduplication.
  const key=`ai-central/v1/telegram-webhook/${update.update_id}.json`;
  await env.TELEGRAM_WEBHOOK_INBOX.put(key,body,{httpMetadata:{contentType:"application/json"}});
  return new Response("accepted",{status:200});
}
