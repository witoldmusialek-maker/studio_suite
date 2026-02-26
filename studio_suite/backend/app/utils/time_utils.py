"""
Timezone-aware helpers for schedule calculations.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


def local_now() -> datetime:
    """
    Return current datetime in configured app timezone as naive local datetime.
    We keep naive values because DB models currently use naive date/time fields.
    """
    tz_now = datetime.now(ZoneInfo(settings.APP_TIMEZONE))
    return tz_now.replace(tzinfo=None)
