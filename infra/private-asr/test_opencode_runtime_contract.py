#!/usr/bin/env python3
"""Regression guard for the fixed OpenCode runtime contract.

This is intentionally static: importing service.py would pull the private media runtime
and external dependencies into CI. The test proves the three constants required by the
health/chat path exist exactly once, before either function can reference them.
"""
import ast
from pathlib import Path

path = Path(__file__).with_name("service.py")
tree = ast.parse(path.read_text(encoding="utf-8"))

expected = {
    "_opencode_model": "openrouter/anthropic/claude-sonnet-4.5",
    "_opencode_timeout": 90,
    "_opencode_max_output": 65536,
    "_research_runtime_revision": "block9-groq-429-fallback-v1",
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

print("OPENCODE_RUNTIME_CONSTANTS_OK")
