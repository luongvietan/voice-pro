import pytest

from app.celery_app import celery_app


@pytest.fixture(scope="session", autouse=True)
def _celery_eager():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
