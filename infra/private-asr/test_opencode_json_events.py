#!/usr/bin/env python3
"""Regression tests for OpenCode JSON event stream parsing without importing media deps."""
import ast
from pathlib import Path

path = Path(__file__).with_name("service.py")
source = path.read_text(encoding="utf-8")
tree = ast.parse(source)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_opencode_text")
module = ast.Module(body=[node], type_ignores=[])
ns = {"json": __import__("json")}
exec(compile(module, str(path), "exec"), ns)
parse = ns["_opencode_text"]

event = '{"type":"text","timestamp":1,"sessionID":"ses_test","part":{"id":"prt_test","type":"text","text":"OPENCODE_CLAUDE_OK"}}'
assert parse(event) == "OPENCODE_CLAUDE_OK"
assert parse('{"type":"step_start","part":{}}\n' + event + '\n{"type":"step_finish","part":{}}') == "OPENCODE_CLAUDE_OK"

try:
    parse('{"type":"step_finish","part":{}}')
except ValueError as exc:
    assert str(exc) == "missing_opencode_text"
else:
    raise AssertionError("missing text event must fail closed")

try:
    parse("not-json")
except ValueError as exc:
    assert str(exc) == "invalid_opencode_json"
else:
    raise AssertionError("invalid NDJSON must fail closed")

print("OPENCODE_JSON_EVENT_PARSE_OK")
