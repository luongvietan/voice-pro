"""Celery task: translate + TTS → payload on Job."""

from __future__ import annotations

import base64
import json
import logging
import uuid

from app.celery_app import celery_app
from app.db.models import Job
from app.db.session import get_session_factory
from app.voice_engine.translate import translate_text
from app.voice_engine.tts import synthesize as tts_synthesize

logger = logging.getLogger(__name__)


@celery_app.task(name="jobs.synthesize_speech")
def synthesize_speech_task(job_id: str, transcript: str, target_language: str) -> dict:
    factory = get_session_factory()
    session = factory()
    jid = uuid.UUID(job_id)
    try:
        job = session.get(Job, jid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.status = "processing"
        session.commit()

        translated = translate_text(transcript, source_lang="auto", target_lang=target_language)
        audio_bytes = tts_synthesize(translated, language=target_language)
        b64 = base64.b64encode(audio_bytes).decode("ascii")
        payload_out = json.dumps({"translated_text": translated, "audio_base64": b64, "mime_type": "audio/mpeg"})
        job.payload = payload_out
        job.status = "completed"
        session.commit()
        return {"job_id": job_id, "audio_base64": b64, "mime_type": "audio/mpeg", "translated_text": translated}
    except Exception as exc:
        logger.exception("synthesize_speech_task failed")
        job = session.get(Job, jid)
        if job is not None:
            job.status = "failed"
            job.payload = json.dumps({"error": str(exc)})
            session.commit()
        raise
    finally:
        session.close()
