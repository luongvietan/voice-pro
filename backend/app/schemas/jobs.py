"""Job API schemas."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TranscribeJobResponse(BaseModel):
    job_id: UUID
    transcript: str
    language_detected: str
    segments: list[dict[str, Any]]


class SynthesizeRequest(BaseModel):
    transcript: str
    target_language: str = Field(..., min_length=2, max_length=32)


class SynthesizeResponse(BaseModel):
    job_id: UUID
    audio_base64: str
    mime_type: str = "audio/mpeg"


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    payload: str | None = None
