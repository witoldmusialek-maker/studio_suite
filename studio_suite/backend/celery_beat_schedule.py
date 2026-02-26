"""
Konfiguracja Celery Beat - harmonogram zadań cyklicznych
"""
from celery.schedules import crontab

beat_schedule = {
    # Sprawdzanie wyświetlaczy offline - co minutę
    "check-displays-offline": {
        "task": "app.tasks.monitoring.check_displays_offline",
        "schedule": crontab(minute="*"),  # Co minutę
    },
    # Sprawdzanie harmonogramu dzwonków - co minutę
    "check-bells": {
        "task": "app.tasks.bells.check_and_play_bells",
        "schedule": crontab(minute="*"),  # Co minutę
    },
}



