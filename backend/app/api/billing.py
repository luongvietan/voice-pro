"""Billing / Stripe — webhook (không JWT), Checkout & Portal (JWT)."""

from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from stripe._error import StripeError
from stripe._webhook import SignatureVerificationError

from app.config import get_settings
from app.db.models import StripeWebhookEvent, User
from app.db.session import get_db_session
from app.deps.auth import get_current_user
from app.services.stripe_billing import (
    apply_stripe_webhook_payload,
    create_checkout_session,
    create_portal_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing")


class CheckoutUrlResponse(BaseModel):
    url: str


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db_session)) -> Response:
    settings = get_settings()
    secret = settings.stripe_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="Thanh toán chưa được cấu hình")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Thiếu chữ ký Stripe")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Payload không hợp lệ") from exc
    except SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Chữ ký webhook không hợp lệ") from exc

    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="Event không có id")

    stmt = insert(StripeWebhookEvent).values(event_id=event_id).on_conflict_do_nothing()
    result = db.execute(stmt)
    if result.rowcount == 0:
        return Response(status_code=200)

    try:
        apply_stripe_webhook_payload(db, event, settings)
    except Exception:
        logger.exception("stripe webhook processing failed event_id=%s", event_id)
        raise HTTPException(status_code=500, detail="Xử lý webhook thất bại") from None

    return Response(status_code=200)


@router.post("/stripe/checkout-session", response_model=CheckoutUrlResponse)
def stripe_checkout_session(user: User = Depends(get_current_user)):
    settings = get_settings()
    try:
        url = create_checkout_session(user, settings)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Thanh toán chưa được cấu hình đầy đủ") from exc
    except StripeError as exc:
        logger.warning("Stripe checkout error: %s", getattr(exc, "user_message", None) or str(exc))
        raise HTTPException(
            status_code=502,
            detail="Không thể mở thanh toán. Thử lại sau hoặc liên hệ hỗ trợ.",
        ) from exc
    except RuntimeError as exc:
        logger.warning("Stripe checkout runtime error: %s", exc)
        raise HTTPException(status_code=503, detail="Thanh toán chưa được cấu hình đầy đủ") from exc
    return CheckoutUrlResponse(url=url)


@router.post("/stripe/portal-session", response_model=CheckoutUrlResponse)
def stripe_portal_session(user: User = Depends(get_current_user)):
    settings = get_settings()
    try:
        url = create_portal_session(user, settings)
    except RuntimeError as exc:
        if str(exc) == "no_customer":
            raise HTTPException(
                status_code=400,
                detail="Chưa có tài khoản thanh toán Stripe. Dùng Upgrade để đăng ký gói trước.",
            ) from exc
        logger.warning("Stripe portal runtime error: %s", exc)
        raise HTTPException(status_code=503, detail="Cổng quản lý gói chưa được cấu hình đầy đủ") from exc
    except StripeError as exc:
        logger.warning("Stripe portal error: %s", getattr(exc, "user_message", None) or str(exc))
        raise HTTPException(
            status_code=502,
            detail="Không thể mở cổng quản lý gói. Thử lại sau.",
        ) from exc
    return CheckoutUrlResponse(url=url)
