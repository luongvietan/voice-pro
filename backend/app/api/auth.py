"""Auth: Google OAuth (extension), email/password (dashboard), refresh."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import RefreshToken, User
from app.db.session import get_db_session
from app.schemas.auth import (
    GoogleOAuthRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserSummary,
)
from app.security.passwords import hash_password, verify_password
from app.security.tokens import hash_refresh_token
from app.services.auth_bootstrap import build_token_response, revoke_refresh_by_raw
from app.services.google_oauth import fetch_google_userinfo

router = APIRouter(prefix="/auth")


def _cookie_args(settings):
    return {
        "key": settings.refresh_cookie_name,
        "httponly": True,
        "secure": settings.environment == "production",
        "samesite": "lax",
        "max_age": settings.jwt_refresh_expire_days * 86400,
        "path": "/",
    }


def _expired(row: RefreshToken) -> bool:
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    return exp < datetime.now(tz=UTC)


@router.post("/oauth/google", response_model=TokenResponse)
def oauth_google(body: GoogleOAuthRequest, db: Session = Depends(get_db_session)):
    settings = get_settings()
    try:
        info = fetch_google_userinfo(body.access_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Google token") from exc

    sub = info.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Google profile missing sub")

    user = db.query(User).filter(User.google_sub == sub).one_or_none()
    email = info.get("email")
    if user is None:
        user = User(
            google_sub=sub,
            email=email,
            display_name=info.get("name"),
            avatar_url=info.get("picture"),
            settings_json={},
        )
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            user = db.query(User).filter(User.google_sub == sub).one()
    else:
        if email and user.email != email:
            user.email = email
        user.display_name = info.get("name") or user.display_name
        user.avatar_url = info.get("picture") or user.avatar_url

    access, refresh_raw, payload = build_token_response(db, user, settings)
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_raw,
        user=UserSummary(**payload),
    )


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db_session)):
    settings = get_settings()
    normalized = body.email.strip().lower()
    exists = db.query(User).filter(User.email == normalized).one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=normalized,
        password_hash=hash_password(body.password),
        settings_json={},
    )
    db.add(user)
    db.flush()

    access, refresh_raw, payload = build_token_response(db, user, settings)
    response.set_cookie(value=refresh_raw, **_cookie_args(settings))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=None, user=UserSummary(**payload))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db_session)):
    settings = get_settings()
    normalized = body.email.strip().lower()
    user = db.query(User).filter(User.email == normalized).one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access, refresh_raw, payload = build_token_response(db, user, settings)
    response.set_cookie(value=refresh_raw, **_cookie_args(settings))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=None, user=UserSummary(**payload))


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    db: Session = Depends(get_db_session),
):
    settings = get_settings()
    raw = request.cookies.get(settings.refresh_cookie_name)
    from_body = body.refresh_token if body else None
    use_extension_flow = bool(from_body)
    if not raw and from_body:
        raw = from_body
    if not raw:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    h = hash_refresh_token(raw)
    row = db.query(RefreshToken).filter(RefreshToken.token_hash == h).one_or_none()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if _expired(row):
        db.delete(row)
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = row.user
    db.delete(row)
    db.flush()

    access, refresh_raw, payload = build_token_response(db, user, settings)

    if use_extension_flow:
        db.commit()
        return TokenResponse(
            access_token=access,
            refresh_token=refresh_raw,
            user=UserSummary(**payload),
        )

    response.set_cookie(value=refresh_raw, **_cookie_args(settings))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=None, user=UserSummary(**payload))


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    body: RefreshRequest | None = None,
    db: Session = Depends(get_db_session),
):
    settings = get_settings()
    raw = request.cookies.get(settings.refresh_cookie_name)
    if not raw and body and body.refresh_token:
        raw = body.refresh_token
    revoke_refresh_by_raw(db, raw)
    response.delete_cookie(settings.refresh_cookie_name, path="/")
    db.commit()
    return {"ok": True}
