"""
Security utilities for Project Rift API
Handles authentication and rate limiting
"""

import secrets

from fastapi import Header, HTTPException, Request
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.config import settings

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)

# HTTP Bearer for potential future token auth
security = HTTPBearer(auto_error=False)


async def verify_webhook_secret(
    x_rift_secret: str = Header(..., alias="X-RIFT-SECRET")
) -> None:
    """
    Verify the webhook secret header matches the configured secret

    Args:
        x_rift_secret: Secret token from request header

    Raises:
        HTTPException: 401 if secret is invalid
    """
    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_rift_secret, settings.WEBHOOK_SECRET):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook secret",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_webhook_secret(length: int = 32) -> str:
    """
    Generate a secure random webhook secret

    Args:
        length: Length of the secret (default 32 characters)

    Returns:
        URL-safe random string
    """
    return secrets.token_urlsafe(length)


async def verify_api_key(api_key: str = Header(..., alias="X-API-KEY")) -> None:
    """
    Verify API key for future multi-user support

    Args:
        api_key: API key from request header

    Raises:
        HTTPException: 401 if API key is invalid
    """
    # Placeholder for future implementation
    # Currently not used, but structure is in place
    pass


def get_rate_limit_key(request: Request) -> str:
    """
    Custom rate limit key function
    Can be extended to rate limit by user ID instead of IP

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key (IP address)
    """
    return get_remote_address(request)


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "webhook": f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
    "health": "100/minute",
    "stats": "120/minute",
}


def get_rate_limit_for_endpoint(endpoint_type: str) -> str:
    """
    Get rate limit configuration for a specific endpoint type

    Args:
        endpoint_type: Type of endpoint (webhook, health, stats)

    Returns:
        Rate limit string (e.g., "60/minute")
    """
    return RATE_LIMITS.get(endpoint_type, f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
