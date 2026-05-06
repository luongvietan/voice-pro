from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserMeResponse(BaseModel):
    id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    balance_minutes: int
    is_paid: bool = False
    settings: dict[str, Any] = Field(default_factory=dict)
