"""Epic 9.3 — fail-open rate limit logging."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from main import app


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)


def test_fail_open_logs_when_redis_unavailable(api_client: TestClient, caplog: pytest.LogCaptureFixture, postgres_live) -> None:
    caplog.set_level(logging.ERROR)
    jid = "00000000-0000-0000-0000-000000000000"
    with patch("app.middleware.rate_limit.get_redis", new_callable=AsyncMock, return_value=None):
        r = api_client.get(f"/api/v1/jobs/{jid}")
    assert r.status_code == 404
    assert any(
        "[rate_limit] redis_unavailable_fail_open get_redis_returned_none" in rec.message
        for rec in caplog.records
        if rec.levelno == logging.ERROR
    )


def test_fail_open_error_throttled_per_process(api_client: TestClient, caplog: pytest.LogCaptureFixture, postgres_live) -> None:
    caplog.set_level(logging.ERROR)
    jid = "00000000-0000-0000-0000-000000000000"
    with patch("app.middleware.rate_limit.get_redis", new_callable=AsyncMock, return_value=None):
        api_client.get(f"/api/v1/jobs/{jid}")
        api_client.get(f"/api/v1/jobs/{jid}")
    errors = [rec for rec in caplog.records if rec.levelno == logging.ERROR]
    assert len(errors) == 1
