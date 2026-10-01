"""Deterministic token/prompt budgeter for advisory cross-checks.

Never summarize or truncate user evidence, source references, numbers, or
attribution. If the budget cannot fit untrusted peer text, omit that text and
explicitly declare the omission. A provider-side tokenizer is not assumed.
"""
from __future__ import annotations

def challenge_evidence(original: str, peer: list[str], limit: int = 2500) -> str:
    if not isinstance(original, str) or len(original) > limit:
        raise ValueError("ORIGINAL_EVIDENCE_EXCEEDS_LIMIT")
    if not peer:
        return original
    delimiter = "\nUNTRUSTED PEER CLAIMS FOR ADVERSARIAL REVIEW ONLY:\n"
    omission = "\n[PEER_DETAILS_OMITTED_FOR_BUDGET; ORIGINAL_EVIDENCE_PRESERVED]"
    if len(original) + len(delimiter) + len(omission) > limit:
        # No transformation of source/user evidence and no invented facts.
        return original
    room = limit - len(original) - len(delimiter)
    accepted = []
    for line in peer:
        if not isinstance(line, str):
            raise TypeError("invalid peer text")
        line = line.replace("\x00", "")[:600]
        projected = len("\n".join(accepted + [line]))
        if projected + len(omission) > room:
            return original + delimiter + "\n".join(accepted) + omission
        accepted.append(line)
    return original + delimiter + "\n".join(accepted)
