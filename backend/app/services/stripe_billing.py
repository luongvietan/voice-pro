"""Stripe Checkout, Billing Portal, và đồng bộ subscription từ webhook."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import Subscription, User
from app.services.subscription_util import infer_plan_slug

logger = logging.getLogger(__name__)


def map_stripe_subscription_status(stripe_status: str | None) -> str:
    if stripe_status in ("active",):
        return "active"
    if stripe_status == "trialing":
        return "trialing"
    if stripe_status == "past_due":
        return "past_due"
    if stripe_status in ("canceled", "unpaid", "incomplete_expired", "incomplete", "paused"):
        return "cancelled"
    return "cancelled"


def _extract_price_id(subscription_obj: dict[str, Any]) -> str | None:
    items = subscription_obj.get("items") or {}
    data = items.get("data") or []
    if not data:
        return None
    price = (data[0] or {}).get("price") or {}
    return price.get("id")


def _resolve_user_for_subscription(
    db: Session,
    customer_id: str | None,
    subscription_metadata: dict[str, Any] | None,
) -> User | None:
    meta = subscription_metadata or {}
    uid_str = meta.get("user_id")
    if uid_str:
        try:
            uid = uuid.UUID(str(uid_str))
        except (ValueError, AttributeError):
            uid = None
        else:
            user = db.get(User, uid)
            if user:
                return user
    if customer_id:
        row = db.scalars(select(User).where(User.stripe_customer_id == customer_id)).first()
        if row:
            return row
    return None


def _ensure_user_customer(db: Session, user: User, customer_id: str) -> None:
    if user.stripe_customer_id != customer_id:
        user.stripe_customer_id = customer_id
        db.flush()


def upsert_subscription_from_stripe(
    db: Session,
    stripe_sub: dict[str, Any],
    settings: Settings,
    *,
    user_hint: User | None = None,
) -> None:
    """Cập nhật hoặc tạo bản ghi Subscription theo payload Stripe Subscription."""
    customer_id = stripe_sub.get("customer")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    sub_id = stripe_sub.get("id")
    if not sub_id:
        return

    meta = stripe_sub.get("metadata") or {}
    user = user_hint or _resolve_user_for_subscription(db, str(customer_id) if customer_id else None, meta)
    if user is None:
        logger.warning("stripe subscription %s: không map được user", sub_id)
        return

    if customer_id:
        _ensure_user_customer(db, user, str(customer_id))

    status = map_stripe_subscription_status(stripe_sub.get("status"))
    price_id = _extract_price_id(stripe_sub)
    plan = infer_plan_slug(price_id, settings)

    if status == "cancelled" or stripe_sub.get("status") in (
        "canceled",
        "unpaid",
        "incomplete_expired",
        "paused",
    ):
        plan = "free"
        price_id = None

    existing = db.scalars(select(Subscription).where(Subscription.stripe_subscription_id == sub_id)).first()

    cust_str = str(customer_id) if customer_id else None

    if existing:
        existing.user_id = user.id
        existing.plan = plan
        existing.status = status
        existing.stripe_customer_id = cust_str or existing.stripe_customer_id
        existing.stripe_subscription_id = sub_id
        existing.stripe_price_id = price_id
    else:
        db.add(
            Subscription(
                user_id=user.id,
                plan=plan,
                stripe_customer_id=cust_str,
                stripe_subscription_id=sub_id,
                stripe_price_id=price_id,
                status=status,
            )
        )


def retrieve_subscription_dict(subscription_id: str, settings: Settings) -> dict[str, Any]:
    if not settings.stripe_api_key:
        raise RuntimeError("STRIPE_API_KEY not configured")
    stripe.api_key = settings.stripe_api_key
    sub = stripe.Subscription.retrieve(subscription_id)
    if isinstance(sub, dict):
        return sub
    to_dict = getattr(sub, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return dict(sub)


def create_checkout_session(user: User, settings: Settings) -> str:
    if not settings.stripe_api_key:
        raise RuntimeError("STRIPE_API_KEY not configured")
    price_id = settings.resolve_default_checkout_price_id()
    stripe.api_key = settings.stripe_api_key

    params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": settings.stripe_success_url + "&session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": settings.stripe_cancel_url,
        "metadata": {"user_id": str(user.id)},
        "subscription_data": {"metadata": {"user_id": str(user.id)}},
    }
    if user.stripe_customer_id:
        params["customer"] = user.stripe_customer_id
    elif user.email:
        params["customer_email"] = user.email

    session = stripe.checkout.Session.create(**params)
    url = session.get("url") if isinstance(session, dict) else session.url
    if not url:
        raise RuntimeError("Stripe Checkout không trả URL")
    return url


def create_portal_session(user: User, settings: Settings) -> str:
    if not settings.stripe_api_key:
        raise RuntimeError("STRIPE_API_KEY not configured")
    if not user.stripe_customer_id:
        raise RuntimeError("no_customer")
    stripe.api_key = settings.stripe_api_key
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=settings.stripe_success_url,
    )
    url = session.get("url") if isinstance(session, dict) else session.url
    if not url:
        raise RuntimeError("Stripe Portal không trả URL")
    return url


def apply_stripe_webhook_payload(db: Session, event: dict[str, Any], settings: Settings) -> None:
    etype = event.get("type", "")
    data = event.get("data") or {}
    obj = data.get("object") or {}
    if not etype:
        return

    if etype == "checkout.session.completed":
        customer = obj.get("customer")
        metadata = obj.get("metadata") or {}
        uid_str = metadata.get("user_id")
        user: User | None = None
        if uid_str:
            try:
                user = db.get(User, uuid.UUID(str(uid_str)))
            except ValueError:
                user = None
        if user and customer:
            _ensure_user_customer(db, user, str(customer))
        sub_ref = obj.get("subscription")
        if sub_ref and settings.stripe_api_key:
            sub_ref_id = sub_ref.get("id") if isinstance(sub_ref, dict) else str(sub_ref)
            sub_dict = retrieve_subscription_dict(sub_ref_id, settings)
            upsert_subscription_from_stripe(db, sub_dict, settings, user_hint=user)
        return

    if etype.startswith("customer.subscription."):
        upsert_subscription_from_stripe(db, obj, settings)
        return
