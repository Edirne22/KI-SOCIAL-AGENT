"""Isolated AST/behavior gate for AI engineer coding interview.

This only proves one tiny coding exercise; it is not production authorization.
"""
from __future__ import annotations
import ast
import json
import re
import sys
from pathlib import Path

ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg,
           ast.Return, ast.IfExp, ast.Compare, ast.Name, ast.Load, ast.Constant,
           ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.Eq, ast.NotEq,
           ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
           ast.Tuple, ast.List)
ARGS = ["license_id", "zero_cost", "days_since_release"]


def extract_text(raw):
    parts = []
    for line in raw.splitlines():
        try:
            item = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(item, dict):
            continue
        if item.get("type") == "error":
            raise ValueError("Provider returned an error event")
        if item.get("type") == "text" and isinstance(item.get("part"), dict):
            text = item["part"].get("text")
            if isinstance(text, str):
                parts.append(text)
    if not parts:
        raise ValueError("No valid OpenCode text response")
    result = "".join(parts).strip()
    # Optional single Markdown Python code fence, treated strictly as data.
    fenced = re.fullmatch(r"\x60{3}(?:python)?\s*\n(.*?)\n\x60{3}\s*", result, re.S)
    return fenced.group(1) if fenced else result


def verify_source(source):
    if not isinstance(source, str) or len(source.encode()) > 2500:
        raise ValueError("Oversized or missing source")
    tree = ast.parse(source)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("Require exactly one function")
    fn = tree.body[0]
    if fn.name != "classify_machine" or fn.decorator_list or fn.returns:
        raise ValueError("Wrong function name or metadata")
    a = fn.args
    if (a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg or
            a.defaults or a.kw_defaults or
            [x.arg for x in a.args] != ARGS or
            any(x.annotation for x in a.args)):
        raise ValueError("Unexpected signature")
    if len(fn.body) != 1 or not isinstance(fn.body[0], ast.Return):
        raise ValueError("Only a single return expression is allowed")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED):
            raise ValueError("Forbidden syntax: " + type(node).__name__)
        if isinstance(node, ast.Name) and node.id not in ARGS:
            raise ValueError("Name outside approved inputs")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (str, int, bool, type(None))):
            raise ValueError("Unexpected constant")
    scope = {"__builtins__": {}}
    exec(compile(tree, "<isolated-interview>", "exec"), scope, scope)
    fn = scope["classify_machine"]
    cases = [
        (("MIT", True, 30), "ELIGIBLE"),
        (("Apache-2.0", True, 200), "ELIGIBLE"),
        (("BSD-3-Clause", True, 365), "ELIGIBLE"),
        (("MIT", True, 366), "WATCH"),
        (("MIT", True, -1), "BLOCKED"),
        (("MIT", False, 30), "BLOCKED"),
        (("proprietary", True, 30), "BLOCKED"),
        (("GPL-3.0", True, 30), "BLOCKED"),
        (("Apache-2.0", False, 900), "BLOCKED"),
        (("unknown", False, -1), "BLOCKED"),
    ]
    for values, expected in cases:
        outcome = fn(*values)
        if type(outcome) is not str or outcome != expected:
            raise ValueError("Incorrect classification for interview case")
    return {"ast_restricted": True, "behavior_cases": len(cases)}


if __name__ == "__main__":
    raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    print("ENGINEER_TRIAL", json.dumps(verify_source(extract_text(raw)), sort_keys=True))
