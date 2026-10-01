"""One-call, explicit opt-in candidate audit. NOT a production router or a price oracle.

Only exact provider/model combos documented on public Free tiers, and ONLY when
the operator has separately confirmed that this exact API key belongs to a free
account. No fallbacks, retries, paid aliases, cloud artifacts, or private tasks.
"""
from __future__ import annotations
import argparse
import json
import os
import requests

CANDIDATES = {
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.7-flash",
        "key": "GEMINI_API_KEY",
        "confirmed": "AI_GEMINI_ACCOUNT_FREE_CONFIRMED",
        "source": "https://ai.google.dev/gemini-api/docs/pricing",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "openai/gpt-oss-20b",
        "key": "GROQ_API_KEY",
        "confirmed": "AI_GROQ_ACCOUNT_FREE_CONFIRMED",
        "source": "https://console.groq.com/docs/rate-limits",
    },
}

def plan(name, env=None):
    """Fail closed before any network I/O or third-party billable endpoint."""
    env = os.environ if env is None else env
    if name not in CANDIDATES:
        raise ValueError("UNLISTED_PROVIDER")
    candidate = CANDIDATES[name]
    if env.get(candidate["confirmed"]) != "true":
        raise ValueError("ACCOUNT_FREE_TIER_NOT_CONFIRMED")
    if not env.get(candidate["key"]):
        raise ValueError("PROVIDER_KEY_MISSING")
    return candidate

def one_probe(name, env=None, transport=requests.post):
    env = os.environ if env is None else env
    candidate = plan(name, env)
    # A synthetic, public prompt; no personal/private R2 content enters this test.
    response = transport(
        candidate["url"],
        headers={"Authorization": "Bearer " + env[candidate["key"]],
                 "Content-Type": "application/json"},
        json={"model": candidate["model"], "temperature": 0,
              "max_tokens": 40,
              "messages": [{"role": "user",
                            "content": "Reply with precisely READY."}]},
        timeout=15,
    )
    if response.status_code != 200:
        return {"provider": name, "requested_model": candidate["model"],
                "status": "HTTP_ERROR", "http_status": response.status_code}
    try:
        body = response.json()
        answer = body["choices"][0]["message"]["content"]
        model = body.get("model", "")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("empty response")
        if not isinstance(model, str):
            model = ""
        # Never print complete answers, HTTP response bodies, headers, or API keys.
        return {"provider": name, "requested_model": candidate["model"],
                "reported_model": model[:100], "status": "ANSWER"}
    except (ValueError, KeyError, IndexError, TypeError):
        return {"provider": name, "requested_model": candidate["model"],
                "status": "INVALID_RESPONSE"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=sorted(CANDIDATES), required=True)
    args = p.parse_args()
    try:
        result = one_probe(args.provider)
    except ValueError as exc:
        result = {"provider": args.provider, "status": str(exc)}
    except requests.RequestException:
        result = {"provider": args.provider, "status": "NETWORK_UNAVAILABLE"}
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "ANSWER":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
