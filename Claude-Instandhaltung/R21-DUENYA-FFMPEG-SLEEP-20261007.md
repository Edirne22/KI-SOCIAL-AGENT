# R21-DUENYA-FFMPEG-SLEEP-20261007 — private video FFmpeg stall

- Machine: `private-media-container`
- Task: `f6f50c9f4c2690e4eb1fe978`
- Stage: `video_editor_ffmpeg`
- Incident: `WD-f6f50c9f4c2690e4eb1fe978-video_editor_ffmpeg`
- Evidence: dashboard showed FFmpeg RUNNING with old stage times while FABRIK LIVE classified STALLED; watcher run 37537855083 emitted `DUENYA_WATCH_NEEDS_AGENT21:STALLED:video_editor_ffmpeg`.
- Root cause class: the HTTP request returns after spawning `_run_video` as a daemon/background thread, while the Cloudflare Container uses `sleepAfter = "15m"`. Cloudflare's Container lifecycle stops an instance after its inactivity timeout unless activity is renewed. The R2 heartbeat does not itself create Container-class incoming activity.
- Minimal repair: while a private video job is active, the existing 10-second heartbeat renews the fixed Worker activity path every third tick (~30 s) through authenticated `/health`. No user-controlled URL, no new provider, no new paid service, no publisher.
- Recovery: after a successful guarded Cloudflare deploy, exact-task Agent 21 reconciliation validates the immutable STALLED incident and stale heartbeat, marks only the orphaned FFmpeg state recoverable, then hands the exact task/stage/checkpoint to Agent 11's existing guarded RESUME adapter.
- Safety: fresh RUNNING and COMPLETED states are never restarted; wrong task/stage/incident fails closed; private prompt/media are not logged.
- Status: PATCHED; CI/deploy/recovery evidence pending.
