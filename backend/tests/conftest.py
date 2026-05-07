import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.redis_client import reset_redis_client_for_tests


@pytest.fixture(scope="session", autouse=True)
def _clear_rate_limit_keys_session():
    """Xóa bucket rate-limit cũ trong Redis để full suite không dính 429/block từ lần chạy trước."""
    try:
        import redis

        from app.config import get_settings

        r = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
        for key in r.scan_iter(match="vp:rl:*"):
            r.delete(key)
        r.close()
    except Exception:
        pass
    yield


@pytest.fixture(autouse=True)
def _reset_redis_singleton():
    """TestClient có thể đóng loop giữa các test — tránh giữ Redis async client cũ."""
    yield
    reset_redis_client_for_tests()


@pytest.fixture(autouse=True)
def _reset_rate_limit_fail_open_throttle():
    from app.middleware.rate_limit import reset_rate_limit_fail_open_log_throttle_for_tests

    reset_rate_limit_fail_open_log_throttle_for_tests()
    yield
    reset_rate_limit_fail_open_log_throttle_for_tests()


@pytest.fixture(scope="session")
def postgres_live():
    """Bỏ qua test cần DB khi PostgreSQL chưa chạy (vd. chưa `docker compose up postgres`)."""
    from app.db.session import get_engine

    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL không khả dụng: {exc}")
    return True
