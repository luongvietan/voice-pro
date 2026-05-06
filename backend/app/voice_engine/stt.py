"""
Speech-to-Text adapter (Epic 2).
Wraps `app.abus_asr_faster_whisper` from Voice-Pro legacy codebase.

Requires PYTHONPATH to include repo root so `import app.xxx` resolves.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

_FASTER_WHISPER_MODULE = "app.abus_asr_faster_whisper"


def _lazy_import(module_path: str) -> Any:
    """Import legacy module lazily — raises clear error if PYTHONPATH not set."""
    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"Cannot import '{module_path}'. "
            "Ensure PYTHONPATH includes the Voice-Pro repo root. "
            f"Original error: {exc}"
        ) from exc


def transcribe_audio(audio_bytes: bytes, language: str | None = None) -> dict[str, Any]:
    """
    Transcribe PCM audio bytes using Faster-Whisper.

    Returns dict: {"transcript": str, "segments": list, "language_detected": str}
    This is a stub — implement in Epic 2 Story 2.3.
    """
    raise NotImplementedError(
        "STT adapter is a stub. Implement in Epic 2 / Story 2.3 using _lazy_import()."
    )
