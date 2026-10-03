"""Offline text-level ASR comparison; no audio, downloads, or private data.

Usage:
python tools/asr_compare.py --input path/to/paired-results.json

Input: {"cases":[{"language":"de","reference":"...", "baseline":"...", "candidate":"...", "names":["Bülent"]}]}
Real ASR measurements require separately generated/licensed audio and actual paired model outputs.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


def tokens(text):
    return re.findall(r"[^\W_]+(?:['’-][^\W_]+)*", unicodedata.normalize("NFC", text).casefold(), re.UNICODE)


def alignment(reference, hypothesis):
    """Return substitution, deletion, insertion counts using Levenshtein traceback."""
    a, b = tokens(reference), tokens(hypothesis)
    dp = [[(0, 0, 0, 0) for _ in range(len(b) + 1)] for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        d = dp[i - 1][0]
        dp[i][0] = (d[0] + 1, d[1], d[2] + 1, d[3])
    for k in range(1, len(b) + 1):
        d = dp[0][k - 1]
        dp[0][k] = (d[0] + 1, d[1], d[2], d[3] + 1)
    for i in range(1, len(a) + 1):
        for k in range(1, len(b) + 1):
            opts = []
            if a[i - 1] == b[k - 1]:
                opts.append(dp[i - 1][k - 1])
            else:
                d = dp[i - 1][k - 1]
                opts.append((d[0] + 1, d[1] + 1, d[2], d[3]))
            d = dp[i - 1][k]
            opts.append((d[0] + 1, d[1], d[2] + 1, d[3]))
            d = dp[i][k - 1]
            opts.append((d[0] + 1, d[1], d[2], d[3] + 1))
            dp[i][k] = min(opts)
    return dp[-1][-1][1:]


def contains_phrase(text, phrase):
    t, p = tokens(text), tokens(phrase)
    return any(t[i:i + len(p)] == p for i in range(len(t) - len(p) + 1)) if p else False


def evaluate(case, key):
    ref, hyp = case["reference"], case[key]
    sub, delete, insert = alignment(ref, hyp)
    names = case.get("names", [])
    return {"substitutions": sub, "deletions": delete, "insertions": insert,
            "reference_words": len(tokens(ref)),
            "name_hits": sum(contains_phrase(hyp, n) for n in names if contains_phrase(ref, n)),
            "name_total": sum(contains_phrase(ref, n) for n in names),
            "unprompted_names": [n for n in names if not contains_phrase(ref, n) and contains_phrase(hyp, n)]}


def compare(cases):
    result = {}
    for language in sorted({c["language"] for c in cases}):
        subset = [c for c in cases if c["language"] == language]
        result[language] = {}
        for key in ("baseline", "candidate"):
            rows = [evaluate(c, key) for c in subset]
            total = sum(x["reference_words"] for x in rows)
            result[language][key] = {
                "WER": round(sum(x["substitutions"] + x["deletions"] + x["insertions"] for x in rows) / total, 4) if total else None,
                "insertions": sum(x["insertions"] for x in rows),
                "name_hits": sum(x["name_hits"] for x in rows),
                "name_total": sum(x["name_total"] for x in rows),
                "unprompted_names": [n for x in rows for n in x["unprompted_names"]],
            }
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    args = p.parse_args()
    cases = json.loads(Path(args.input).read_text(encoding="utf-8"))["cases"]
    print(json.dumps(compare(cases), ensure_ascii=False, indent=2))
