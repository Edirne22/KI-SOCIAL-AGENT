"""Fail-closed conversational Telegram change-request state.

Pure boundary helper; caller must persist the returned context durably with
atomic compare-and-swap, authenticate sender and call the EXISTING canonical
review-intent API. This module never approves, publishes, or dispatches.
"""
from dataclasses import dataclass
from uuid import UUID
import re

MAX_FEEDBACK = 2000

@dataclass(frozen=True)
class PendingChange:
    chat_id: str
    actor_id: str
    job_id: str
    preview_id: str
    revision: int
    manifest: str
    request_id: str

    def __post_init__(self):
        for field in ("job_id", "preview_id", "request_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or str(UUID(value)) != value:
                raise ValueError("invalid immutable review identity")
        if not self.chat_id or not self.actor_id or not self.manifest:
            raise ValueError("missing authenticated review context")
        if type(self.revision) is not int or self.revision < 1:
            raise ValueError("invalid revision")

def prepare_change_text(context: PendingChange, *, chat_id: str, actor_id: str,
                        text: str, current_job_id: str, current_preview_id: str,
                        current_revision: int, current_manifest: str) -> dict:
    """Validate reply against the exact live preview before canonical submission."""
    if not isinstance(context, PendingChange):
        raise ValueError("pending change context required")
    if chat_id != context.chat_id or actor_id != context.actor_id:
        raise PermissionError("foreign review actor")
    if (current_job_id, current_preview_id, current_revision, current_manifest) != (
            context.job_id, context.preview_id, context.revision, context.manifest):
        raise ValueError("stale or replaced preview")
    if not isinstance(text, str) or not (1 <= len(text.strip()) <= MAX_FEEDBACK):
        raise ValueError("change feedback required (max 2000 chars)")
    if any(ord(char) < 32 and char not in "\n\t" for char in text):
        raise ValueError("invalid control character")
    if re.search(r"(?i)(?:authorization\s*:\s*bearer|api[_-]?key\s*[=:]|secret\s*[=:]|password\s*[=:])\s*\S+", text):
        raise ValueError("possible credential in feedback")
    return {
        "schema": "FACTORY-REVIEW-INTENT-V1",
        "request_id": context.request_id,
        "preview_id": context.preview_id,
        "job_id": context.job_id,
        "revision": context.revision,
        "manifest": context.manifest,
        "action": "change",
        "text": text.strip(),
    }
