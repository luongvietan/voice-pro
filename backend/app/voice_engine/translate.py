"""
Machine Translation via Deep-Translator (Epic 2).

Google Translate qua deep-translator có giới hạn độ dài (~5000 ký tự). Ta chunk an toàn tại 4500.
"""

from __future__ import annotations

import re

# Dưới ngưỡng 5000 của Google để tránh lỗi im lặng (Epic 8.2).
_GOOGLE_TRANSLATE_SAFE_MAX_CHARS = 4500

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


def _hard_split(text: str, max_len: int) -> list[str]:
    return [text[i : i + max_len] for i in range(0, len(text), max_len)]


def _paragraph_aware_chunks(text: str, max_len: int) -> list[str]:
    """Chia text thành các đoạn ≤ max_len, ưu tiên ranh giới \\n\\n."""
    if len(text) <= max_len:
        return [text]
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        pieces = _hard_split(para, max_len) if len(para) > max_len else [para]
        for piece in pieces:
            if not buf:
                buf = piece
                continue
            merged = buf + "\n\n" + piece
            if len(merged) <= max_len:
                buf = merged
            else:
                chunks.append(buf)
                buf = piece
    if buf:
        chunks.append(buf)
    return chunks


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Dịch text; ``source_lang`` ``auto`` ủy quyền cho GoogleTranslator.

    Text dài hơn :data:`_GOOGLE_TRANSLATE_SAFE_MAX_CHARS` được chia chunk,
    dịch tuần tự và nối lại (giữ ``\\n\\n`` trong từng phần đã gộp).
    """
    from deep_translator import GoogleTranslator

    if not text.strip():
        return text

    tgt = _normalize_target(target_lang)
    src = "auto" if source_lang == "auto" else _normalize_target(source_lang)
    translator = GoogleTranslator(source=src, target=tgt)

    parts = _paragraph_aware_chunks(text, _GOOGLE_TRANSLATE_SAFE_MAX_CHARS)
    if len(parts) == 1:
        return translator.translate(parts[0])
    return "\n\n".join(translator.translate(p) for p in parts)
