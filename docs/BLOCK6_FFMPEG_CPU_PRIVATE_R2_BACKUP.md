# Block 6 independent CPU FFmpeg fallback, not OpenChatCut acceptance

## Evidence and scope
The Cloudflare OpenChatCut container is intermittently responsive: run #36910059322 showed the application listener at internal port 5199 (unauthenticated HTTP401) while the public MCP initialize returned HTTP500; #36911098650 showed internal ECONNREFUSED despite the container's running flag; #36911811987 showed outer MCP initialize HTTP200 and internal listener HTTP401 but local exec probe missed the token because Cloudflare exec children do not inherit envVars. Separate diagnostic fixes continue through #296. None of those conditions proves full edit/render stability.

This separate fallback proves actual existing **CPU** FFmpeg media handling and the existing `R2Storage` factory storage contract without waiting on upstream OpenChatCut and without requiring the Cloudflare container. It uses a tracked synthetic video fixture only, a literal TEST text caption, and a generated silent AAC audio track (NOT a human speech synthesis), 7/15/30-second real renders, a bounded encoder, `ffprobe` verification, SHA256 hash of the rendered bytes, private R2 put/get and repeat `ffprobe` on downloaded bytes. The synthetic artifact is NOT user footage and must never be published.

No new cloud service and no additional paid model; no API calls to any AI provider. Tests guard bad source paths, duration, fake successful renders and missing media tracks; no shell interpolation or untrusted filter text.

Full Block6 still requires a genuine source-to-editor or agreed FFmpeg substitute integrated into the Factory job/revision handoff, protected preview and real end-to-end verification. This PR is a standalone alternate machine capability benchmark. Do not claim it completes SupoClip or OpenChatCut. After a genuine PASS, it may be integrated into the existing `MediaProductionRunner` as explicit opt-in failover instead of silently swapping media machine provenance.

Merge under Bülent's development scope only after CI, then the workflow's own file path triggers one synthetic real private R2 benchmark. If pending OpenChatCut upstream diagnostics already prove an immediately reparable path, this branch can remain unmerged and no duplicate media work is necessary.
