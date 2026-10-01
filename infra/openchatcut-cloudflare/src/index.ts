import { Container, getContainer } from "@cloudflare/containers";
import { env } from "cloudflare:workers";

let workerBootId: string | undefined;
let workerStartedAt: string | undefined;
function workerIdentity() {
  if (!workerBootId) {
    workerBootId = crypto.randomUUID();
    workerStartedAt = new Date().toISOString();
  }
  return { workerBootId, workerStartedAt };
}

type Env = {
  OPENCHATCUT: DurableObjectNamespace<OpenChatCutContainer>;
  OPENCHATCUT_MCP_TOKEN: string;
  R2_ACCOUNT_ID?: string;
  R2_ACCESS_KEY_ID?: string;
  R2_SECRET_ACCESS_KEY?: string;
  R2_BUCKET_NAME?: string;
};

export class OpenChatCutContainer extends Container {
  defaultPort = 5199;
  sleepAfter = "5m";
  enableInternet = true;
  async fetch(request: Request): Promise<Response> {
    this.renewActivityTimeout();
    const startedAt = Date.now();
    console.log(JSON.stringify({ event: "openchatcut_container_readiness_start", port: this.defaultPort }));
    await this.startAndWaitForPorts({ ports: [this.defaultPort] });
    console.log(JSON.stringify({ event: "openchatcut_container_readiness_ready", port: this.defaultPort, durationMs: Date.now() - startedAt }));
    return super.fetch(request);
  }
  override onStart(): void {
    console.log(JSON.stringify({ event: "openchatcut_container_start", at: new Date().toISOString() }));
  }
  override onStop(stopParams: { exitCode: number; reason: string }): void {
    console.log(JSON.stringify({ event: "openchatcut_container_stop", at: new Date().toISOString(), ...stopParams }));
  }
  override onError(error: unknown): void {
    console.error(JSON.stringify({ event: "openchatcut_container_error", at: new Date().toISOString(), error: String(error) }));
  }
  envVars = {
    OPENCHATCUT_MCP_TOKEN: env.OPENCHATCUT_MCP_TOKEN,
    __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS: "edirne22-openchatcut-poc.butupeli.workers.dev",
    R2_ACCOUNT_ID: env.R2_ACCOUNT_ID || "",
    R2_ACCESS_KEY_ID: env.R2_ACCESS_KEY_ID || "",
    R2_SECRET_ACCESS_KEY: env.R2_SECRET_ACCESS_KEY || "",
    R2_BUCKET: env.R2_BUCKET_NAME || "",
    OPENCHATCUT_DISABLE_HARDWARE_ENCODING: "1",
    OPENCHATCUT_RENDER_CONCURRENCY: "50%",
    OPENCHATCUT_MAX_ACTIVE_EXPORTS: "1"
  };
}

function unauthorized() {
  return new Response("unauthorized", { status: 401 });
}

export default {
  async fetch(request: Request, e: Env): Promise<Response> {
    const expected = e.OPENCHATCUT_MCP_TOKEN || "";
    const auth = request.headers.get("authorization") || "";
    if (!expected || auth !== `Bearer ${expected}`) return unauthorized();

    const url = new URL(request.url);
    if (url.pathname === "/_factory/health") {
      const identity = workerIdentity();
      return Response.json({ ok: true, service: "openchatcut", truth: "LIVE_CANDIDATE", ...identity });
    }

    const container = getContainer(e.OPENCHATCUT, "buelent-single-user");
    const sessionId = request.headers.get("mcp-session-id") || "";
    console.log(JSON.stringify({ event: "openchatcut_proxy", method: request.method, path: url.pathname, hasMcpSessionId: Boolean(sessionId), mcpSessionIdPrefix: sessionId.slice(0, 8), workerBootId: workerIdentity().workerBootId }));
    return container.fetch(request);
  }
};
