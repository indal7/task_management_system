# app/utils/timezone_utils.py
"""
Timezone utilities for IST (Indian Standard Time, UTC+5:30) serialization.

Strategy:
  - Datetimes are stored as naive UTC in the database.
  - All API responses serialize datetimes in IST with explicit +05:30 offset so
    clients always know the exact local time.
"""
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def ist_isoformat(dt):
    """
    Serialize a datetime to an IST ISO-8601 string (e.g. 2026-03-18T11:17:45+05:30).
    Naive datetimes are assumed to be UTC and converted to IST.
    Returns None if dt is None.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()


def now_ist_isoformat():
    """Return the current datetime as an IST ISO-8601 string."""
    return datetime.now(timezone.utc).astimezone(IST).isoformat()
