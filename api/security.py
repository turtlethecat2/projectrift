"""Webhook secret verification and rate limiting."""

import secrets

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


async def verify_webhook_secret(
    x_rift_secret: str = Header(..., alias="X-RIFT-SECRET"),
) -> None:
    if not secrets.compare_digest(x_rift_secret, settings.WEBHOOK_SECRET):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook secret",
            headers={"WWW-Authenticate": "Bearer"},
        )


RATE_LIMITS = {
    "webhook": f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
    "health": "100/minute",
    "stats": "120/minute",
}


def get_rate_limit_for_endpoint(endpoint_type: str) -> str:
    return RATE_LIMITS.get(endpoint_type, f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
