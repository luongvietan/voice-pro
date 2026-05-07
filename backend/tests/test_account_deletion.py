"""Epic 7 — account soft delete API."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_delete_me_soft_delete_revokes_access_and_refresh(postgres_live):
    email = f"del{uuid.uuid4().hex[:10]}@example.com"
    password = "GoodPass1"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]
    cookie = r.cookies.get("refresh_token")
    assert cookie

    d = client.delete("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
    assert d.status_code == 204
    assert d.text == ""

    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 401

    rf = client.post("/api/v1/auth/refresh", cookies={"refresh_token": cookie})
    assert rf.status_code == 401

    d2 = client.delete("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
    assert d2.status_code == 204


def test_register_same_email_after_soft_delete(postgres_live):
    email = f"reuse{uuid.uuid4().hex[:8]}@example.com"
    password = "GoodPass1"
    r1 = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r1.status_code == 200
    access = r1.json()["access_token"]
    assert client.delete("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"}).status_code == 204

    r2 = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r2.status_code == 200, r2.text
