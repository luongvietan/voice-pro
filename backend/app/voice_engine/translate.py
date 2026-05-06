"""
Machine Translation adapter (Epic 2).
Wraps `app.abus_translate_deep` from Voice-Pro legacy codebase.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text via Deep-Translator.

    Stub — implement in Epic 2 / Story 2.4.
    """
    raise NotImplementedError(
        "Translate adapter is a stub. Implement in Epic 2 / Story 2.4."
    )
