"""Celery task: transcribe audio file → payload JSON on Job."""

from __future__ import annotations

import json
import logging
import os
import uuid

from app.celery_app import celery_app
from app.db.models import Job
from app.db.session import get_session_factory
from app.voice_engine.stt import transcribe_audio

logger = logging.getLogger(__name__)


@celery_app.task(name="jobs.transcribe_file")
def transcribe_file_task(job_id: str, audio_path: str, language_hint: str | None = None) -> dict:
    """Reads WAV/WebM file from disk, runs STT, updates Job row."""
    jid = uuid.UUID(job_id)
    factory = get_session_factory()
    session = factory()
    try:
        job = session.get(Job, jid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job.status = "processing"
        session.commit()

        with open(audio_path, "rb") as f:
            raw = f.read()
        result = transcribe_audio(raw, language=language_hint)
        payload_out = json.dumps(
            {
                "transcript": result["transcript"],
                "language_detected": result["language_detected"],
                "segments": result["segments"],
            }
        )
        job.payload = payload_out
        job.status = "completed"
        session.commit()
        return {
            "job_id": job_id,
            "transcript": result["transcript"],
            "language_detected": result["language_detected"],
            "segments": result["segments"],
        }
    except Exception as exc:
        logger.exception("transcribe_file_task failed")
        job = session.get(Job, jid)
        if job is not None:
            job.status = "failed"
            job.payload = json.dumps({"error": str(exc)})
            session.commit()
        raise
    finally:
        session.close()
        try:
            os.unlink(audio_path)
        except OSError:
            pass
