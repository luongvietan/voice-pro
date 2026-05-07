"""Celery task: transcribe audio file → payload JSON on Job."""

from __future__ import annotations

import json
import logging
import os
import uuid

from app.celery_app import celery_app
from app.db.models import Job
from app.db.session import get_session_factory
from app.services.credit_metering import apply_transcribe_credit_metering, failure_payload
from app.services.job_account_guard import abort_job_if_user_soft_deleted
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
        if abort_job_if_user_soft_deleted(session, job):
            return {"cancelled": True, "reason": "ACCOUNT_DELETED"}
        job.status = "processing"
        session.commit()

        with open(audio_path, "rb") as f:
            raw = f.read()
        result = transcribe_audio(raw, language=language_hint)
        duration_sec = float(result.get("duration_seconds") or 0.0)
        payload_out = json.dumps(
            {
                "transcript": result["transcript"],
                "language_detected": result["language_detected"],
                "segments": result["segments"],
                "duration_seconds": duration_sec,
            }
        )
        ok, err = apply_transcribe_credit_metering(session, job=job, duration_seconds=duration_sec)
        if not ok:
            # P14: wrap commit in try/except to avoid leaving job in undefined state
            try:
                job.payload = failure_payload(err or "CREDIT_EXHAUSTED")
                job.status = "failed"
                session.commit()
            except Exception:
                session.rollback()
            # P1: return sentinel instead of raising — custom exceptions don't survive
            # Celery JSON serialization reliably across environments
            return {"credit_exhausted": True, "error": err or "CREDIT_EXHAUSTED"}

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
        try:
            os.unlink(audio_path)
        except OSError:
            pass
