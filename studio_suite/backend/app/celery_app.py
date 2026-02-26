"""
Konfiguracja Celery
"""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "studio_suite",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.processing", "app.tasks.monitoring", "app.tasks.bells"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Sprawdzanie wyĹ›wietlaczy offline - co minutÄ™
        "check-displays-offline": {
            "task": "app.tasks.monitoring.check_displays_offline",
            "schedule": 60.0,  # Co 60 sekund
        },
        # Sprawdzanie harmonogramu dzwonkĂłw - co minutÄ™
        "check-bells": {
            "task": "app.tasks.bells.check_and_play_bells",
            "schedule": 60.0,  # Co 60 sekund
        },
    },
)


