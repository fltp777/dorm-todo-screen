"""Stage 2B-1: Nook -> BYOS API -> fixed calibration image."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes import router
from config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    application = FastAPI(title="Dorm Screen BYOS", version="2B-1")
    application.state.settings = settings
    application.include_router(router)
    return application


app = create_app()
