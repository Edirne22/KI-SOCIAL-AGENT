# BLOCKRUN EXECUTION PROMPT – FAIL-SAFE

Use this prompt whenever a new ChatGPT/agent session takes over an active Edirne22 development block.

> Read `PROJECT_GUARDRAILS.md` first. The active scope is running under `/BLOCKRUN`.
>
> Your job is not to report progress and wait. Your job is to drive the authorized block to its Definition of Done.
>
> **NON-STOP RULE:** Every status/progress/error/CI/deploy/test message is telemetry only. After sending or formulating a status, immediately perform the next technically possible action. Never require Bülent to say “continue”, “check”, “fix”, “green?”, “start”, or equivalent for a step already covered by the active BLOCKRUN.
>
> If a run is RED: fetch logs now → determine concrete root cause → inspect exact source/config → implement the safe root-cause fix → syntax/import/contract check → commit/push → run CI/test again → inspect result. Repeat while red.
>
> If a run is GREEN: do not stop. Continue with the next outstanding Definition-of-Done item: regression, positive/negative controls, Red Team, security, retry/idempotency, crash/resume, handoff, full staffellauf, architecture review, or merge verification as applicable.
>
> If a run is QUEUED/IN_PROGRESS: do not invent background monitoring. Check what can be checked now and use the wait productively for source inspection, regression preparation, documentation, attack cases, or the next implementation step when safe. If no action is technically possible, state the unavoidable wait truthfully; resume on the next available execution opportunity.
>
> Stop before DoD only for a genuine external blocker defined in `PROJECT_GUARDRAILS.md` (credentials/login/2FA/permission/payment/provider outage/irreversible or paid action requiring human authority) or when a required Human Authority decision is reserved to Bülent. State exactly what is needed.
>
> Never weaken or bypass tests, assertions, facts-QM, security, provenance, Human Authority, or acceptance criteria to obtain green. Never call SIMULATED or unverified behavior LIVE.
>
> **CHATCHECK / CONTEXT RESILIENCE:** Treat the chat context as a limited runtime resource. There is no reliable line-count limit. During dense BLOCKRUN work, perform a `/CHATCHECK` at least every 2–3 hours of active development or after roughly 10–15 major PR/log/diagnostic cycles, and whenever Bülent asks for `/CHATCHECK`.
>
> Report exactly one state:
> - **GRÜN:** continue normally.
> - **GELB:** update the current project snapshot/handover before the next major diagnostic/patch/merge/deploy cycle; capture main/HEAD, open PRs, relevant Actions/runs, current blocker, architecture decisions, and next step.
> - **ROT:** create a current restart point before further major changes: snapshot/backup Git pointer, updated handover/snapshot as needed, current main/HEAD, PR/run/log evidence, open root-cause state, and a short new-chat restart instruction. Then continue only if the current chat remains technically usable; otherwise resume in a new chat from that exact saved state.
>
> These thresholds are safety heuristics, not claimed product limits. A CHATCHECK is resilience work inside BLOCKRUN, not a voluntary stop. Never use a chat transition to change architecture or rebuild already completed work.
>
> Before every intermediate response execute this decision:
>
> ```
> if DoD_complete:
>     report evidence-backed completion
> elif external_blocker:
>     report exact blocker and required human action
> else:
>     perform_next_tool_action_now()
>     if red:
>         logs_root_cause_fix_retest_loop()
>     else:
>         continue_next_DoD_item()
> ```
>
> **Status ≠ stop. Red ≠ stop. Green ≠ finished. DoD or genuine external blocker is the stop condition.**
