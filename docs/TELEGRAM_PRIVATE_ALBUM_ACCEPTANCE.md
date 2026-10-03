# Telegram private albums — LIVE acceptance protocol (PR #371)

## Governing boundaries

Scope: **only** the owner's explicit `/privat` photo/video album through the **single** existing Telegram poller into the private R2 lane. No social posting, external vision, public URLs, automatic editor execution, added paid service, personal media in CI, or parallel Telegram `getUpdates` consumers.

Three separate proofs are required. Never label a green synthetic run as an actual Telegram delivery.

## Acceptance matrix

| Check | Evidence required | Status |
|---|---|---|
| Synthetic full router: private album, out-of-order, duplicate, retry, CAS race, UTC-midnight, malformed media and unauthorized chat | `Private Telegram Album Regression`, complete tests and syntax on same PR head | Confirm latest CI |
| **Real R2** with entirely synthetic, locally generated photos/video and synthetic Telegram transport | Explicitly manual branch-only job `telegram-album-real-r2-synthetic-telegram`: stdout `LIVE_R2_SYNTHETIC_TELEGRAM_ALBUM_PASS` | **NOT YET EXECUTED** |
| Real Telegram owner album sent and handled by deployed single main poller | Owner's private bot receipt with exact `tgalbum...` job ID | **AWAITING OWNER + DEPLOYMENT** |
| Real R2 manifest + original object metadata + correct count after real receipt | Manually dispatched main-only job `owner-album-metadata-readonly-after-deploy`: `REAL_TELEGRAM_R2_METADATA_PASS` | **AWAITING REAL RECEIPT** |
| Owner can retrieve/see expected files in private UI, if album player is available | Owner confirms actual photo/video playback or reports UI gap; do not treat R2 HEAD as a visual preview | **NOT PROVEN HERE** |
| No unintended publication / privacy boundary | Router has no media → publisher call and no publication was authorized; verify no resulting social posts for this test | Verify operationally |
| Existing unrelated commands | Relevant main and feature-branch regression results | Recheck final SHA |

## Phase A — manually run real R2 BEFORE merge (no personal data)

1. Open [R2 warehouse synthetic private live smoke](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/workflows/r2-warehouse-synthetic-live.yml).
2. Press **Run workflow**. Choose **`feature/guarded-telegram-album-import`**. Leave `album_job_id` blank; it is ONLY for the later owner-album metadata audit on main.
3. The job `telegram-album-real-r2-synthetic-telegram` runs only for an intentional manual dispatch on that exact feature branch. It uses EXISTING R2 repository secrets; no Telegram token or real photographs are provided to the job.
4. Check the log for **`LIVE_R2_SYNTHETIC_TELEGRAM_ALBUM_PASS`** and for no error. The job tests immutable originals, actual R2 reads/SHA-256, out-of-order quarantine, the owner's synthetic authorization, video, idempotence and a UTC-midnight split.
5. A normal pull-request R2 workflow run **will show the live job as SKIPPED**. This is intentional. The entire run may show green despite no live work; do not count that as Phase A PASS. `MISSING_R2_BINDING_...` is a real configuration blocker, not a green test.

## Phase B — real owner Telegram end-to-end

**Deployment sequencing:** `telegram-receive.yml` checks out and updates **main** on the 5-minute schedule. Thus messages sent now go to existing main code, not the PR branch. **Do not send real private test media before the PR code is live.** Do not run branch Telegram polling in parallel or disable the production poller silently. There are two legitimate ways to test: (1) a separately provisioned staging bot and its own chat/token, explicitly configured without sharing production `getUpdates`, or (2) after Phase A and final code review, an explicitly approved, guarded merge/deploy to main, followed by owner participation. Without one of these, the Telegram→R2 segment remains UNTESTED and no full acceptance may be claimed.

Once one safe test environment is active:

1. Owner sends a **small, non-sensitive test album** containing **2 test photos and 1 short test video**, in **one Telegram album** to the designated bot, caption `/privat` on the FIRST item. Do not send family/private/child photos for engineering tests. Telegram can deliver album items in non-caption order; this is supported by quarantine.
2. Wait for private bot messages. The final receipt contains `Privat in R2 gespeichert · tgalbum... · Keine Veröffentlichung.` Copy just the **`tgalbum...` ID** and note the exact number of album files. Extra `zurückgehalten` replies for out-of-order items are possible and are NOT successful uploads by themselves.
3. Confirm the response was from the authorized chat, that no public media URL or social post was created, and that a subsequent duplicate/retry does not create another asset. A second owner-initiated album is a separate ID; do not use it to assert idempotence.
4. Record only timestamp, short SHA, count, PASS/FAIL and GitHub run ID in the evidence table below. Keep original photos, filenames and chat ID out of issues, Actions logs, and reports.

## Phase C — remote read-only owner-album verification (after main deployment)

1. Open the same [R2 warehouse workflow](https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/workflows/r2-warehouse-synthetic-live.yml).
2. Press **Run workflow**, this time selecting **main**. Paste the exact `tgalbum...` ID from the owner's bot receipt into `album_job_id` and `3` (or the true album file count) into `expected_count`.
3. Check ONLY the job `owner-album-metadata-readonly-after-deploy` for `REAL_TELEGRAM_R2_METADATA_PASS`. It validates the private index/manifest, expected count, distinct asset IDs, absence of quarantined remnants, R2 HEAD object existence, byte lengths and MIME. It DOES NOT download personal photo/video bytes into CI.
4. A green metadata audit does **not** independently verify stored file SHA-256; real visual playback and checksum validation must happen in an owner-private runtime or UI. Do not print file names, object keys, private hashes, chat ID or original media in GitHub logs.
5. If the expected asset count is wrong, a MIME/size differs, quarantine remains, or owner receipt is missing: **FAIL**; inspect the legitimate bot run and correct the root cause, then rerun the entire affected staffellauf.

## Boundaries and known gaps

- Telegram Bot API has media size limits (current implementation bounds direct downloads to <19 MiB); larger media uses the dashboard upload, not this bot-album acceptance.
- A metadata-only quarantine entry is retained until an owner caption is received and replay succeeds; the **per-album** cap is 100. There is not yet a time-based cleanup or a global quarantine cap. A long-unapproved album must not be described as accepted; archive/retention policy is a separate follow-up.
- Current receipt confirms R2 upload only; it does **not** prove that Block-8 video preview/rendering, AI processing or any Social publisher ran. Those remain distinct acceptance scopes.
- A manual real-R2 synthetic smoke test does not verify Telegram's real network or real user message ordering; Phase B is indispensable.
- Deployment/merge authority is governed by `PROJECT_GUARDRAILS.md`; private media require owner participation and no test authorizes publication.

## Evidence log (fill only with actual observed results)

| Stage | HEAD / Run | Result | Next action |
|---|---|---|---|
| Synthetic CI on final SHA | Pending latest regression | PENDING | Read test logs |
| Phase A real R2 with synthetic Telegram | Not dispatched yet | PENDING | Manual branch run |
| Phase B real owner Telegram | Not sent to deployed PR code | PENDING | Safe environment + owner album |
| Phase C read-only metadata audit | No real receipt yet | PENDING | Manual main run with actual job ID |
| Private UI playback and no-publication owner check | Not checked | PENDING | Owner inspection |

Full LIVE acceptance requires PASS on Phase A **and** Phase B **and** Phase C, plus appropriate privacy and preview scope evidence. Tests passing alone are not merge or publication authority.
