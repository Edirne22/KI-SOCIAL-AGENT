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
import subprocess
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
        source = Path(folder) / ("input." + {"audio/webm":"webm",
                "audio/mp4":"m4a", "audio/x-m4a":"m4a", "audio/m4a":"m4a",
                "audio/ogg":"ogg"}[request.mime])
        source.write_bytes(audio)
        prepared = Path(folder) / "prepared.wav"
        # Decode only after canonical R2 metadata, digest and consent validation.
        # No shell, network or external converter; output stays ephemeral.
        try:
            subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                            "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
                            "-c:a", "pcm_s16le", str(prepared)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=90)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            raise PrivateASRError("private audio decoding failed") from exc
        if not prepared.is_file() or prepared.stat().st_size < 44:
            raise PrivateASRError("private decoded audio unavailable")
        # Context guides spelling of known names; actual audio remains authoritative.
        vocabulary = {
            "de": "Bülent. Edirne 22. BMW M 1000 R. Motorradtour.",
            "tr": "Bülent. Edirne 22. BMW M 1000 R. Motosiklet turu.",
        }
        segments, info = model.transcribe(str(prepared), language=request.language,
                                          vad_filter=True, beam_size=5,
                                          initial_prompt=vocabulary[request.language])
        if getattr(info, "language", None) not in (None, request.language):
            raise PrivateASRError("ASR returned different language")
        text = " ".join(s.text.strip() for s in segments).strip()
    transcript = PrivateASRTranscript(request.inbox_id, request.sha256,
                                      request.language, text)
    bind_transcript(request, transcript)
    return transcript
