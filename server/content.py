"""Provider-neutral content passed into screen renderers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class NormalizedContent:
    type: str
    body: str
    updated_at: datetime
    daily_reminder_text: str = ""
    yijing_position: int = 0

    def __post_init__(self) -> None:
        if not self.type:
            raise ValueError("Content type is required")
        if not isinstance(self.body, str):
            raise TypeError("Content body must be a string")
        if not isinstance(self.daily_reminder_text, str):
            raise TypeError("Daily reminder text must be a string")
        if isinstance(self.yijing_position, bool) or not isinstance(self.yijing_position, int):
            raise TypeError("Yijing position must be an integer")
        if self.yijing_position < 0:
            raise ValueError("Yijing position must not be negative")
        if self.updated_at.tzinfo is None:
            raise ValueError("updated_at must include a timezone")


def normalize_body(body: str) -> str:
    """Preserve user text while making newline handling deterministic."""
    return body.replace("\r\n", "\n").replace("\r", "\n")


def normalized_updated_at(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def content_version(content: NormalizedContent) -> str:
    """Derive a URL-safe version from the authoritative database timestamp."""
    timestamp = normalized_updated_at(content.updated_at)
    return hashlib.sha256(timestamp.encode("utf-8")).hexdigest()[:20]


def battery_state(battery_percent: int | None) -> str:
    """Encode request-only battery state without putting it in user content."""
    if battery_percent is None:
        return "none"
    if isinstance(battery_percent, bool) or not isinstance(battery_percent, int):
        raise ValueError("Battery percentage must be an integer or None")
    if not 0 <= battery_percent <= 100:
        raise ValueError("Battery percentage must be between 0 and 100")
    return str(battery_percent)


def battery_percent_from_state(state: str) -> int | None:
    """Decode the stable battery state carried by a signed image URL."""
    if state == "none":
        return None
    if not state.isascii() or not state.isdigit():
        raise ValueError("Battery state is invalid")
    value = int(state)
    if not 0 <= value <= 100 or str(value) != state:
        raise ValueError("Battery state is invalid")
    return value


def refresh_state(refresh_at: datetime | None) -> str:
    """Encode the successful display response minute for a reproducible footer."""
    if refresh_at is None:
        return "none"
    if refresh_at.tzinfo is None:
        raise ValueError("Refresh timestamp must include a timezone")
    return str(int(refresh_at.astimezone(timezone.utc).timestamp()) // 60)


def refresh_at_from_state(state: str) -> datetime | None:
    """Decode a signed UTC minute without trusting a free-form timestamp."""
    if state == "none":
        return None
    if not state.isascii() or not state.isdigit():
        raise ValueError("Refresh state is invalid")
    minute = int(state)
    if minute < 0 or str(minute) != state:
        raise ValueError("Refresh state is invalid")
    return datetime.fromtimestamp(minute * 60, tz=timezone.utc)


def display_version(
    content: NormalizedContent,
    battery_percent: int | None,
    refresh_at: datetime | None = None,
) -> str:
    """Version content, battery, and the server-confirmed refresh display minute."""
    source = f"{content_version(content)}\0{battery_state(battery_percent)}\0{refresh_state(refresh_at)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
