"""Minimal endpoints used by TRMNL Nook client v0.16.0."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import FileResponse

from config import Settings, normalize_device_id
from display_service import DisplayService, DisplayUnavailable, StaleContentVersion
from security.signed_url import SignedImageURL

router = APIRouter()
TEST_IMAGE_PATH = Path(__file__).resolve().parent.parent / "static" / "test-screen.png"


def _get_settings(request: Request) -> Settings:
    configured_settings = getattr(request.app.state, "settings", None)
    return configured_settings or Settings.from_env()


def _get_display_service(request: Request) -> DisplayService:
    return request.app.state.display_service


def _get_image_signer(request: Request) -> SignedImageURL:
    return request.app.state.image_signer


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
    if not settings.content_is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dynamic screen content is not configured",
        )

    try:
        artifact = _get_display_service(request).current()
        signed_path = _get_image_signer(request).signed_path(artifact.version)
    except (DisplayUnavailable, ValueError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Screen content is temporarily unavailable",
        ) from None

    base_url = settings.public_base_url or str(request.base_url).rstrip("/")
    return {
        "status": 0,
        "image_url": f"{base_url}{signed_path}",
        "filename": f"todo-{artifact.version}.png",
        "refresh_rate": settings.refresh_rate_seconds,
    }


@router.get("/screen/current.png", name="current_screen")
def current_screen(
    request: Request,
    v: str | None = None,
    exp: str | None = None,
    sig: str | None = None,
) -> Response:
    signer = _get_image_signer(request)
    if not signer.verify(v, exp, sig):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired image URL",
        )

    try:
        artifact = _get_display_service(request).for_version(v or "")
    except StaleContentVersion:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Screen image version is no longer current",
        ) from None
    except DisplayUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Screen image is temporarily unavailable",
        ) from None

    return Response(
        content=artifact.png,
        media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )


@router.get("/screen/test.png", name="test_screen")
def test_screen() -> FileResponse:
    # v0.16.0 does not forward API auth headers when it downloads image_url.
    return FileResponse(
        TEST_IMAGE_PATH,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )
