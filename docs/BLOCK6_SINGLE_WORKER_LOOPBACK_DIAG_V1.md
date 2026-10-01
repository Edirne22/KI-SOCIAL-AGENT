# Block 6 – isolated one-time Worker-only OpenChatCut loopback investigation

## Verbindliche Regeln
PROJECT_GUARDRAILS.md is authoritative. This change is an intentionally narrow diagnostic, not approval of OpenChatCut media-production completion. No model text, arbitrary user input or remote caller controls the container exec script. Never claim HTTP health alone proves app/session readiness.

## Actual historic root-cause evidence and scope
Previously observed run #36847153610 after PR #271 deploy: protected Worker health succeeded, raw MCP initialize HTTP 200, SDK connected then `openchatcut_status` returned MCP `session not found or expired`. Other runs sometimes timed out with HTTP 000. This distinguishes outer Worker health from per-session backend readiness but does **not** yet prove why sessions disappear.
Open PR #271 adds explicit startAndWaitForPorts and lifecycle logs; stacked #278 adds protected `/_factory/container-diag` using fixed 127.0.0.1:5199 fetch within existing running container, no user-derived commands or secrets in diagnostic responses. Both have prior offline contract evidence; #271 live media acceptance failed. Do not merge these two old branches blindly.

## One-shot diagnostic implementation
This workflow runs offline checks on immutable same-repository PR #278 code ref `73756825c8cd167e5997e24514e2c11e1170120b`. After reviewed merge of **this new workflow only**, it triggers exactly once on its own file path:
- validates auth gating, fixed internal loopback target, TypeScript and `wrangler --dry-run --containers-rollout=none`.
- uses existing GitHub Secrets to deploy only the diagnostic Worker to the **existing** Cloudflare target with `--containers-rollout=none`. This changes active Worker routing, so regard it as a real deployment and verify it.
- checks protected health; performs just **one bounded** MCP initialize call to wake container if sleeping (no duplicate loops); immediately calls the protected internal loopback endpoint and prints only `containerRunning/probe/httpStatus/errorCode`. Does not print private MCP session data, arbitrary logs or credentials. Compares availability of before/after container inventory but **does not** claim image was unchanged merely by list count. Worker-only `--containers-rollout=none` is the actual mechanism for suppressing image rollout.
- requires `probe:responding` to pass real internal connectivity. A mere HTTP200 on `/_factory/container-diag` with `not-running` or `fetch-error` is NOT acceptance.

## Following the new evidence
- `probe:responding`: local app listener reached; investigate MCP session persistence and proxy/session routing using concrete request logs. Then run a real complete edit/render/R2/ffprobe live acceptance before marking Block6 complete.
- `probe:fetch-error`: local listener absent/unresponsive despite claimed container running, diagnose application process, boot/port/in-container network and bounded warmup.
- `probe:not-running`: container wake/start is still failing; inspect Worker/container lifecycle, no repeated identical transport tests.
- `probe:exec-error`: bounded Cloudflare exec diagnostic itself failed; review runtime support or error data without declaring application failure.
- If even after these controlled tests OpenChatCut remains blocked, reuse existing tested FFmpeg adapter and Remotion rather than making the whole Content Factory depend indefinitely on OpenChatCut.

No new paid model, VPS or publisher action. Keep #271/#278 available for forensic comparison; only merge/stabilize after actual evidence and clean PR scope.
