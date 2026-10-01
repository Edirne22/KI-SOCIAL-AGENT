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

const containerBindings = env as unknown as Pick<Env, "OPENCHATCUT_MCP_TOKEN" | "R2_ACCOUNT_ID" | "R2_ACCESS_KEY_ID" | "R2_SECRET_ACCESS_KEY" | "R2_BUCKET_NAME">;

export class OpenChatCutContainer extends Container {
  defaultPort = 5199;
  requiredPorts = [5199];
  sleepAfter = "5m";
  enableInternet = true;
  async fetch(request: Request): Promise<Response> {
    this.renewActivityTimeout();
    const startedAt = Date.now();
    console.log(JSON.stringify({ event: "openchatcut_readiness_wait", port: this.defaultPort, at: new Date().toISOString() }));
    await this.startAndWaitForPorts({
      ports: [this.defaultPort],
      cancellationOptions: { portReadyTimeoutMS: 30_000 }
    });
    console.log(JSON.stringify({ event: "openchatcut_readiness_ready", port: this.defaultPort, durationMs: Date.now() - startedAt, at: new Date().toISOString() }));
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
  // Read-only internal network test: does not wake a stopped container or expose secrets.
  async probeLoopback5199(): Promise<{
    containerRunning: boolean;
    probe: "not-running" | "responding" | "fetch-error" | "exec-error";
    httpStatus?: number;
    errorCode?: string;
  }> {
    const runtime = this.ctx.container;
    if (!runtime?.running) {
      return { containerRunning: false, probe: "not-running" };
    }
    // Intentionally fixed command. User/model input never reaches exec().
    const script = [
      "const url='http://127.0.0.1:5199/api/external-mcp/mcp';",
      "fetch(url,{method:'GET',signal:AbortSignal.timeout(1800)})",
      ".then(r=>console.log(JSON.stringify({probe:'responding',httpStatus:r.status})))",
      ".catch(e=>console.log(JSON.stringify({probe:'fetch-error',errorCode:String(e?.cause?.code||e?.name||'unknown').slice(0,40)})));"
    ].join("");
    try {
      const process = await runtime.exec(["node", "-e", script]);
      const output = await Promise.race([
        process.output(),
        new Promise<never>((_resolve, reject) =>
          setTimeout(() => reject(new Error("probe_timeout")), 6500)
        )
      ]);
      const value = JSON.parse(new TextDecoder().decode(output.stdout).trim()) as {
        probe?: string; httpStatus?: number; errorCode?: string;
      };
      if (output.exitCode !== 0 || (value.probe !== "responding" && value.probe !== "fetch-error")) {
        return { containerRunning: true, probe: "exec-error" };
      }
      if (value.probe === "responding" && Number.isInteger(value.httpStatus)) {
        return { containerRunning: true, probe: "responding", httpStatus: value.httpStatus };
      }
      return {
        containerRunning: true,
        probe: "fetch-error",
        errorCode: String(value.errorCode || "unknown").slice(0, 40)
      };
    } catch {
      // Do not return exception messages: they can include internal infrastructure details.
      return { containerRunning: true, probe: "exec-error" };
    }
  }
  // Distinct, bounded follow-up to the read-only GET probe: test authenticated
  // MCP session persistence INSIDE the existing container process only.
  // Fixed commands/payloads; no external user input, secrets or response bodies leave it.
  async probeAuthenticatedMcp(): Promise<{
    containerRunning: boolean;
    probe: "not-running" | "no-key" | "completed" | "fetch-error" | "exec-error";
    initStatus?: number;
    sessionHeaderPresent?: boolean;
    followupStatus?: number;
    followupSessionLost?: boolean;
    errorCode?: string;
  }> {
    const runtime = this.ctx.container;
    if (!runtime?.running) return { containerRunning: false, probe: "not-running" };
    const script = [
      "const token=process.env.OPENCHATCUT_MCP_TOKEN||'';",
      "if(!token){console.log(JSON.stringify({probe:'no-key'}));process.exit(0)}",
      "const url='http://127.0.0.1:5199/api/external-mcp/mcp';",
      "const h={Authorization:'Bearer '+token,'Content-Type':'application/json',Accept:'application/json, text/event-stream','MCP-Protocol-Version':'2025-06-18'};",
      "const post=(b,extra={})=>fetch(url,{method:'POST',headers:{...h,...extra},body:JSON.stringify(b),signal:AbortSignal.timeout(5000)});",
      "async function run(){try{",
      "const a=await post({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'bounded-local-diagnostic',version:'1'}}});",
      "const sid=a.headers.get('mcp-session-id')||'';let next=0,lost=false;",
      "if(sid&&a.ok){",
      "await post({jsonrpc:'2.0',method:'notifications/initialized',params:{}},{'mcp-session-id':sid}).then(r=>r.body?.cancel().catch(()=>{})).catch(()=>{});",
      "const b=await post({jsonrpc:'2.0',id:2,method:'tools/list',params:{}},{'mcp-session-id':sid});next=b.status;",
      "if(b.status>=400){lost=(await b.text()).slice(0,5000).toLowerCase().includes('session not found');}else{await b.body?.cancel().catch(()=>{});}await a.body?.cancel().catch(()=>{});}",
      "console.log(JSON.stringify({probe:'completed',initStatus:a.status,sessionHeaderPresent:!!sid,followupStatus:next,followupSessionLost:lost}));",
      "}catch(e){console.log(JSON.stringify({probe:'fetch-error',errorCode:String(e?.cause?.code||e?.name||'unknown').slice(0,40)}));}}run();"
    ].join("");
    try {
      const process = await runtime.exec(["node", "-e", script]);
      const output = await Promise.race([
        process.output(),
        new Promise<never>((_resolve, reject) =>
          setTimeout(() => reject(new Error("probe_timeout")), 18000)
        )
      ]);
      const value = JSON.parse(new TextDecoder().decode(output.stdout).trim()) as {
        probe?: string; initStatus?: number; sessionHeaderPresent?: boolean;
        followupStatus?: number; followupSessionLost?: boolean; errorCode?: string;
      };
      if (output.exitCode !== 0) return { containerRunning: true, probe: "exec-error" };
      if (value.probe === "no-key") return { containerRunning: true, probe: "no-key" };
      if (value.probe === "fetch-error") return {
        containerRunning: true, probe: "fetch-error", errorCode: String(value.errorCode || "unknown").slice(0, 40)
      };
      if (value.probe === "completed" && Number.isInteger(value.initStatus)) return {
        containerRunning: true, probe: "completed", initStatus: value.initStatus,
        sessionHeaderPresent: value.sessionHeaderPresent === true,
        followupStatus: Number.isInteger(value.followupStatus) ? value.followupStatus : 0,
        followupSessionLost: value.followupSessionLost === true
      };
      return { containerRunning: true, probe: "exec-error" };
    } catch {
      return { containerRunning: true, probe: "exec-error" };
    }
  }
  envVars = {
    OPENCHATCUT_MCP_TOKEN: containerBindings.OPENCHATCUT_MCP_TOKEN,
    __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS: "edirne22-openchatcut-poc.butupeli.workers.dev",
    R2_ACCOUNT_ID: containerBindings.R2_ACCOUNT_ID || "",
    R2_ACCESS_KEY_ID: containerBindings.R2_ACCESS_KEY_ID || "",
    R2_SECRET_ACCESS_KEY: containerBindings.R2_SECRET_ACCESS_KEY || "",
    R2_BUCKET: containerBindings.R2_BUCKET_NAME || "",
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
    if (url.pathname === "/_factory/container-diag") {
      if (request.method !== "GET") return new Response("method not allowed", { status: 405 });
      const diagnosis = await container.probeLoopback5199();
      return Response.json({ service: "openchatcut", scope: "container-loopback", ...diagnosis });
    }
    if (url.pathname === "/_factory/container-auth-diag") {
      if (request.method !== "GET") return new Response("method not allowed", { status: 405 });
      const diagnosis = await container.probeAuthenticatedMcp();
      return Response.json({ service: "openchatcut", scope: "authenticated-local-mcp", ...diagnosis });
    }
    const sessionId = request.headers.get("mcp-session-id") || "";
    console.log(JSON.stringify({ event: "openchatcut_proxy", method: request.method, path: url.pathname, hasMcpSessionId: Boolean(sessionId), mcpSessionIdPrefix: sessionId.slice(0, 8), workerBootId: workerIdentity().workerBootId }));
    return container.fetch(request);
  }
};
