"""
Text-to-Speech via Edge-TTS (Epic 2).
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# Primary neural voices per language prefix
_VOICE_BY_LANG: dict[str, str] = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-GuyNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "pt": "pt-BR-AntonioNeural",
    "it": "it-IT-DiegoNeural",
}


def _voice_for_language(language: str) -> str:
    key = language.strip().lower().split("-")[0]
    if key in _VOICE_BY_LANG:
        return _VOICE_BY_LANG[key]
    env = os.environ.get("EDGE_TTS_VOICE")
    if env:
        return env
    return _VOICE_BY_LANG["en"]


async def _save_mp3(text: str, voice: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        await communicate.save(path)
        with open(path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def synthesize(text: str, language: str, voice: str | None = None) -> bytes:
    """Synthesize MP3 bytes."""
    v = voice or _voice_for_language(language)
    return asyncio.run(_save_mp3(text, v))
