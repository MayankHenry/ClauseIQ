from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from app.core.auth import verify_password, create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    if not verify_password(request.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    return LoginResponse(access_token=create_access_token())


def require_auth(authorization: Optional[str] = Header(default=None)) -> None:
    """
    FastAPI dependency that protects mutating endpoints. If APP_PASSWORD
    isn't configured (local dev default), auth is a no-op so existing
    workflows keep working without setup. Once APP_PASSWORD is set (any
    deployed environment should set it), a valid Bearer token is required.
    """
    if not settings.APP_PASSWORD:
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
