#!/usr/bin/env python3
"""Regression guard for the fixed OpenCode runtime contract.

This is intentionally static: importing service.py would pull the private media runtime
and external dependencies into CI. The test proves the three constants required by the
health/chat path exist exactly once, before either function can reference them.
"""
import ast
import json
from pathlib import Path

path = Path(__file__).with_name("service.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

expected = {
    "_opencode_model": "openrouter/anthropic/claude-sonnet-4.5",
    "_opencode_timeout": 90,
    "_opencode_max_output": 65536,
    "_code_executor_contract": "repo-readonly-v1",
    "_research_runtime_revision": "block9-groq-429-fallback-v1",
    "_private_video_runtime_revision": "duenya-creative-chain-v3",
}
seen = {}
first_function_line = min(
    node.lineno for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
)
for node in tree.body:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        continue
    target = node.targets[0]
    if isinstance(target, ast.Name) and target.id in expected:
        assert target.id not in seen, f"duplicate runtime constant: {target.id}"
        seen[target.id] = (ast.literal_eval(node.value), node.lineno)

assert set(seen) == set(expected), f"missing runtime constants: {set(expected) - set(seen)}"
for name, wanted in expected.items():
    value, line = seen[name]
    assert value == wanted, f"{name} changed: {value!r}"
    assert line < first_function_line, f"{name} must exist before runtime functions"


repo_root = Path(__file__).resolve().parents[2]
workflow = (repo_root / ".github/workflows/private-asr-cloudflare-deploy.yml").read_text(encoding="utf-8")
worker = (repo_root / "infra/private-asr-cloudflare/src/index.ts").read_text(encoding="utf-8")

restart_name = "Restart existing container once after deployment"
restart_path = "/admin/container-restart"
revision_name = "Authenticated target-revision health check"
research_name = "Authenticated live research smoke with source proof"
claude_name = "Authenticated OpenCode Claude live smoke"

assert restart_name in workflow, "deployment restart step missing"
assert workflow.count('url="https://edirne22-private-asr.butupeli.workers.dev/admin/container-restart"') == 1, "restart POST must be single-shot"
assert '-X POST -H "Authorization: Bearer $PRIVATE_ASR_INTERNAL_TOKEN"' in workflow, "restart must be authenticated POST"
assert 'if [ "$code" = 503 ]' in workflow, "transient restart must defer to revision health"
assert 'elif [ "$code" = 202 ]' in workflow, "ready restart must require HTTP 202"
assert 'assert d.get("status") == "container_restarted_ready"' in workflow, "202 must prove port readiness"
assert 'python3 scripts/private_asr_deploy_guard.py' in workflow, "strict health revision gate required"
assert 'PRIVATE_ASR_TARGET_REVISION_LIVE_FAILED"; exit 1' in workflow, "health exhaustion must fail closed"
assert workflow.index(restart_name) < workflow.index(revision_name), "restart must precede revision gate"
assert workflow.index(revision_name) < workflow.index(research_name), "revision gate must precede research smoke"
assert workflow.index(revision_name) < workflow.index(claude_name), "revision gate must precede Claude smoke"
assert restart_path in worker, "worker restart route missing"
assert "await instance.destroy()" in worker, "deploy restart must use documented direct container lifecycle destroy"
assert "restartForDeployment()" not in worker, "legacy restart RPC wrapper must not remain"
assert 'container_restart_failed' in worker, "restart failure must return bounded diagnostic"

service_text = path.read_text(encoding="utf-8")
dockerfile = (repo_root / "infra/private-asr/Dockerfile").read_text(encoding="utf-8")
code_config = (repo_root / "infra/ai-central-tools/claude-code-readonly/opencode.jsonc").read_text(encoding="utf-8")

assert '"/opencode/code"' in service_text, "CODE endpoint missing from container service"
assert worker.count('url.pathname === "/opencode/code"') >= 6, "CODE route must be wired through allow/method/body/readiness/health/proxy paths"
assert "def _prepare_code_workspace" in service_text, "CODE workspace preparation missing"
assert "def _sanitize_diagnostic" in service_text, "sanitized diagnostic helper missing"
assert "error_code=$(python3 -c" in workflow, "sanitized error_code extraction missing from workflow"
assert "detail=$(python3 -c" in workflow, "sanitized detail extraction missing from workflow"
code_cfg = json.loads(code_config)
code_model = code_cfg["providers"]["openrouter"]["models"]["anthropic/claude-sonnet-4.5"]
assert code_model["capabilities"]["tools"] is True, "CODE tools must be enabled"
rules = code_cfg.get("permissions")
assert isinstance(rules, list) and rules, "CODE permissions missing"
assert {"action":"edit","resource":"*","effect":"deny"} in rules, "CODE edits must stay denied"
assert {"action":"shell","resource":"git push*","effect":"deny"} in rules, "git push must stay denied"
assert {"action":"shell","resource":"git rev-parse*","effect":"allow"} in rules, "read-only git inspection must stay allowed"
assert " git nodejs npm" in dockerfile, "git must be installed in CODE runtime image"
assert "claude-code-readonly/opencode.jsonc" in dockerfile, "CODE policy must be copied into image"
assert "OPENCODE_CODE_GIT_TOOL_LIVE_OK" in workflow, "real CODE git-tool live smoke missing"
assert workflow.index("Authenticated OpenCode CODE git-tool live smoke") < workflow.index("Authenticated OpenCode Claude live smoke")

print("OPENCODE_RUNTIME_CONSTANTS_OK")
