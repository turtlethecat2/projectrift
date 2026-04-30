"""Outreach OAuth routes (optional)."""

import logging
import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from api.config import outreach_oauth_configured, settings
from api.outreach_client import (
    OUTREACH_AUTH_URL,
    OUTREACH_SCOPES,
    OUTREACH_TOKEN_URL,
    save_tokens,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_pending_states: set[str] = set()


@router.get("/outreach/start", summary="Start Outreach OAuth")
async def outreach_start():
    if not outreach_oauth_configured():
        raise HTTPException(
            status_code=400,
            detail="Outreach OAuth is not configured. Set OUTREACH_CLIENT_ID, "
            "OUTREACH_CLIENT_SECRET, and OUTREACH_REDIRECT_URI in .env (see docs/MVP_SETUP.md).",
        )
    state = secrets.token_urlsafe(32)
    _pending_states.add(state)

    params = {
        "client_id": settings.OUTREACH_CLIENT_ID,
        "redirect_uri": settings.OUTREACH_REDIRECT_URI,
        "response_type": "code",
        "scope": OUTREACH_SCOPES,
        "state": state,
    }
    auth_url = OUTREACH_AUTH_URL + "?" + urlencode(params)
    return RedirectResponse(url=auth_url)


@router.get("/outreach/callback", summary="Outreach OAuth callback")
async def outreach_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Outreach authorization failed: {error}",
        )

    if not state or state not in _pending_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid state (CSRF). Start again at /auth/outreach/start",
        )
    _pending_states.discard(state)

    if not outreach_oauth_configured():
        raise HTTPException(status_code=400, detail="Outreach OAuth is not configured")

    try:
        response = httpx.post(
            OUTREACH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.OUTREACH_REDIRECT_URI,
            },
            auth=(settings.OUTREACH_CLIENT_ID, settings.OUTREACH_CLIENT_SECRET),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        logger.error("Outreach token exchange failed: %s", e.response.text)
        raise HTTPException(
            status_code=502,
            detail=f"Outreach token exchange failed: {e.response.text}",
        ) from e

    from datetime import datetime, timedelta, timezone

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    save_tokens(data["access_token"], data["refresh_token"], expires_at)
    logger.info("Outreach OAuth authorized successfully")

    return {"status": "authorized", "expires_at": expires_at.isoformat()}
