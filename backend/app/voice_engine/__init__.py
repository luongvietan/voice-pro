"""
voice_engine — thin adapters around the legacy Voice-Pro `app/` modules.

Import pattern (inside Docker or with PYTHONPATH=repo-root):
    from app.abus_asr_faster_whisper import FasterWhisperASR
    from app.abus_tts_edge import EdgeTTS
    from app.abus_translate_deep import DeepTranslator

This package provides typed wrappers for use in Celery tasks (Epic 2+).
"""
