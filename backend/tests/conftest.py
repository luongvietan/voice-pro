import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


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
