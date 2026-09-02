"""Stage 2B-2: Supabase todo -> signed Nook screen image."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes import router
from cache import ArtifactCache
from config import Settings
from display_service import ContentProvider, ContentRenderer, DisplayService
from providers.todo import TodoProvider
from renderer.todo import TodoRenderer
from security.signed_url import SignedImageURL


def create_app(
    settings: Settings | None = None,
    *,
    provider: ContentProvider | None = None,
    renderer: ContentRenderer | None = None,
    cache: ArtifactCache | None = None,
    signer: SignedImageURL | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    resolved_provider = provider or TodoProvider(
        resolved_settings.supabase_url,
        resolved_settings.supabase_secret_key,
    )
    resolved_renderer = renderer or TodoRenderer()
    resolved_cache = cache if cache is not None else ArtifactCache(max_versions=2)
    resolved_signer = signer or SignedImageURL(
        resolved_settings.screen_signing_secret,
        resolved_settings.screen_url_ttl_seconds,
    )

    application = FastAPI(title="Dorm Screen BYOS", version="2B-2")
    application.state.settings = resolved_settings
    application.state.display_service = DisplayService(
        resolved_provider,
        resolved_renderer,
        resolved_cache,
    )
    application.state.image_signer = resolved_signer
    application.include_router(router)
    return application


app = create_app()
