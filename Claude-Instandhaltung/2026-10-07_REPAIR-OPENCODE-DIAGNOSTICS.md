# Repair Report: OpenCode CODE Route & Sanitized Error Diagnostics

- **Repair-ID:** `REPAIR-2026-10-07-OPENCODE-DIAG`
- **Datum:** 2026-10-07
- **Maschine / Tool:** OpenCode / Cloudflare Worker / Dashboard CODE Console / Private ASR Service
- **Task / Stage:** OpenCode CODE Route Dispatch & Sanitized Runtime Diagnostics
- **Fehlerklasse:** `OPENCODE_CODE_LIVE_FAILED` (body withheld) / Route Disconnect in Dashboard

## 1. Root Cause
1. **Uninformative Error Suppressions (`body withheld`):** When `opencode` CLI or workspace preparation failed in `infra/private-asr/service.py`, stdout/stderr details were discarded and returned as generic HTTP 502/503 errors. Downstream deployment workflows in `.github/workflows/private-asr-cloudflare-deploy.yml` suppressed response bodies as `(body withheld)`, preventing Agent 21 and developers from diagnosing the exact failure layer.
2. **Dashboard Route Disconnect:** In `infra/ai-central-dashboard/src/index.js`, messages from sessions with `session.mode === "code"` were erroneously hardcoded to fetch `https://private-asr/opencode/chat` instead of `https://private-asr/opencode/code`.
3. **Status Coupling Risk:** Need to enforce explicit domain status separation (`VIDEO_PRODUCTION_STATUS`, `CODE_STATUS`, `RUNTIME_STATUS`, `AGENT_STATUS`, `QM_STATUS`) so `CODE` or `RUNTIME` degradation cannot alter protected video statuses (e.g., `READY_FOR_HUMAN`).

## 2. Reparatur-Massnahmen
- **`infra/private-asr/service.py`:** Added `_sanitize_diagnostic(raw)` to redact secrets, tokens, and authorization headers, and include sanitized `detail` in 502/503 JSON responses.
- **`infra/ai-central-dashboard/src/index.js`:** Updated `chatMessage()` to dispatch `session.mode === "code"` requests to `https://private-asr/opencode/code`.
- **`.github/workflows/private-asr-cloudflare-deploy.yml`:** Updated the CODE live smoke step to parse and display sanitized `error`, `detail`, `body_bytes`, and `content_type` fields on non-200 HTTP responses rather than withholding bodies.
- **`agents/11_system_restart_agent.md` & `agents/21_instandhaltungsagent.md`:** Documented explicit status domain decoupling.
- **Tests Updated:** `infra/private-asr/test_opencode_runtime_contract.py` and `infra/ai-central-dashboard/tests/dashboard.test.mjs` updated and passing.

## 3. Nachweise
- Node test suite (`node --test infra/ai-central-dashboard/tests/dashboard.test.mjs`): 26/26 PASS.
- Python test suites (`test_opencode_runtime_contract.py`, `test_telegram_bot_bugs.py`, `racing_v85_selftest.py`, `racing_pipeline_selftest.py`, `racing_final_guard_selftest.py`): PASS.
- Task `f6f50c9f4c2690e4eb1fe978` (`Dünya – Level 12`) state protected in `READY_FOR_HUMAN`.

## 4. Endzustand
VERIFIED / TESTED / PASS
