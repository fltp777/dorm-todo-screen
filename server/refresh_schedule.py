"""Business-time refresh scheduling for the Nook's next deep sleep."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from math import ceil


# China Standard Time is UTC+8 with no daylight-saving transition relevant to
# this device schedule.  An explicit offset avoids relying on Windows/Render
# tzdata availability while keeping the business timezone deterministic.
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")
DAY_START = time(hour=7, minute=10)
NIGHT_START = time(hour=22, minute=40)


def compute_refresh_rate(now: datetime, daytime_refresh_seconds: int) -> int:
    """Return the next Nook refresh delay from a timezone-aware instant.

    The normal daytime window is ``[07:10, 22:40)`` in Asia/Shanghai. At
    night, the caller sleeps exactly until the next local 07:10 rather than a
    fixed number of hours, so late manual requests still wake at the intended
    morning boundary.
    """
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    if daytime_refresh_seconds <= 0:
        raise ValueError("daytime_refresh_seconds must be positive")

    local_now = now.astimezone(SHANGHAI)
    local_clock = local_now.time()
    if DAY_START <= local_clock < NIGHT_START:
        return daytime_refresh_seconds

    target_date = local_now.date()
    if local_clock >= NIGHT_START:
        target_date += timedelta(days=1)
    target = datetime.combine(target_date, DAY_START, tzinfo=SHANGHAI)
    seconds_until_target = ceil((target - local_now).total_seconds())
    if seconds_until_target <= 0:
        raise RuntimeError("next morning refresh must be in the future")
    return seconds_until_target
