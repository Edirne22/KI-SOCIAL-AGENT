# Block6: NEW Evidence – authenticated in-container MCP vs outer Worker
**Verified previous live diagnostic:** GitHub run #36910059322 SUCCESS for the narrow Worker-only probe, not for full Block6 video. Protected Worker health HTTP200; one outer MCP initialize HTTP500; protected internal loopback HTTP200 reported `{"containerRunning":true,"probe":"responding","httpStatus":401}`. HTTP401 from the internal unauthenticated GET proves a reachable application listener but is NOT proof authenticated MCP operation, edit stability or session persistence. Full OpenChatCut live acceptance still not complete.

**This step deliberately obtains NEW evidence:** existing stacked PR #278 gets a fixed, bounded authenticated MCP initialize and immediate follow-up `tools/list` executed within the running container itself. New protected GET-only `/_factory/container-auth-diag` never accepts user commands, arbitrary URLs, tokens or request bodies. It returns ONLY booleans and HTTP status codes, never the token/session ID/model response or raw logs. The script takes its token only from `process.env.OPENCHATCUT_MCP_TOKEN` inside that same container; source file contains no secret. It keeps initialization stream alive until after the follow-up to avoid accidentally causing a session loss by closing the stream prematurely. Errors are bounded and redacted.

The new separate **one-time** workflow on merge pins the exact audited PR #278 SHA, checks TypeScript and fixed privileged route, deploys only the updated Worker with `--containers-rollout=none`, probes protected health / one outer initialize / internal unauthenticated reachability and now compares the authenticated local MCP initialization. It does NOT install/roll out a new OpenChatCut Docker image, invoke arbitrary commands, create published content or enable expensive models.

Interpretation:
- Local authenticated initialize 200 and local session follow-up good vs outer HTTP500: isolate Worker-to-container transport/proxy behavior before modifying the application.
- Local authenticated initialize 401: compare internal auth token propagation, not Cloudflare wake.
- Local authenticated initialize >=500: investigate the application MCP implementation.
- Local initialize 200 then follow-up non-200 or session-expired: investigate upstream in-process session persistence and keepalive.
- `not-running` / `exec-error`: inability to determine application state; no false PASS.
- A passing diagnostic is **only a diagnostic**. Block6 requires actual import/edit/render/ffprobe/verified private R2 roundtrip before marking LIVE. Consider existing FFmpeg + Remotion fallback if session persistence remains an upstream limitation.

This extends docs/BLOCK6_SINGLE_WORKER_LOOPBACK_DIAG_V1.md, never overwrites Guardrails or V6 handover.
