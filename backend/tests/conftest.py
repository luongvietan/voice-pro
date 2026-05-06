import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.redis_client import reset_redis_client_for_tests


@pytest.fixture(autouse=True)
def _reset_redis_singleton():
    """TestClient có thể đóng loop giữa các test — tránh giữ Redis async client cũ."""
    yield
    reset_redis_client_for_tests()


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
