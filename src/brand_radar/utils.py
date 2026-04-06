from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


def stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def within_days(dt: datetime | None, days: int) -> bool:
    if dt is None:
        return False
    return dt >= datetime.utcnow() - timedelta(days=days)
