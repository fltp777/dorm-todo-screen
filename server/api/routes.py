"""Minimal endpoints used by TRMNL Nook client v0.16.0."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import FileResponse

from config import Settings, normalize_device_id

router = APIRouter()
TEST_IMAGE_PATH = Path(__file__).resolve().parent.parent / "static" / "test-screen.png"


def _get_settings(request: Request) -> Settings:
    configured_settings = getattr(request.app.state, "settings", None)
    return configured_settings or Settings.from_env()


def _require_device(
    request: Request,
    device_id: str | None = Header(default=None, alias="ID"),
    access_token: str | None = Header(default=None, alias="access-token"),
) -> Settings:
    settings = _get_settings(request)
    if not settings.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server device credentials are not configured",
        )

    supplied_id = normalize_device_id(device_id or "")
    expected_id = normalize_device_id(settings.device_id)
    valid_id = secrets.compare_digest(supplied_id, expected_id)
    valid_key = secrets.compare_digest(access_token or "", settings.api_key)
    if not (valid_id and valid_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device credentials",
        )

    return settings


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/display")
def display(
    request: Request,
    settings: Settings = Depends(_require_device),
) -> dict[str, object]:
    # The Nook app normalizes its configured base URL to /api, then appends /display.
    base_url = settings.public_base_url or str(request.base_url).rstrip("/")
    return {
        "status": 0,
        "image_url": f"{base_url}/screen/test.png",
        "filename": "test-screen.png",
        "refresh_rate": settings.refresh_rate_seconds,
    }


@router.get("/screen/test.png", name="test_screen")
def test_screen() -> FileResponse:
    # v0.16.0 does not forward API auth headers when it downloads image_url.
    return FileResponse(
        TEST_IMAGE_PATH,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )
