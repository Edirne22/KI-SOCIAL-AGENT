# SupoClip Cloudflare Container PoC

Independent A/B infrastructure test. OpenChatCut is intentionally untouched.

Pinned upstream: FujiwaraChoki/supoclip@3cbe23d25acdca15a3f46b28a9700a244559ab26

## Truth contract
`/_factory/health` is not a Worker-only health check. It proxies to the real SupoClip backend `/health` endpoint inside the Cloudflare Container. A 200 therefore proves the container-backed FastAPI process answered.

## Scope
Stage 1 tests whether the real pinned SupoClip backend can boot and answer from Cloudflare Containers. SupoClip's complete self-host architecture additionally requires PostgreSQL, Redis and the background worker; those are deliberately not faked in this boot PoC. If upstream startup blocks because those dependencies are mandatory, the run must stay red and the logs become the next BLOCKRUN input.
