"""Block 9: fail-closed private ASR request and transcript contracts.

This module does not fetch private recordings or start a model. It validates
metadata passed between an authenticated R2 intake and a private ASR worker.
No GitHub Actions job may receive a user's original recording.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

_AUDIO_MIME = frozenset({"audio/webm", "audio/mp4", "audio/ogg"})
_R2_KEY = re.compile(r"^ai-central/v1/uploads/[0-9a-f-]{36}/data$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MAX_AUDIO_BYTES = 8 * 1024 * 1024
MAX_TRANSCRIPT_CHARS = 2500

class PrivateASRError(ValueError):
    pass

@dataclass(frozen=True)
class PrivateASRRequest:
    inbox_id: str
    r2_key: str
    sha256: str
    size: int
    mime: str
    language: str
    consent_ref: str
    def __post_init__(self):
        if not _UUID.fullmatch(self.inbox_id):
            raise PrivateASRError("invalid inbox identity")
        if not _R2_KEY.fullmatch(self.r2_key):
            raise PrivateASRError("audio must originate in private intake")
        if not _SHA256.fullmatch(self.sha256):
            raise PrivateASRError("invalid original media digest")
        if type(self.size) is not int or not 0 < self.size <= MAX_AUDIO_BYTES:
            raise PrivateASRError("audio size outside intake limits")
        if self.mime not in _AUDIO_MIME:
            raise PrivateASRError("unsupported audio format")
        if self.language not in ("de", "tr"):
            raise PrivateASRError("explicit German or Turkish language required")
        if not isinstance(self.consent_ref, str) or not self.consent_ref.strip():
            raise PrivateASRError("explicit current consent required")

@dataclass(frozen=True)
class PrivateASRTranscript:
    inbox_id: str
    source_sha256: str
    language: str
    text: str
    def __post_init__(self):
        if not _UUID.fullmatch(self.inbox_id) or not _SHA256.fullmatch(self.source_sha256):
            raise PrivateASRError("invalid transcript source binding")
        if self.language not in ("de", "tr"):
            raise PrivateASRError("invalid transcript language")
        if not isinstance(self.text, str) or not self.text.strip() or len(self.text) > MAX_TRANSCRIPT_CHARS:
            raise PrivateASRError("transcript missing or exceeds dashboard limit")

def bind_transcript(request: PrivateASRRequest, transcript: PrivateASRTranscript) -> str:
    """Return editable text only for the exact consented source recording."""
    if request.inbox_id != transcript.inbox_id or request.sha256 != transcript.source_sha256:
        raise PrivateASRError("cross-job or stale audio transcript")
    if request.language != transcript.language:
        raise PrivateASRError("language mismatch")
    return transcript.text
