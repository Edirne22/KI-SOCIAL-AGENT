import { Container, getContainer } from "@cloudflare/containers";
import { env as workerEnv } from "cloudflare:workers";
const runtimeEnv = workerEnv as unknown as Record<string, string>;
type Env = {
  PRIVATE_ASR: DurableObjectNamespace<PrivateASRContainer>;
  PRIVATE_ASR_INTERNAL_TOKEN: string;
  R2_ACCOUNT_ID: string; R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string; R2_BUCKET_NAME: string;
  TELEGRAM_BOT_TOKEN: string; TELEGRAM_CHAT_ID: string;
};
export class PrivateASRContainer extends Container {
  defaultPort = 5200;
  sleepAfter = "15m";
  envVars = {
    PRIVATE_ASR_INTERNAL_TOKEN: runtimeEnv.PRIVATE_ASR_INTERNAL_TOKEN,
    R2_ACCOUNT_ID: runtimeEnv.R2_ACCOUNT_ID,
    R2_ACCESS_KEY_ID: runtimeEnv.R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY: runtimeEnv.R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME: runtimeEnv.R2_BUCKET_NAME,
    TELEGRAM_BOT_TOKEN: runtimeEnv.TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID: runtimeEnv.TELEGRAM_CHAT_ID
  };
}
const reply = (data: object, status: number) =>
  Response.json(data, {status, headers: {"cache-control": "no-store"}});
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const auth = request.headers.get("authorization") || "";
    if (!env.PRIVATE_ASR_INTERNAL_TOKEN || auth !== "Bearer " + env.PRIVATE_ASR_INTERNAL_TOKEN)
      return reply({error:"unauthorized"},401);
    const url = new URL(request.url);
    if (url.pathname !== "/health" && url.pathname !== "/jobs" && url.pathname !== "/private-video/jobs")
      return reply({error:"not_found"},404);
    if ((url.pathname === "/health" && request.method !== "GET") ||
        ((url.pathname === "/jobs" || url.pathname === "/private-video/jobs") && request.method !== "POST"))
      return reply({error:"method"},405);
    let jobBody: string | null = null;
    if (url.pathname === "/jobs" || url.pathname === "/private-video/jobs") {
      jobBody = await request.text();
      const size = new TextEncoder().encode(jobBody).byteLength;
      if (size < 1 || size > 1024) return reply({error:"size"},413);
    }
    const instance = getContainer(env.PRIVATE_ASR, "edirne22-private-asr");
    if (url.pathname === "/jobs" || url.pathname === "/private-video/jobs") {
      // Warm the same named container before sending a non-idempotent job.
      // Never retry POST: duplicate transcription could overwrite private drafts.
      let ready = false;
      for (let attempt = 0; attempt < 4; attempt++) {
        try {
          const health = await instance.fetch(new Request("http://localhost:5200/health"));
          if (health.ok && (await health.json() as {ready?: boolean}).ready === true) {
            ready = true; break;
          }
        } catch { /* Container may still be starting. */ }
        if (attempt < 3) await new Promise(resolve => setTimeout(resolve, 1500));
      }
      if (!ready) return reply({error:"container_not_ready"},503);
      const headers = new Headers(request.headers);
      headers.set("content-length", String(new TextEncoder().encode(jobBody!).byteLength));
      return instance.fetch(new Request("http://localhost:5200" + url.pathname, {
        method:"POST", headers, body:jobBody!
      }));
    }
    return instance.fetch(new Request("http://localhost:5200" + url.pathname, request));
  }
};