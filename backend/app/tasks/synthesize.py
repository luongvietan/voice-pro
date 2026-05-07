"""Celery task: translate + TTS → payload on Job."""

from __future__ import annotations

import base64
import json
import logging
import uuid

from app.celery_app import celery_app
from app.config import get_settings
from app.db.models import Job
from app.db.session import get_session_factory
from app.services.credit_metering import apply_transcribe_credit_metering, failure_payload
from app.services.job_account_guard import abort_job_if_user_soft_deleted
from app.utils.sync_timeout import run_sync_with_timeout
from app.voice_engine.translate import translate_text
from app.voice_engine.tts import synthesize as tts_synthesize

logger = logging.getLogger(__name__)

# edge-tts generates MP3 at ~32 kbps → ~4000 bytes/second
_TTS_BYTES_PER_SECOND = 4000.0


@celery_app.task(name="jobs.synthesize_speech")
def synthesize_speech_task(job_id: str, transcript: str, target_language: str) -> dict:
    factory = get_session_factory()
    session = factory()
    jid = uuid.UUID(job_id)
    try:
        job = session.get(Job, jid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        if abort_job_if_user_soft_deleted(session, job):
            return {"cancelled": True, "reason": "ACCOUNT_DELETED"}
        job.status = "processing"
        session.commit()

        settings = get_settings()
        translated = run_sync_with_timeout(
            lambda: translate_text(transcript, source_lang="auto", target_lang=target_language),
            timeout_seconds=settings.translate_timeout_seconds,
            operation_label="translate_text",
        )
        audio_bytes = tts_synthesize(
            translated,
            language=target_language,
            timeout_seconds=settings.tts_timeout_seconds,
        )
        b64 = base64.b64encode(audio_bytes).decode("ascii")

        # P16: apply credit metering — estimate duration from audio byte length
        duration_sec = len(audio_bytes) / _TTS_BYTES_PER_SECOND
        ok, err = apply_transcribe_credit_metering(session, job=job, duration_seconds=duration_sec)
        if not ok:
            try:
                job.payload = failure_payload(err or "CREDIT_EXHAUSTED")
                job.status = "failed"
                session.commit()
            except Exception:
                session.rollback()
            return {"credit_exhausted": True, "error": err or "CREDIT_EXHAUSTED"}

        payload_out = json.dumps({"translated_text": translated, "audio_base64": b64, "mime_type": "audio/mpeg"})
        job.payload = payload_out
        job.status = "completed"
        session.commit()
        return {"job_id": job_id, "audio_base64": b64, "mime_type": "audio/mpeg", "translated_text": translated}
    except Exception as exc:
        logger.exception("synthesize_speech_task failed")
        try:
            job = session.get(Job, jid)
            if job is not None:
                job.status = "failed"
                job.payload = json.dumps({"error": str(exc)})
                session.commit()
        except Exception:
            session.rollback()
        raise
    finally:
        session.close()
