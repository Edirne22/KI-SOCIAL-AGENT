# Block 8/9: bounded automatic revision and intake repairs

Mandatory: PROJECT_GUARDRAILS.md, actual code, MASTER-SNAPSHOT.md.

Existing authenticated Dashboard review dispatch now applies canonical ACK/intake and a bounded FFmpeg producer. Fully understood requests: Neu rendern, Ton entfernen, Auf N Sekunden kürzen (1–99, never extend). Sources limited to MP4, 32 MiB, 120 seconds, 4096 pixels per dimension. No model/provider call, speech transcription, social publishing, new infrastructure or credential change.

Unsupported creative/object/text replacement remains BLOCKED_UNSUPPORTED_EDIT. No fabricated completion. Existing caption stays unchanged; technical checks do not newly certify editorial facts. Publication still requires independent editorial/rights/human clearance.

Persistence: exact authenticated ACK -> immutable ticket -> CAS-persisted plan -> private source SHA -> FFmpeg/probe -> private output roundtrip -> FinalQM/verified Golden Tablet -> CAS-persisted READY job -> immutable preview -> ETag pointer CAS. Restart after READY reuses output. Crash before output commit can render again and leave an unused private object, but cannot overwrite a competing canonical output/later human decision. No claim of exactly-once rendering.

The consumer handles a second pending human request before replaying the prior completed render. Resume revalidates ticket, source, state; the current preview is required for completed status. TTL remains two hours. Posting authority remains absent.

Repairs: Python sorted JSON versus JS field-order comparison; MP4 offered but rejected by upload; microphone setup/start/error cleanup, concurrent starts, 2-minute/8-MiB bounds and no failed partial upload; inbox refuses truncated latest listing (single-list bound now 1000); workflow input passed by quoted environment variable.

Local tests before workspace reset: 64 Python, 90 Node, SOURCE-FACT PASS. Recovered code rechecked with actual FFmpeg revision tests and all 90 Node tests including real Python-produced canonical records. R2 transport is simulated locally. GitHub repeats the full suite with installed requests, then trusted main runs a synthetic-only real private R2 test. That test creates a NEW synthetic job, accepts no caller job ID, and uses generated video/tone. Simulated owner event is never claimed as real browser/human acceptance. Live/merge/deploy evidence remains pending until actual runs complete.

Not completed by this scope: arbitrary creative object edits, private server Whisper transcription, actual microphone/desktop/mobile owner acceptance, Telegram notifications, expired-preview renewal, orphan-media cleanup. No private voice or actual social post used.
