"""One bounded, non-production coding interview using a pre-existing NVIDIA key.

No repository writes, installations, shell commands, or user media access.
Do not print raw model answers or secrets. Fail closed on unavailable free quota.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"

TASK = (
    "Return only Python source, no explanation. Define exactly "
    "def classify_machine(license_id, zero_cost, days_since_release): "
    "as ONE function with ONE pure return expression (a nested conditional "
    "expression is okay). No imports, loops, calls, helpers, decorators, "
    "type annotations, assignments, or side effects. Output a string. "
    "Return BLOCKED if zero_cost is not True, days_since_release is negative, "
    "or license_id is not exactly one of MIT, Apache-2.0, BSD-3-Clause. "
    "Otherwise return ELIGIBLE if days_since_release <= 365, or WATCH if older. "
    "The rule is an artificial interview exercise, NOT a real license approval."
)

def main():
    token = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not token:
        raise SystemExit("TRIAL_BLOCKED: NVIDIA_API_KEY absent")
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": TASK}],
        "temperature": 0,
        "max_tokens": 450,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        URL, payload, method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read(100000).decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SystemExit("TRIAL_BLOCKED: provider error " + type(exc).__name__)
    choice = data.get("choices", [{}])
    answer = (choice[0].get("message", {}).get("content") if isinstance(choice, list) and choice else None)
    if not isinstance(answer, str) or not answer.strip():
        raise SystemExit("TRIAL_BLOCKED: empty or invalid model response")
    # The answer remains untrusted data; only the separate AST gate may inspect it.
    artifact = Path("trial-model-text.jsonl")
    artifact.write_text(json.dumps({"type": "text", "part": {"text": answer}}) + "\n", encoding="utf-8")
    print("MODEL_PROBE_RETURNED: response saved for restrictive AST gate; no source executed by this runner")

if __name__ == "__main__":
    main()
