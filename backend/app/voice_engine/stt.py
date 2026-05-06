"""
Speech-to-Text via Faster-Whisper (Epic 2).
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_ENV = "WHISPER_MODEL"
_DEFAULT_MODEL = "tiny"

_whisper_model = None
_model_lock = threading.Lock()


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        with _model_lock:
            if _whisper_model is None:
                from faster_whisper import WhisperModel

                name = os.environ.get(_MODEL_ENV, _DEFAULT_MODEL)
                device = os.environ.get("WHISPER_DEVICE", "cpu")
                ctype = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
                _whisper_model = WhisperModel(name, device=device, compute_type=ctype)
                logger.info("Loaded Whisper model %s (%s)", name, device)
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, language: str | None = None) -> dict[str, Any]:
    """
    Transcribe audio (WebM/MP3/WAV bytes). Faster-Whisper reads via ffmpeg internally.
    Returns dict: transcript, language_detected, segments (list of dicts).
    """
    if not audio_bytes:
        return {"transcript": "", "language_detected": "unknown", "segments": [], "duration_seconds": 0.0}

    suffix = ".webm"
    lower = audio_bytes[:16]
    if lower.startswith(b"RIFF"):
        suffix = ".wav"

    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        with open(path, "wb") as out:
            out.write(audio_bytes)

        model = _get_whisper_model()
        segments_iter, info = model.transcribe(path, language=language)
        segments: list[dict[str, Any]] = []
        texts: list[str] = []
        for seg in segments_iter:
            texts.append(seg.text)
            segments.append({"start": seg.start, "end": seg.end, "text": seg.text})
        transcript = "".join(texts).strip()
        lang = getattr(info, "language", None) or "unknown"
        duration = float(getattr(info, "duration", 0.0) or 0.0)
        return {
            "transcript": transcript,
            "language_detected": str(lang),
            "segments": segments,
            "duration_seconds": duration,
        }
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
