"""Coordinate provider, renderer, versions, and last-known-good fallback."""

from __future__ import annotations

from typing import Protocol

from cache import ArtifactCache, ScreenArtifact
from content import NormalizedContent, content_version


class ContentProvider(Protocol):
    def load(self) -> NormalizedContent: ...


class ContentRenderer(Protocol):
    def render(self, content: NormalizedContent) -> bytes: ...


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

    def current(self) -> ScreenArtifact:
        try:
            content = self.provider.load()
            version = content_version(content)
            cached = self.cache.get(version)
            if cached is not None:
                return cached
            artifact = ScreenArtifact(version=version, png=self.renderer.render(content))
            self.cache.put(artifact)
            return artifact
        except Exception:
            latest = self.cache.latest()
            if latest is not None:
                return latest
            raise DisplayUnavailable("No screen artifact is currently available") from None

    def for_version(self, version: str) -> ScreenArtifact:
        cached = self.cache.get(version)
        if cached is not None:
            return cached

        try:
            content = self.provider.load()
        except Exception:
            raise DisplayUnavailable("Screen content could not be loaded") from None

        if content_version(content) != version:
            raise StaleContentVersion("The requested screen version is no longer current")

        try:
            artifact = ScreenArtifact(version=version, png=self.renderer.render(content))
        except Exception:
            raise DisplayUnavailable("Screen content could not be rendered") from None
        self.cache.put(artifact)
        return artifact
