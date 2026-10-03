"""Private faster-whisper execution boundary (no GitHub/private audio access).

The trusted R2 gateway must verify the authenticated inbox object, obtain
fresh explicit consent and supply the original bytes. This module validates
those bytes and runs ONLY a pre-provisioned local model; it never downloads a
model or forwards recordings to an external API.
"""
from __future__ import annotations
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import tempfile
from content_factory_private_asr import (
    MAX_AUDIO_BYTES, PrivateASRError, PrivateASRRequest,
    PrivateASRTranscript, bind_transcript,
)

def transcribe_private_audio(request: PrivateASRRequest, audio: bytes, *,
                             model=None, model_dir=None) -> PrivateASRTranscript:
    if not isinstance(audio, bytes) or not audio or len(audio) > MAX_AUDIO_BYTES:
        raise PrivateASRError("invalid private audio payload")
    if len(audio) != request.size or sha256(audio).hexdigest() != request.sha256:
        raise PrivateASRError("original private audio size or digest mismatch")
    if model is None:
        local = model_dir or os.environ.get("EDIRNE22_LOCAL_WHISPER_MODEL")
        if not local or not Path(local).is_dir():
            raise PrivateASRError("private local faster-whisper model not provisioned")
        # Import only after local model and request are verified. Never download
        # via a Hugging Face model identifier or use an external inference API.
        from faster_whisper import WhisperModel
        model = WhisperModel(str(Path(local).resolve()), device="cpu", compute_type="int8",
                             local_files_only=True)
    # Temporary file stays inside private execution runtime and is removed
    # even when decoder/model inference raises.
    with tempfile.TemporaryDirectory(prefix="edirne22-private-asr-") as folder:
        path = Path(folder) / ("input." + {"audio/webm":"webm",
                "audio/mp4":"m4a", "audio/x-m4a":"m4a", "audio/m4a":"m4a", "audio/ogg":"ogg"}[request.mime])
        path.write_bytes(audio)
        segments, info = model.transcribe(str(path), language=request.language,
                                          vad_filter=True, beam_size=1)
        if getattr(info, "language", None) not in (None, request.language):
            raise PrivateASRError("ASR returned different language")
        text = " ".join(s.text.strip() for s in segments).strip()
    transcript = PrivateASRTranscript(request.inbox_id, request.sha256,
                                      request.language, text)
    bind_transcript(request, transcript)
    return transcript
