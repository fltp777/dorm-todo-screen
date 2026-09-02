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
