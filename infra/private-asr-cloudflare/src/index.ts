import { Container, getContainer } from "@cloudflare/containers";
type Env = {
  PRIVATE_ASR: DurableObjectNamespace<PrivateASRContainer>;
  PRIVATE_ASR_INTERNAL_TOKEN: string;
  OPENROUTER_API_KEY: string;
  GROQ_API_KEY: string;
  GEMINI_API_KEY: string;
  NVIDIA_API_KEY?: string;
  SEARXNG_URL?: string;
  R2_ACCOUNT_ID: string; R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string; R2_BUCKET_NAME: string;
  TELEGRAM_BOT_TOKEN: string; TELEGRAM_CHAT_ID: string;
};
export class PrivateASRContainer extends Container {
  defaultPort = 5200;
  requiredPorts = [5200];
  sleepAfter = "15m";
  enableInternet = true;
}
const reply = (data: object, status: number) =>
  Response.json(data, {status, headers: {"cache-control": "no-store"}});
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const auth = request.headers.get("authorization") || "";
    if (!env.PRIVATE_ASR_INTERNAL_TOKEN || auth !== "Bearer " + env.PRIVATE_ASR_INTERNAL_TOKEN)
      return reply({error:"unauthorized"},401);
    const url = new URL(request.url);
    // POST /private-video/jobs is an internal authenticated control-plane call.
    // A valid token already passed above; mark the request so Cloudflare's edge
    // security layer can distinguish it from public form/browser traffic.
    const internalControlHeaders = new Headers(request.headers);
    if (url.pathname === "/private-video/jobs") internalControlHeaders.set("x-edirne22-internal-control", "private-video");
    if (url.pathname !== "/health" && url.pathname !== "/jobs" && url.pathname !== "/private-video/jobs" &&
        url.pathname !== "/opencode/health" && url.pathname !== "/opencode/chat" && url.pathname !== "/opencode/code" && url.pathname !== "/research/search" && url.pathname !== "/admin/container-restart")
      return reply({error:"not_found"},404);
    if (((url.pathname === "/health" || url.pathname === "/opencode/health") && request.method !== "GET") ||
        ((url.pathname === "/jobs" || url.pathname === "/private-video/jobs" || url.pathname === "/opencode/chat" || url.pathname === "/opencode/code" || url.pathname === "/research/search" || url.pathname === "/admin/container-restart") && request.method !== "POST"))
      return reply({error:"method"},405);
    const instance = getContainer(env.PRIVATE_ASR, "edirne22-private-asr-mobile-v3");
    if (url.pathname === "/admin/container-restart") {
      try {
        await instance.destroy();
        return reply({status:"container_restart_requested"},202);
      } catch (error) {
        const name = error instanceof Error ? error.name.slice(0,80) : "unknown";
        return reply({error:"container_restart_failed", exception:name},503);
      }
    }
    let jobBody: string | null = null;
    if (url.pathname === "/jobs" || url.pathname === "/private-video/jobs" || url.pathname === "/opencode/chat" || url.pathname === "/opencode/code" || url.pathname === "/research/search") {
      jobBody = await request.text();
      const size = new TextEncoder().encode(jobBody).byteLength;
      const limit = (url.pathname === "/opencode/chat" || url.pathname === "/opencode/code") ? 8192 : (url.pathname === "/research/search" ? 2048 : 1024);
      if (size < 1 || size > limit) return reply({error:"size"},413);
    }
    // Every route must enter through the same lifecycle gate. In particular, /health
    // must not be allowed to cold-start the container without its runtime secrets.
    await instance.startAndWaitForPorts({
      ports: [5200],
      startOptions: {
        enableInternet: true,
        envVars: {
          PRIVATE_ASR_INTERNAL_TOKEN: env.PRIVATE_ASR_INTERNAL_TOKEN,
          OPENROUTER_API_KEY: env.OPENROUTER_API_KEY,
          GROQ_API_KEY: env.GROQ_API_KEY,
          GEMINI_API_KEY: env.GEMINI_API_KEY,
          ...(env.NVIDIA_API_KEY ? {NVIDIA_API_KEY: env.NVIDIA_API_KEY} : {}),
          ...(env.SEARXNG_URL ? {SEARXNG_URL: env.SEARXNG_URL} : {}),
          R2_ACCOUNT_ID: env.R2_ACCOUNT_ID,
          R2_ACCESS_KEY_ID: env.R2_ACCESS_KEY_ID,
          R2_SECRET_ACCESS_KEY: env.R2_SECRET_ACCESS_KEY,
          R2_BUCKET_NAME: env.R2_BUCKET_NAME,
          TELEGRAM_BOT_TOKEN: env.TELEGRAM_BOT_TOKEN,
          TELEGRAM_CHAT_ID: env.TELEGRAM_CHAT_ID
        }
      }
    });
    if (url.pathname === "/jobs" || url.pathname === "/private-video/jobs" || url.pathname === "/opencode/chat" || url.pathname === "/opencode/code" || url.pathname === "/research/search") {
      // The container is already started/woken above. Never retry POST:
      // duplicate transcription or private-video jobs could overwrite private drafts.
      let ready = false;
      for (let attempt = 0; attempt < 4; attempt++) {
        try {
          const healthPath = (url.pathname === "/opencode/chat" || url.pathname === "/opencode/code" || url.pathname === "/research/search") ? "/opencode/health" : "/health";
          const healthHeaders = new Headers();
          if (healthPath === "/opencode/health") healthHeaders.set("authorization", auth);
          const health = await instance.fetch(new Request("http://localhost:5200" + healthPath, {headers: healthHeaders}));
          if (health.ok && (await health.json() as {ready?: boolean}).ready === true) {
            ready = true; break;
          }
        } catch { /* Container may still be starting. */ }
        if (attempt < 3) await new Promise(resolve => setTimeout(resolve, 1500));
      }
      if (!ready) return reply({error:"container_not_ready"},503);
      const headers = new Headers(internalControlHeaders);
      headers.set("content-length", String(new TextEncoder().encode(jobBody!).byteLength));
      try {
        const upstream = await instance.fetch(new Request("http://localhost:5200" + url.pathname, {
          method:"POST", headers, body:jobBody!
        }));
        // OpenCode is a JSON-only internal API. If the container/runtime emits an
        // HTML/plaintext 500, do not leak that body; convert it to a bounded JSON
        // diagnostic so Actions can identify the failing layer safely.
        if (url.pathname === "/opencode/chat" || url.pathname === "/opencode/code" || url.pathname === "/research/search") {
          const contentType = upstream.headers.get("content-type") || "";
          if (!contentType.toLowerCase().includes("application/json")) {
            return Response.json(
              {error:"opencode_upstream_non_json", upstream_status:upstream.status},
              {status:502, headers:{"cache-control":"no-store","x-edirne22-stage":"worker-opencode-proxy"}}
            );
          }
        }
        return upstream;
      } catch (error) {
        if (url.pathname !== "/opencode/chat" && url.pathname !== "/opencode/code" && url.pathname !== "/research/search") throw error;
        const name = error instanceof Error ? error.name.slice(0,80) : "unknown";
        return Response.json(
          {error:"opencode_container_fetch_failed", exception:name},
          {status:502, headers:{"cache-control":"no-store","x-edirne22-stage":"worker-opencode-fetch"}}
        );
      }
    }
    return instance.fetch(new Request("http://localhost:5200" + url.pathname, request));
  }
};