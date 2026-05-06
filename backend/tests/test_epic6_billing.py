"""Epic 6 — Stripe billing helpers và webhook payload."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings, get_settings
from app.services.stripe_billing import (
    apply_stripe_webhook_payload,
    map_stripe_subscription_status,
    upsert_subscription_from_stripe,
)
from app.services.subscription_util import (
    infer_plan_slug,
    paid_subscription_filter_clause,
    parse_paid_price_ids,
    subscription_counts_as_paid_row,
    user_has_paid_plan,
)


def test_parse_paid_price_ids():
    assert parse_paid_price_ids("price_a, price_b") == frozenset({"price_a", "price_b"})
    assert parse_paid_price_ids("") == frozenset()


def test_infer_plan_slug_basic_pro_and_list():
    s = Settings.model_construct(
        stripe_price_basic="pb",
        stripe_price_pro="pp",
        stripe_paid_price_ids="px,py",
    )
    assert infer_plan_slug("pb", s) == "basic"
    assert infer_plan_slug("pp", s) == "pro"
    assert infer_plan_slug("px", s) == "pro"
    assert infer_plan_slug("unknown", s) == "free"


def test_map_stripe_subscription_status():
    assert map_stripe_subscription_status("active") == "active"
    assert map_stripe_subscription_status("trialing") == "trialing"
    assert map_stripe_subscription_status("canceled") == "cancelled"


def test_subscription_counts_as_paid_row_legacy_slug(monkeypatch):
    from app.db.models import Subscription

    monkeypatch.setenv("STRIPE_PAID_PRICE_IDS", "")
    get_settings.cache_clear()
    sub = MagicMock(spec=Subscription)
    sub.status = "active"
    sub.stripe_price_id = None
    sub.plan = "basic"
    assert subscription_counts_as_paid_row(sub) is True


def test_subscription_counts_as_paid_row_price_id(monkeypatch):
    from app.db.models import Subscription

    monkeypatch.setenv("STRIPE_PAID_PRICE_IDS", "price_x")
    get_settings.cache_clear()
    sub = MagicMock(spec=Subscription)
    sub.status = "active"
    sub.stripe_price_id = "price_x"
    sub.plan = "free"
    assert subscription_counts_as_paid_row(sub) is True


@pytest.fixture
def settings_price():
    return Settings.model_construct(
        stripe_price_basic="pb",
        stripe_price_pro="pp",
        stripe_paid_price_ids="pp,p_other",
    )


def _mock_db_session():
    """SQLAlchemy 2: db.scalars(statement).first() — mock đủ chuỗi."""
    db = MagicMock()
    scalar_result = MagicMock()
    scalar_result.first.return_value = None
    db.scalars.return_value = scalar_result
    return db


def test_upsert_subscription_creates_row(settings_price):
    from app.db.models import Subscription, User

    uid = uuid.uuid4()
    user = User(id=uid, email="t@example.com", settings_json={})
    db = _mock_db_session()
    db.get.return_value = user

    stripe_sub = {
        "id": "sub_123",
        "customer": "cus_1",
        "status": "active",
        "metadata": {"user_id": str(uid)},
        "items": {"data": [{"price": {"id": "pp"}}]},
    }
    upsert_subscription_from_stripe(db, stripe_sub, settings_price)

    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert isinstance(added, Subscription)
    assert added.stripe_subscription_id == "sub_123"
    assert added.plan == "pro"
    assert added.stripe_price_id == "pp"


def test_apply_webhook_subscription_updated(settings_price):
    from app.db.models import User

    uid = uuid.uuid4()
    user = User(id=uid, email="t@example.com", settings_json={})
    db = _mock_db_session()
    db.get.return_value = user

    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_999",
                "customer": "cus_x",
                "status": "active",
                "metadata": {"user_id": str(uid)},
                "items": {"data": [{"price": {"id": "pp"}}]},
            }
        },
    }
    apply_stripe_webhook_payload(db, event, settings_price)
    db.add.assert_called_once()


@patch("app.services.stripe_billing.retrieve_subscription_dict")
def test_apply_webhook_checkout_completed(mock_retrieve, settings_price):
    from app.db.models import User

    uid = uuid.uuid4()
    user = User(id=uid, email="t@example.com", settings_json={})
    db = _mock_db_session()
    db.get.return_value = user

    mock_retrieve.return_value = {
        "id": "sub_chk",
        "customer": "cus_chk",
        "status": "active",
        "metadata": {"user_id": str(uid)},
        "items": {"data": [{"price": {"id": "pp"}}]},
    }

    settings_with_key = Settings.model_construct(
        stripe_api_key="sk_test_dummy",
        stripe_price_basic="pb",
        stripe_price_pro="pp",
        stripe_paid_price_ids="pp",
    )

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_chk",
                "subscription": "sub_chk",
                "metadata": {"user_id": str(uid)},
            }
        },
    }
    apply_stripe_webhook_payload(db, event, settings_with_key)
    mock_retrieve.assert_called_once_with("sub_chk", settings_with_key)
    db.add.assert_called_once()


# ── P6: Subscription cancellation → user_has_paid_plan = False ──────────────

def test_upsert_subscription_cancellation_clears_plan(settings_price):
    """Khi subscription bị cancel, plan phải về free và price_id về None."""
    from app.db.models import User

    uid = uuid.uuid4()
    user = User(id=uid, email="t@example.com", settings_json={})
    db = _mock_db_session()
    db.get.return_value = user

    stripe_sub = {
        "id": "sub_cancel",
        "customer": "cus_1",
        "status": "canceled",
        "metadata": {"user_id": str(uid)},
        "items": {"data": [{"price": {"id": "pp"}}]},
    }
    upsert_subscription_from_stripe(db, stripe_sub, settings_price)

    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert added.plan == "free"
    assert added.stripe_price_id is None
    assert added.status == "cancelled"


def test_upsert_subscription_paused_clears_plan(settings_price):
    """Khi subscription bị paused, plan phải về free (P2 patch)."""
    from app.db.models import User

    uid = uuid.uuid4()
    user = User(id=uid, email="t@example.com", settings_json={})
    db = _mock_db_session()
    db.get.return_value = user

    stripe_sub = {
        "id": "sub_paused",
        "customer": "cus_1",
        "status": "paused",
        "metadata": {"user_id": str(uid)},
        "items": {"data": [{"price": {"id": "pp"}}]},
    }
    upsert_subscription_from_stripe(db, stripe_sub, settings_price)

    db.add.assert_called_once()
    added = db.add.call_args[0][0]
    assert added.plan == "free"
    assert added.stripe_price_id is None


def test_user_has_paid_plan_returns_false_after_cancel(monkeypatch):
    """user_has_paid_plan = False khi subscription không còn active."""
    from sqlalchemy.orm import Session

    monkeypatch.setenv("STRIPE_PAID_PRICE_IDS", "price_pro")
    get_settings.cache_clear()

    uid = uuid.uuid4()
    db = MagicMock(spec=Session)
    db.execute.return_value.first.return_value = None

    assert user_has_paid_plan(db, uid) is False


# ── P7: Idempotency duplicate event short-circuit ───────────────────────────

def test_webhook_duplicate_event_is_skipped():
    """Khi rowcount == 0 (event đã thấy), apply_stripe_webhook_payload không được gọi."""
    from fastapi.testclient import TestClient
    from unittest.mock import patch as mock_patch
    from main import app
    from app.db.session import get_db_session

    db = MagicMock()
    result_mock = MagicMock()
    result_mock.rowcount = 0
    db.execute.return_value = result_mock

    def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db
    try:
        with mock_patch("app.api.billing.stripe") as mock_stripe, \
             mock_patch("app.api.billing.apply_stripe_webhook_payload") as mock_apply, \
             mock_patch("app.api.billing.get_settings") as mock_settings:

            mock_event = MagicMock()
            mock_event.get.side_effect = lambda k, *a: {
                "id": "evt_dup_001", "type": "customer.subscription.updated"
            }.get(k, *a)
            mock_stripe.Webhook.construct_event.return_value = mock_event
            mock_settings.return_value.stripe_webhook_secret = "whsec_test"

            client = TestClient(app)
            client.post(
                "/api/v1/billing/stripe/webhook",
                content=b"payload",
                headers={"stripe-signature": "t=1,v1=abc"},
            )
            mock_apply.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_db_session, None)


# ── P9: paid_subscription_filter_clause SQL logic ────────────────────────────

def test_paid_subscription_filter_clause_with_price_ids(monkeypatch):
    """Khi STRIPE_PAID_PRICE_IDS được set, clause dùng price_id IN (...)."""
    from sqlalchemy import String
    from sqlalchemy.sql import column

    monkeypatch.setenv("STRIPE_PAID_PRICE_IDS", "price_pro,price_basic")
    get_settings.cache_clear()

    clause = paid_subscription_filter_clause()
    compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))

    assert "price_pro" in compiled or "stripe_price_id" in compiled
    assert "active" in compiled or "trialing" in compiled


def test_paid_subscription_filter_clause_legacy_only(monkeypatch):
    """Khi STRIPE_PAID_PRICE_IDS trống, clause chỉ dùng legacy plan slug."""
    monkeypatch.setenv("STRIPE_PAID_PRICE_IDS", "")
    get_settings.cache_clear()

    clause = paid_subscription_filter_clause()
    compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))

    assert "basic" in compiled or "pro" in compiled


# ── P11: StripeError error paths in checkout/portal endpoints ────────────────

@patch("app.api.billing.create_checkout_session")
def test_checkout_session_stripe_error_returns_502(mock_create):
    """StripeError during checkout → HTTP 502 with safe message."""
    from stripe._error import StripeError
    from fastapi.testclient import TestClient
    from main import app
    from app.deps.auth import get_current_user
    from app.db.models import User as UserModel

    mock_create.side_effect = StripeError("card_declined")
    fake_user = UserModel(id=uuid.uuid4(), email="u@test.com", settings_json={})
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        client = TestClient(app)
        response = client.post("/api/v1/billing/stripe/checkout-session")
        assert response.status_code == 502
        assert "card_declined" not in response.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@patch("app.api.billing.create_portal_session")
def test_portal_session_stripe_error_returns_502(mock_create):
    """StripeError during portal → HTTP 502 with safe message."""
    from stripe._error import StripeError
    from fastapi.testclient import TestClient
    from main import app
    from app.deps.auth import get_current_user
    from app.db.models import User as UserModel

    mock_create.side_effect = StripeError("portal_error")
    fake_user = UserModel(id=uuid.uuid4(), email="u@test.com", settings_json={})
    app.dependency_overrides[get_current_user] = lambda: fake_user
    try:
        client = TestClient(app)
        response = client.post("/api/v1/billing/stripe/portal-session")
        assert response.status_code == 502
        assert "portal_error" not in response.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)