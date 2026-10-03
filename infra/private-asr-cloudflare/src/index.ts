import { Container, getContainer } from "@cloudflare/containers";
type Env = {
  PRIVATE_ASR: DurableObjectNamespace<PrivateASRContainer>;
  PRIVATE_ASR_INTERNAL_TOKEN: string;
  R2_ACCOUNT_ID: string; R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string; R2_BUCKET_NAME: string;
};
export class PrivateASRContainer extends Container {
  defaultPort = 5200;
  sleepAfter = "5m";
  envVars = {
    PRIVATE_ASR_INTERNAL_TOKEN: "",
    R2_ACCOUNT_ID: "",
    R2_ACCESS_KEY_ID: "",
    R2_SECRET_ACCESS_KEY: "",
    R2_BUCKET_NAME: ""
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
    if (url.pathname !== "/health" && url.pathname !== "/jobs")
      return reply({error:"not_found"},404);
    if ((url.pathname === "/health" && request.method !== "GET") ||
        (url.pathname === "/jobs" && request.method !== "POST"))
      return reply({error:"method"},405);
    if (url.pathname === "/jobs") {
      const size = Number(request.headers.get("content-length"));
      if (!Number.isSafeInteger(size) || size < 1 || size > 1024)
        return reply({error:"size"},413);
    }
    const instance = getContainer(env.PRIVATE_ASR, "edirne22-private-asr");
    return instance.fetch(new Request("http://localhost:5200" + url.pathname, request));
  }
};