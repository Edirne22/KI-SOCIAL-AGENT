// Read-only LIVE MCP transport diagnostic. Never log bearer tokens or full session IDs.
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const base = (process.env.OPENCHATCUT_BASE_URL || "").replace(/\/$/, "");
const token = process.env.OPENCHATCUT_MCP_TOKEN || "";
if (!base || !token) throw new Error("missing live target or credential");
const url = base + "/api/external-mcp/mcp";
const count = Math.max(1, Math.min(Number(process.env.DIAG_PAIRS || 6), 20));
const auth = { Authorization: "Bearer " + token, Accept: "application/json, text/event-stream" };
const init = { jsonrpc: "2.0", id: "init", method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "edirne22-session-compare", version: "1" } } };
function safeHeaders(headers) {
  const allowed = ["content-type", "cf-ray", "server", "x-request-id", "retry-after"];
  return Object.fromEntries(allowed.map(k => [k, headers.get(k)]).filter(x => x[1]));
}
async function readResponse(response) {
  const body = await response.text();
  return { status: response.status, headers: safeHeaders(response.headers), body: body.slice(0, 650).replace(/[a-f0-9]{8}-[a-f0-9-]{20,}/ig, "[session-redacted]") };
}
function log(out) { console.log("MCP_DIAG", JSON.stringify(out)); }
async function raw(i) {
  const started = Date.now();
  let sessionId;
  try {
    const r = await fetch(url, { method: "POST", headers: { ...auth, "content-type": "application/json" }, body: JSON.stringify(init), signal: AbortSignal.timeout(25000) });
    sessionId = r.headers.get("mcp-session-id");
    const connect = await readResponse(r);
    if (!r.ok || !sessionId) { log({ path: "raw", i, phase: "initialize", ...connect }); return false; }
    // MCP initialized notification does not need a GET stream.
    const n = await fetch(url, { method: "POST", headers: { ...auth, "mcp-session-id": sessionId, "content-type": "application/json" }, body: JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }), signal: AbortSignal.timeout(25000) });
    if (!n.ok) { log({ path: "raw", i, phase: "notification", ...await readResponse(n) }); return false; }
    await n.arrayBuffer();
    const t = await fetch(url, { method: "POST", headers: { ...auth, "mcp-session-id": sessionId, "content-type": "application/json" }, body: JSON.stringify({ jsonrpc: "2.0", id: "status", method: "tools/call", params: { name: "openchatcut_status", arguments: {} } }), signal: AbortSignal.timeout(25000) });
    const result = await readResponse(t);
    const ok = result.status === 200 && result.body.includes('"result"');
    log({ path: "raw", i, phase: "status", ok, elapsedMs: Date.now() - started, ...(!ok ? result : { status: result.status }) });
    return ok;
  } catch (e) { log({ path: "raw", i, phase: "exception", message: String(e), elapsedMs: Date.now() - started }); return false; }
  finally {
    if (sessionId) {
      try { await fetch(url, { method: "DELETE", headers: { ...auth, "mcp-session-id": sessionId }, signal: AbortSignal.timeout(5000) }); } catch {}
    }
  }
}
async function sdk(i) {
  const started = Date.now();
  const transport = new StreamableHTTPClientTransport(new URL(url), { requestInit: { headers: { Authorization: "Bearer " + token } } });
  const client = new Client({ name: "edirne22-sdk-compare", version: "1" });
  try {
    await client.connect(transport);
    const t = await client.callTool({ name: "openchatcut_status", arguments: {} });
    const ok = !t.isError;
    log({ path: "sdk", i, phase: "status", ok, elapsedMs: Date.now() - started, ...(ok ? {} : { error: JSON.stringify(t.content).slice(0, 650) }) });
    return ok;
  } catch (e) {
    log({ path: "sdk", i, phase: "exception", message: String(e).slice(0, 650), elapsedMs: Date.now() - started });
    return false;
  } finally { try { await client.close(); } catch {} }
}
const tally = { rawPass: 0, rawFail: 0, sdkPass: 0, sdkFail: 0 };
for (let i = 1; i <= count; i++) {
  if (await raw(i)) tally.rawPass++; else tally.rawFail++;
  if (await sdk(i)) tally.sdkPass++; else tally.sdkFail++;
}
log({ event: "SUMMARY", pairs: count, ...tally });
// Diagnostic failures are reported in logs. Do not treat failures as PASS or mark LIVE.
if (tally.rawFail || tally.sdkFail) process.exitCode = 1;
