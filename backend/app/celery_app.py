from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

_settings = get_settings()
_redis = _settings.redis_url

celery_app = Celery(
    "voice_pro",
    broker=_redis,
    backend=_redis,
    include=["app.tasks.ping", "app.tasks.transcribe", "app.tasks.synthesize", "app.tasks.credits_reset"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "reset-free-tier-monthly": {
            "task": "credits.reset_free_tier_monthly",
            "schedule": crontab(day_of_month=1, hour=0, minute=0),
        },
    },
)
