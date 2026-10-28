"""Deterministic posting slots per platform (local time), spread across days."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# (hour, minute, allowed weekdays Mon=0) - sensible defaults, tune with real analytics later.
SLOTS = {
    "instagram": (20, 0, range(7)),
    "tiktok": (21, 0, range(7)),
    "youtube": (18, 0, range(7)),
    "facebook": (19, 30, range(7)),
    "linkedin": (9, 0, (1, 2, 3)),
    "x": (12, 30, range(7)),
}


def slot_for(platform, index, tz, now=None):
    """index = clip number; each clip lands on the next free allowed day."""
    zone = ZoneInfo(tz)
    now = now or datetime.now(zone)
    hour, minute, days = SLOTS[platform]
    day, found = now.date(), -1
    for _ in range(366):
        cand = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
        if cand > now + timedelta(minutes=30) and cand.weekday() in days:
            found += 1
            if found == index:
                return cand
        day += timedelta(days=1)
    raise RuntimeError("no slot")
