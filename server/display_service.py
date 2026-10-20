"""Coordinate provider, renderer, versions, and last-known-good fallback."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Protocol

from cache import ArtifactCache, ScreenArtifact
from content import (
    NormalizedContent,
    battery_state,
    display_version,
    refresh_at_from_state,
    refresh_state,
)


class ContentProvider(Protocol):
    def load(self) -> NormalizedContent: ...


class ContentRenderer(Protocol):
    def render(
        self,
        content: NormalizedContent,
        battery_percent: int | None = None,
        *,
        refresh_at: datetime | None = None,
    ) -> bytes: ...


class DisplayUnavailable(RuntimeError):
    pass


class StaleContentVersion(RuntimeError):
    pass


class DisplayService:
    def __init__(
        self,
        provider: ContentProvider,
        renderer: ContentRenderer,
        cache: ArtifactCache,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.provider = provider
        self.renderer = renderer
        self.cache = cache
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def current(
        self, battery_percent: int | None = None, *, refresh_at: datetime | None = None
    ) -> ScreenArtifact:
        try:
            content = self.provider.load()
            response_time = refresh_at or self._clock()
            state = refresh_state(response_time)
            version = display_version(content, battery_percent, response_time)
            cached = self.cache.get(version)
            if cached is not None:
                return cached
            artifact = ScreenArtifact(
                version=version,
                png=self.renderer.render(content, battery_percent, refresh_at=response_time),
                battery_state=battery_state(battery_percent),
                refresh_state=state,
            )
            self.cache.put(artifact)
            return artifact
        except Exception:
            latest = self.cache.latest()
            if latest is not None:
                return latest
            raise DisplayUnavailable("No screen artifact is currently available") from None

    def for_version(
        self, version: str, battery_percent: int | None, refresh_display_state: str = "none"
    ) -> ScreenArtifact:
        cached = self.cache.get(version)
        if (
            cached is not None
            and cached.battery_state == battery_state(battery_percent)
            and cached.refresh_state == refresh_display_state
        ):
            return cached

        try:
            content = self.provider.load()
        except Exception:
            raise DisplayUnavailable("Screen content could not be loaded") from None

        try:
            refresh_at = refresh_at_from_state(refresh_display_state)
        except ValueError:
            raise StaleContentVersion("The requested refresh state is invalid") from None
        if display_version(content, battery_percent, refresh_at) != version:
            raise StaleContentVersion("The requested screen version is no longer current")

        try:
            artifact = ScreenArtifact(
                version=version,
                png=self.renderer.render(content, battery_percent, refresh_at=refresh_at),
                battery_state=battery_state(battery_percent),
                refresh_state=refresh_display_state,
            )
        except Exception:
            raise DisplayUnavailable("Screen content could not be rendered") from None
        self.cache.put(artifact)
        return artifact
