# Block 8/9 – Verified Video Studio acceptance and remaining production chain

Date: 2026-10-02. This document records only evidence verified during the owner's actual Desktop acceptance and the scoped UI improvement. It is NOT authority to post to social media, provision new paid runtimes or claim a finished render.

## Actual human-in-the-loop acceptance

- Browser desktop login/R2 activity and the real new synthetic 15s R2 FFmpeg preview were exercised by the owner. The previous preview expired under its fixed 2-hour TTL; new live registration from GitHub run `37024336756` was `eb8685ce-a494-482e-a8d9-640f595a92be`, job `187bf9c3-3461-4c9d-ad8f-7ec50c81b87d`, revision 1, **synthetic test only**.
- The owner requested an actual change in the private Dashboard. Real independent review consumer GitHub run `37025484062` ended successfully; server log confirms `BLOCK8_REVIEW_CANONICAL_APPLIED_AND_ACKNOWLEDGED` on that job, request `4dc089db-ac82-4dfa-8b96-70138557cecb`, action `change`, ACK `ACKNOWLEDGED`.
- The owner reloaded "Entscheidungen prüfen" and saw one persistent decision with time, revision, task and factory-applied status. This establishes Block 8 **private preview + durable human decision + canonical R2 review ACK** partial acceptance. It does not establish any new editable video version, fresh render or notification.
- Audio: owner verified private `aufnahme.webm` uploads and separate working Windows+H native dictation. Own private faster-whisper upload→transcript→editable text path remains unintegrated. Block 7 first-boot-only PR #318 has **no merge approval yet**.

## Scoped PR #324: one video workspace, truthful refresh

- Independent `Videostudio` tab is reachable from the same responsive Dashboard on phone and desktop. Video player, explicit change/discard confirmation, durable decision history and genuine newly-registered R2 preview notices live together; system logs/inbox and chat stay separate.
- Once manually enabled, browser checks authenticated `/api/previews` and `/api/reviews` every 30 seconds **only while the studio tab is active**. Notification banner indicates a new preview ONLY when its real trusted server-returned preview ID is newly observed relative to the already-retrieved baseline. Initial listing does not claim newly completed production. Reload cannot expose expired/rejected videos; server canonical guards remain authoritative. Manual refresh is the default.
- Do NOT auto-request notification permission, auto-dispatch model jobs, trigger paid GPU, run new media production, or post. There is no implemented Telegram or OS-level push notification in this change. Closing the browser stops local polling.
- Security/regression: existing server-owned R2 preview manifest, authenticated private video fetch, signed original video integrity validation, locked preview on review, single controlled human decision and canonical ACK all remain unchanged. Previous real Block8 run cannot be repeated as synthetic evidence of future rendering.

## Follow-up production gate – NOT IMPLEMENTED

A change request transitions the canonical Factory job to `CHANGES_REQUESTED` and advances its revision; that **is not a video-edit instruction directly executable by FFmpeg**. For example, changing a source motorcycle into a different supersport bike requires a new appropriately licensed/approved source or a rights-compatible media generation path; a caption-only FFmpeg test cannot silently masquerade as that material creative change.

Required separate, reviewable implementation/acceptance:
1. Derive an idempotent edit job from the **exact canonical ACKed** immutable review request+revised job record; never dispatch straight from unverified browser text. Reconcile timeout/retries and stale revision fail-closed; log request provenance.
2. Route edit to an explicitly selected free/approved capable production provider; check availability, source/media rights and provenance. If no approved way to fulfill the requested visual change, set an honest `BLOCKED_NEEDS_SOURCE_OR_APPROVAL` reason instead of generating a placeholder or marking creative edit PASS.
3. Re-run original content/source facts and media QC, verify actual revision-specific video content (not just FFmpeg exit code), upload private R2 artefact and register a new authenticated preview only once with revision/version lineage; never revive the stale prior preview.
4. Add actionable Factory statuses (`CHANGES_REQUESTED`, `AWAITING_APPROVED_MEDIA`, `RENDERING`, `QM_PENDING`, `PREVIEW_READY`, `BLOCKED`) **only when backed by persisted real states**, not a fake countdown. Private studio should display status for each canonical video rather than mixing R2 inbox task states.
5. Notify owner via Telegram only after true QC-pass and authenticated preview registration, using existing explicitly approved bot lane, idempotent notification key per canonical job+revision, and sanitized text; no unreviewed media URL/token, no overnight/quiet-hour violation. Optional browser notice requires a separate owner opt-in; no silent permission prompts.
6. Human must review each new private version and explicitly authorize every actual post. No direct publisher call from upload, text prompt, generic review ACK, CI fixture or test-only preview. Add negative/regression races, expired manifest, unauthenticated/forged payload, no-ready-media, duplicate notification, failed provider, safe refusal and positive control before offering live acceptance.
7. No real platform publication without owner’s specific per-post confirmation and verifiable source/rights/QM proof.

Merge policy: `PROJECT_GUARDRAILS.md` requires Bülent’s express PR-level approval. CI success is not acceptance or permission to merge.
