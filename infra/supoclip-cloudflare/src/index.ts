import { Container, getContainer } from "@cloudflare/containers";

type Env = {
  SUPOCLIP: DurableObjectNamespace<SupoClipContainer>;
  SUPOCLIP_POC_TOKEN: string;
};

export class SupoClipContainer extends Container {
  defaultPort = 8000;
  sleepAfter = "5m";
  enableInternet = true;
  async fetch(request: Request): Promise<Response> {
    this.renewActivityTimeout();
    return super.fetch(request);
  }
}

function unauthorized() { return new Response("unauthorized", { status: 401 }); }

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const expected = env.SUPOCLIP_POC_TOKEN || "";
    if (!expected || request.headers.get("authorization") !== `Bearer ${expected}`) return unauthorized();
    const url = new URL(request.url);
    if (url.pathname === "/_factory/health") {
      const container = getContainer(env.SUPOCLIP, "buelent-supoclip-poc");
      const started = performance.now();
      try {
        const upstream = await container.fetch(new Request("http://supoclip/health", { headers: { accept: "application/json" } }));
        const body = await upstream.text();
        return Response.json({ok:upstream.ok,service:"supoclip",truth:"LIVE_CANDIDATE",upstreamStatus:upstream.status,upstreamBody:body,upstreamMs:Math.round(performance.now()-started)},{status:upstream.ok?200:503});
      } catch (error) {
        return Response.json({ok:false,service:"supoclip",truth:"LIVE_CANDIDATE",error:String(error),upstreamMs:Math.round(performance.now()-started)},{status:503});
      }
    }
    return getContainer(env.SUPOCLIP, "buelent-supoclip-poc").fetch(request);
  }
};