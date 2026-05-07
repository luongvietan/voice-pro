from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db_session
from app.security.tokens import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def get_user_from_bearer_allow_deleted(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db_session),
) -> User:
    """Validate access JWT and load user (including soft-deleted) — for idempotent DELETE /me."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    settings = get_settings()
    try:
        uid = decode_access_token(creds.credentials, settings)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None
    user = db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db_session),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    settings = get_settings()
    try:
        uid = decode_access_token(creds.credentials, settings)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None
    user = db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Account deleted")
    return user
