from celery import Celery

from app.config import get_settings

_settings = get_settings()
_redis = _settings.redis_url

celery_app = Celery(
    "voice_pro",
    broker=_redis,
    backend=_redis,
    include=["app.tasks.ping"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
