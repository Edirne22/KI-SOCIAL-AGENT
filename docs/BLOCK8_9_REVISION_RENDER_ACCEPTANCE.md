# Block 8/9: bounded automatic revision and intake repairs

Mandatory: PROJECT_GUARDRAILS.md, actual code, MASTER-SNAPSHOT.md.

Existing authenticated Dashboard review dispatch now applies canonical ACK/intake and a bounded FFmpeg producer. Fully understood requests: Neu rendern, Ton entfernen, Auf N Sekunden kürzen (1–99, never extend). Sources limited to MP4, 32 MiB, 120 seconds, 4096 pixels per dimension. No model/provider call, speech transcription, social publishing, new infrastructure or credential change.

Unsupported creative/object/text replacement remains BLOCKED_UNSUPPORTED_EDIT. No fabricated completion. Existing caption stays unchanged; technical checks do not newly certify editorial facts. Publication still requires independent editorial/rights/human clearance.

Persistence: exact authenticated ACK -> immutable ticket -> CAS-persisted plan -> private source SHA -> FFmpeg/probe -> private output roundtrip -> FinalQM/verified Golden Tablet -> CAS-persisted READY job -> immutable preview -> ETag pointer CAS. Restart after READY reuses output. Crash before output commit can render again and leave an unused private object, but cannot overwrite a competing canonical output/later human decision. No claim of exactly-once rendering.

The consumer handles a second pending human request before replaying the prior completed render. Resume revalidates ticket, source, state; the current preview is required for completed status. TTL remains two hours. Posting authority remains absent.

Repairs: Python sorted JSON versus JS field-order comparison; MP4 offered but rejected by upload; microphone setup/start/error cleanup, concurrent starts, 2-minute/8-MiB bounds and no failed partial upload; inbox refuses truncated latest listing (single-list bound now 1000); workflow input passed by quoted environment variable.

Local tests before workspace reset: 64 Python, 90 Node, SOURCE-FACT PASS. Recovered code rechecked with actual FFmpeg revision tests and all 90 Node tests including real Python-produced canonical records. R2 transport is simulated locally. GitHub repeats the full suite with installed requests, then trusted main runs a synthetic-only real private R2 test. That test creates a NEW synthetic job, accepts no caller job ID, and uses generated video/tone. Simulated owner event is never claimed as real browser/human acceptance. Live/merge/deploy evidence remains pending until actual runs complete.

Not completed by this scope: arbitrary creative object edits, private server Whisper transcription, actual microphone/desktop/mobile owner acceptance, Telegram notifications, expired-preview renewal, orphan-media cleanup. No private voice or actual social post used.

## Verified final evidence (2026-10-03)

PR337 merged f9d256760123acaa35acd677ebe937c06bd604b0 after five exact-head green workflows. Cloudflare guarded deploy 37102063107 SUCCESS. Initial live run 37102063087 failed at the strict unauthenticated HTTP control (Python-urllib received 403 / Cloudflare 1010); the private revision had already been created. No failed run was presented as complete.

PR338 merged f8e06babaaed1966335c4b627102c79183dfa4d5 after CI 37102409338 SUCCESS. Existing requests dependency now carries an honest application User-Agent, disallows redirects and keeps exact 401 control, owner token and one-shot POST. No Cloudflare rule or auth gate weakened.

Main run 37102493064 SUCCESS: 67 Python tests, 90 Node tests and SOURCE-FACT PASS. Live job 111144749416 logged BLOCK89_LIVE_DASHBOARD_STATUS_VIDEO_SHA_OLD_PREVIEW_REVOKED_MP4_UPLOAD_PASS. Real R2 and deployed Dashboard verified new revision, byte SHA, unauthenticated 401, old preview 404, new synthetic MP4 draft upload and identical private download. Job 2cd0a22f-4626-473f-b71a-560ea410ff83 revision 2, preview 10a7c569-4560-41fe-b578-db32a32087fd; replay leaves same store version/output. Human browser acceptance remains false; published=false. Only generated blue video and sine tone, no private speech.

Final test-only tightening requires the expected missing-ACK exception AND asserts the renderer was never called; concurrent-CAS test requires ConcurrentUpdateError. No runtime change or additional live rerender is required for that test assertion change.
