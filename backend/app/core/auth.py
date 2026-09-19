"""
Bare-bones auth for ClauseIQ.

This is deliberately NOT multi-tenant user auth -- there's a single
shared APP_PASSWORD (set via env var), and anyone with it gets a JWT
that authorizes mutating requests (upload, set-template, risk-diff).
Read-only endpoints (status, list, search, query) stay open, since the
goal here is "not a wide-open single-user toy," not a real identity
system -- that's future work, tracked as a known limitation.

Real multi-tenant auth (per-user accounts, org membership, RBAC) is
out of scope for this project's timeline; Clerk/Auth0 was the
originally planned upgrade path if this became a real product.
"""

import time
from typing import Optional

import jwt

from app.core.config import settings

ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60 * 60 * 12  # 12 hours


def verify_password(password: str) -> bool:
    if not settings.APP_PASSWORD:
        # No password configured -- auth is effectively disabled. This is
        # intentional for local dev (matches pre-Day-13 behavior) but
        # should always be set in any deployed environment.
        return True
    return password == settings.APP_PASSWORD


def create_access_token() -> str:
    payload = {"exp": int(time.time()) + TOKEN_TTL_SECONDS, "iat": int(time.time())}
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
