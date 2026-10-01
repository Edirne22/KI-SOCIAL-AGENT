# Step 1: NVIDIA Team + Token Budget + Shared Dashboard / Telegram

Authoritative: PROJECT_GUARDRAILS.md. Work based on verified main ffa1e99059cebc03ac6f7acd346387d3bd7ce037 and V6 handover. Historical docs may lag; read actual code and latest run logs.

## What is actually wired by this PR
- Reuses existing R2 inbox and the **single existing** authorized Telegram poller.
- Legacy reviewed free-only remains default, unchanged (OpenRouter/free).
- Explicit /zentrale team TASK_ID or dashboard NVIDIA button queues the already-live-proven direct Nemotron+Kimi free-team route, with independent OpenRouter/free challenge allowed to return UNAVAILABLE. No paid aliases or model-suggested actions.
- Job dispatcher must re-read exact R2 approved task and require the matching mode. A guessed GitHub dispatch may NOT reinterpret a legacy free-only task as NVIDIA free-team or vice versa; R2 ETag prevents duplicate starts.
- No NVIDIA or other provider calls occur merely by writing a Telegram draft or dashboard task. Only an explicit authorized Start action triggers inference.
- Adds deterministic context/token budgeter: full original user/source evidence remains intact; ONLY bounded untrusted peer descriptions are reduced or omitted. No reliance on OmniRoute process; cannot remove facts, references, attribution or silently convert hypotheses into source truth. Token savings are estimated by reducing characters, not a guarantee of precise tokenizer counts.
- Existing R2 report fields and status lifecycle are reused; PENDING_REVIEW means a report archived for human assessment, **not** 3/3 models answered. Result UI must show each role's status.
- Gemini and Groq direct one-call candidate proof was merged separately in PR #289 but not manually live-proven on actual account Free tiers. Do NOT auto-enable or infer a free account from presence of secrets. Expand role router only after safe live check; keep OpenCode Claude-only paid-risk route separate.
- No OmniRoute dependency, no container deployment, no auto-publishing, no new secrets, no claims Block 6 is already live.

## Required actual acceptance before claiming production ready
1. Syntax, regression, adversarial wrong-mode, double dispatch, peer-injection and source preservation controls GREEN in PR CI.
2. After merge, if permitted, dashboard Worker deployment must use its **existing** secrets and first pass a real authenticated proof from mobile/dashboard. No unapproved new costs.
3. Live actual authorized Telegram /zentrale team TASK_ID, R2 job state and exact report validation. Beware scheduled poller SUCCESS with **no updates** does not prove new Telegram command works.
4. Inspect real Nemotron/Kimi response models and any OpenRouter UNAVAILABLE, transparently flag partial success. If Cloudflare OpenChatCut persists with HTTP 000 on internal loopback, Block6 stays unaccepted until proven renderer→R2 SHA/ffprobe.

No new per-run OmniRoute installation. For Block 6, target existing PR #271 and stacked diagnostic #278 and verify actual Worker↔Container loopback before another full speculative deploy.
