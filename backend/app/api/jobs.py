"""Jobs API — transcribe / synthesize / status."""

from __future__ import annotations

import os
import tempfile
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.models import Job, User
from app.db.session import get_db_session
from app.deps.auth import get_current_user
from app.schemas.jobs import JobStatusResponse, SynthesizeRequest, SynthesizeResponse, TranscribeJobResponse
from app.tasks.synthesize import synthesize_speech_task
from app.tasks.transcribe import transcribe_file_task

router = APIRouter(prefix="/jobs")


@router.post("/transcribe", response_model=TranscribeJobResponse)
def post_transcribe(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    data = file.file.read()
    fd, path = tempfile.mkstemp(suffix=".webm")
    os.close(fd)
    # P5: clean up temp file if DB operations fail before task dispatch
    try:
        with open(path, "wb") as fh:
            fh.write(data)

        job = Job(status="pending", user_id=user.id)
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise

    async_result = transcribe_file_task.delay(str(job.id), path, None)
    try:
        out = async_result.get(timeout=600)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # P1: check sentinel return value instead of relying on exception propagation
    if isinstance(out, dict) and out.get("credit_exhausted"):
        raise HTTPException(
            status_code=402,
            detail={"code": "CREDIT_EXHAUSTED", "message": "Không đủ phút credit cho đoạn audio này."},
        )

    return TranscribeJobResponse(
        job_id=UUID(out["job_id"]),
        transcript=out["transcript"],
        language_detected=out["language_detected"],
        segments=out["segments"],
    )


@router.post("/synthesize", response_model=SynthesizeResponse)
def post_synthesize(
    body: SynthesizeRequest,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    job = Job(status="pending", user_id=user.id)
    db.add(job)
    db.commit()
    db.refresh(job)

    async_result = synthesize_speech_task.delay(str(job.id), body.transcript, body.target_language)
    try:
        out = async_result.get(timeout=600)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # P16: check credit exhaustion sentinel from synthesize task
    if isinstance(out, dict) and out.get("credit_exhausted"):
        raise HTTPException(
            status_code=402,
            detail={"code": "CREDIT_EXHAUSTED", "message": "Không đủ phút credit cho đoạn audio này."},
        )

    return SynthesizeResponse(
        job_id=UUID(out["job_id"]),
        audio_base64=out["audio_base64"],
        mime_type=out.get("mime_type", "audio/mpeg"),
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: UUID, db: Session = Depends(get_db_session)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=job.id, status=job.status, payload=job.payload)
