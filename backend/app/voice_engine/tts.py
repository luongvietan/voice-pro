"""
Text-to-Speech adapter (Epic 2).
Wraps `app.abus_tts_edge` from Voice-Pro legacy codebase.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def synthesize(text: str, language: str, voice: str | None = None) -> bytes:
    """
    Synthesise text to MP3 audio bytes using Edge-TTS.

    Stub — implement in Epic 2 / Story 2.4.
    """
    raise NotImplementedError(
        "TTS adapter is a stub. Implement in Epic 2 / Story 2.4."
    )
