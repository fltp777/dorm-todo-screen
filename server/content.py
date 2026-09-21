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

    def __post_init__(self) -> None:
        if not self.type:
            raise ValueError("Content type is required")
        if not isinstance(self.body, str):
            raise TypeError("Content body must be a string")
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


def display_version(content: NormalizedContent, battery_percent: int | None) -> str:
    """Version the rendered artifact by both content and request-only battery state."""
    source = f"{content_version(content)}\0{battery_state(battery_percent)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
