# Hermes / Agent Reach GitHub Actions rollout
Status: opt-in smoke test only. Existing scheduled workflows remain untouched.
- Workflow: .github/workflows/hermes-agent-reach-smoke.yml (manual workflow_dispatch).
- Install Agent Reach with --safe; do not install extra system packages.
- Install Hermes headless without browser or persistent gateway.
- Verify hermes CLI, Agent Reach doctor and coordinator contract tests.
- GitHub Actions runners are ephemeral. This smoke test does not create an always-on Hermes agent, preserve Hermes memory, connect Telegram, or switch production dispatch.
- Before enabling production: pin and audit upstream versions; check Hermes model provider configuration and NVIDIA compatibility; implement real worker adapters and R2-backed state; test with one research-only job; require verified claims; stage shadow mode then canary and rollback.
- Publishing still requires explicit owner approval. No video from research-only requests.
