"""
Machine Translation via Deep-Translator (Epic 2).
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ISO-like codes Edge/Google expect (extension sends these)
_LANG_MAP = {
    "vn": "vi",
    "vietnamese": "vi",
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "japanese": "ja",
    "korean": "ko",
    "chinese": "zh-CN",
}


def _normalize_target(code_or_name: str) -> str:
    key = code_or_name.strip().lower()
    if key == "zh-cn":
        return "zh-CN"
    if re.match(r"^[a-z]{2}(-[a-z]{2})?$", key):
        return key
    return _LANG_MAP.get(key, key[:2] if len(key) >= 2 else "en")


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text; source_lang 'auto' delegates to GoogleTranslator."""
    from deep_translator import GoogleTranslator

    if not text.strip():
        return text

    tgt = _normalize_target(target_lang)
    src = "auto" if source_lang == "auto" else _normalize_target(source_lang)
    translator = GoogleTranslator(source=src, target=tgt)
    return translator.translate(text)
