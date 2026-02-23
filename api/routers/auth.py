"""
OAuth 2.0 endpoints for Outreach integration.
Handles the authorization redirect and token exchange callback.
"""

import logging
import secrets
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from api.config import settings
from api.outreach_client import (
    OUTREACH_AUTH_URL,
    OUTREACH_SCOPES,
    OUTREACH_TOKEN_URL,
    save_tokens,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# CSRF protection: pending state tokens (single-user, in-memory is sufficient)
_pending_states: set[str] = set()


@router.get("/outreach/start", summary="Start Outreach OAuth authorization flow")
async def outreach_start():
    """
    Redirect the user to Outreach's authorization page.
    Generates a CSRF state token to verify the callback.
    """
    state = secrets.token_urlsafe(32)
    _pending_states.add(state)

    params = {
        "client_id": settings.OUTREACH_CLIENT_ID,
        "redirect_uri": settings.OUTREACH_REDIRECT_URI,
        "response_type": "code",
        "scope": OUTREACH_SCOPES,
        "state": state,
    }
    auth_url = OUTREACH_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=auth_url)


@router.get("/outreach/callback", summary="Handle Outreach OAuth callback")
async def outreach_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
):
    """
    Receive the OAuth callback from Outreach.

    - If Outreach sends ?error=..., return 400 immediately.
    - Validates the state parameter against the pending set (CSRF check).
    - Exchanges the authorization code for access and refresh tokens.
    - Saves tokens to the database.
    """
    # Outreach rejected authorization (e.g. user clicked "Deny")
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Outreach authorization failed: {error}",
        )

    # CSRF check: state must match one we generated in /start
    if not state or state not in _pending_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter (CSRF check failed). Start auth again at /auth/outreach/start",
        )
    _pending_states.discard(state)

    # Exchange authorization code for tokens
    try:
        response = httpx.post(
            OUTREACH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.OUTREACH_CLIENT_ID,
                "client_secret": settings.OUTREACH_CLIENT_SECRET,
                "redirect_uri": settings.OUTREACH_REDIRECT_URI,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Outreach token exchange failed: {e.response.text}")
        raise HTTPException(
            status_code=502,
            detail=f"Outreach token exchange failed: {e.response.text}",
        )

    from datetime import datetime, timezone, timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    save_tokens(data["access_token"], data["refresh_token"], expires_at)
    logger.info("Outreach OAuth authorized successfully")

    return {"status": "authorized", "expires_at": expires_at.isoformat()}
