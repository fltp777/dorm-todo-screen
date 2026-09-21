"""Coordinate provider, renderer, versions, and last-known-good fallback."""

from __future__ import annotations

from typing import Protocol

from cache import ArtifactCache, ScreenArtifact
from content import NormalizedContent, battery_state, display_version


class ContentProvider(Protocol):
    def load(self) -> NormalizedContent: ...


class ContentRenderer(Protocol):
    def render(self, content: NormalizedContent, battery_percent: int | None = None) -> bytes: ...


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
    ) -> None:
        self.provider = provider
        self.renderer = renderer
        self.cache = cache

    def current(self, battery_percent: int | None = None) -> ScreenArtifact:
        try:
            content = self.provider.load()
            version = display_version(content, battery_percent)
            cached = self.cache.get(version)
            if cached is not None:
                return cached
            artifact = ScreenArtifact(
                version=version,
                png=self.renderer.render(content, battery_percent),
                battery_state=battery_state(battery_percent),
            )
            self.cache.put(artifact)
            return artifact
        except Exception:
            latest = self.cache.latest()
            if latest is not None:
                return latest
            raise DisplayUnavailable("No screen artifact is currently available") from None

    def for_version(self, version: str, battery_percent: int | None) -> ScreenArtifact:
        cached = self.cache.get(version)
        if cached is not None and cached.battery_state == battery_state(battery_percent):
            return cached

        try:
            content = self.provider.load()
        except Exception:
            raise DisplayUnavailable("Screen content could not be loaded") from None

        if display_version(content, battery_percent) != version:
            raise StaleContentVersion("The requested screen version is no longer current")

        try:
            artifact = ScreenArtifact(
                version=version,
                png=self.renderer.render(content, battery_percent),
                battery_state=battery_state(battery_percent),
            )
        except Exception:
            raise DisplayUnavailable("Screen content could not be rendered") from None
        self.cache.put(artifact)
        return artifact
