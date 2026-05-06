"""Auth API tests (Epic 3)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_register_weak_password_422():
    email = f"pwt{uuid.uuid4().hex[:6]}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "weakpass"})
    assert r.status_code == 422


def test_register_login_me_patch_settings(postgres_live):
    email = f"u{uuid.uuid4().hex[:10]}@example.com"
    password = "GoodPass1"

    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]
    assert r.cookies.get("refresh_token")

    r2 = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
    assert r2.status_code == 200
    assert r2.json()["balance_minutes"] == 10
    assert r2.json()["is_paid"] is False
    assert r2.json()["settings"] == {}

    r3 = client.patch(
        "/api/v1/users/me/settings",
        headers={"Authorization": f"Bearer {access}"},
        json={"dubTargetLang": "es", "dubMode": True},
    )
    assert r3.status_code == 200
    assert r3.json()["settings"]["dubTargetLang"] == "es"
    assert r3.json()["settings"]["dubMode"] is True

    bad = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass1"})
    assert bad.status_code == 401


def test_google_oauth_creates_user(postgres_live):
    sub = f"google-{uuid.uuid4().hex}"
    with patch("app.api.auth.fetch_google_userinfo", new_callable=AsyncMock) as m:
        m.return_value = {"sub": sub, "email": f"{sub}@gmail.com", "name": "Tester", "picture": "https://x/y"}
        r = client.post("/api/v1/auth/oauth/google", json={"access_token": "fake-google-access-token-xx"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["display_name"] == "Tester"


def test_refresh_cookie_rotation(postgres_live):
    email = f"rf{uuid.uuid4().hex[:8]}@example.com"
    password = "RefreshMe2"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200
    cookie = r.cookies.get("refresh_token")
    assert cookie

    r2 = client.post("/api/v1/auth/refresh", cookies={"refresh_token": cookie})
    assert r2.status_code == 200
    new_cookie = r2.cookies.get("refresh_token")
    assert new_cookie
    assert new_cookie != cookie
