# OpenChatCut Cloudflare Container PoC

Pinned upstream: `0xsline/OpenChatCut@d1af1ade45521e8ed9a5be09e3acad823f269453`.

Purpose: disposable Cloudflare workbench for the Edirne22 Content Factory. R2 remains the durable media system of record; container disk is temporary work/cache space.

Security:
- one container instance / single-user factory
- EU placement constraint
- public requests fail closed without `Authorization: Bearer ...`
- OpenChatCut's own `OPENCHATCUT_MCP_TOKEN` receives the same secret
- R2 stays private
- no secret values in repository files

Resource profile: `standard-2` (1 vCPU / 6 GiB / 12 GB ephemeral disk), scale-to-zero after five idle minutes.

Acceptance before LIVE label:
1. protected health/MCP reachability
2. upstream status/tool discovery
3. real input import/edit/export
4. ffprobe validation of MP4
5. upload/download through private R2 and SHA-256 equality
6. benchmarks: 720x1280/7s, 1080x1920/15s, 1080x1920/30s with captions/audio
7. negative controls: no token, wrong token, stale/foreign media, corrupt/non-video output
8. only then replace SIMULATED OpenChatCut factory port with LIVE adapter
