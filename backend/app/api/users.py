from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db_session
from app.deps.auth import get_current_user
from app.schemas.users import UserMeResponse
from app.services.subscription_util import user_has_paid_plan

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserMeResponse)
def read_me(user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    credits = user.credits_row
    bal = credits.balance_minutes if credits else 0
    is_paid = user_has_paid_plan(db, user.id)
    return UserMeResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        balance_minutes=bal,
        is_paid=is_paid,
        settings=dict(user.settings_json or {}),
    )


@router.patch("/me/settings", response_model=UserMeResponse)
def patch_my_settings(
    patch: dict[str, Any] = Body(default_factory=dict),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    base = dict(user.settings_json or {})
    for k, v in patch.items():
        if v is not None:
            base[k] = v
    user.settings_json = base
    db.flush()
    credits = user.credits_row
    bal = credits.balance_minutes if credits else 0
    is_paid = user_has_paid_plan(db, user.id)
    return UserMeResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        balance_minutes=bal,
        is_paid=is_paid,
        settings=dict(user.settings_json or {}),
    )
