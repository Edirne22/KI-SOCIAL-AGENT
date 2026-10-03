# R2 Media Warehouse V1 — strict separation

Status: ARCHITECTURE CONTRACT; implementation and live E2E pending. No new billing or deployment authorized by this document.

## Mandatory intake classification

Every Telegram/dashboard media upload MUST be assigned a lane BEFORE persistence:
- PRIVATE: family events, birthday, personal clips and any media with children. Default for ambiguous content and any unclassified upload. No social distribution.
- SOCIAL: explicitly designated social-media production input. Classification must be an explicit owner action, never guessed by a model or inferred from a caption.

A media item may never silently migrate between lanes. Moving private originals to social requires a separate, explicit owner decision for the specific assets; per-post publishing approval is still mandatory. Never use private family assets in a social agent's retrieval index or training corpus.

## Key layout (single bucket only if permissions enforce lane isolation; separate buckets preferred where available)

private/v1/YYYY/MM/DD/<job-id>/originals/<asset-id>/<sanitized-filename>
private/v1/YYYY/MM/DD/<job-id>/working/<revision>/<asset-id>
private/v1/YYYY/MM/DD/<job-id>/outputs/<revision>/<asset-id>
private/v1/YYYY/MM/DD/<job-id>/manifest.json

social/v1/YYYY/MM/DD/<job-id>/originals/<asset-id>/<sanitized-filename>
social/v1/YYYY/MM/DD/<job-id>/working/<revision>/<asset-id>
social/v1/YYYY/MM/DD/<job-id>/outputs/<revision>/<asset-id>
social/v1/YYYY/MM/DD/<job-id>/manifest.json

The YYYY/MM/DD folder uses UTC ingest date; manifest retains the source's original capture time and timezone separately, if reliable. Unique opaque job/asset IDs prevent collisions. Date partitions alone are not an index: store a private job index and list assets by manifest/job ID, never broad cross-lane scans. R2 folders are key prefixes, not physical directories.

## Manifest minimum

Schema MEDIA-JOB-MANIFEST-V1; job_id; lane; owner_chat_id hash (not raw public identifiers); display_title; event_date (optional); created_at; updated_at; status; ordered asset list with asset_id, original_filename sanitized, capture_time (if known), received_at, sha256, size, mime, R2 key, origin, processing consent; revisioned output list; explicit publication approvals separate from job-level access. Original assets are immutable. Reject unexpected media types, oversized payloads and filename traversal. Upload completion is acknowledged only after private durable write and verified metadata.

## Container contract

Telegram/dashboard intake streams uploads directly to the correct R2 lane (no durable storage in container). On reviewed production start: read only manifest-scoped inputs for one job, wake container, perform bounded render, verify checksum/QM, write revisioned output back to same R2 lane. Container local scratch is disposable; R2 originals survive restarts. Retrieval uses exact manifest keys and lane-scoped credentials. A failed render must never delete originals or pretend success.

## Security and lifecycle

Private family media: least-privilege separate access, authenticated previews, no public R2 URLs, no automatic social publication, no model training or third-party transfer without explicit approval. No automatic deletion policy until owner approves one. Secrets never in manifests/logs. Media containing children remains private by default. Keep explicit audit events for uploads, renders, lane transfer, approvals and deletion. Human per-post social approval remains required even for SOCIAL lane.

## Acceptance tests before activation

- Private birthday photos/video upload -> private manifest, chronological ordering and SHA verified.
- Social upload -> social-only manifest; no private asset visible in social search.
- Ambiguous upload -> private lane or clarification; never auto-social.
- Unauthorized cross-lane fetch and forged job ID -> denied.
- Container standby -> wake on approved job only, exact manifest fetch, output stored in same lane, revision preview protected.
- Retries -> no duplicate asset/job; failure -> no false Telegram success.
- Social post without individual human approval -> blocked.
- Live test uses synthetic media first; personal recordings only after owner initiates.
