"""
Unit tests for auth: password verification, token issue/decode, and the
require_auth FastAPI dependency's no-op-when-unconfigured behavior.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi import HTTPException

from app.core.auth import verify_password, create_access_token, decode_access_token
from app.core.config import settings
import app.api.auth as auth_module


def test_verify_password_no_password_configured_allows_anything(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD", "")
    assert verify_password("literally anything") is True


def test_verify_password_correct(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD", "secret123")
    assert verify_password("secret123") is True


def test_verify_password_incorrect(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD", "secret123")
    assert verify_password("wrong") is False


def test_create_and_decode_access_token_roundtrip(monkeypatch):
    monkeypatch.setattr(settings, "APP_SECRET_KEY", "test-secret")
    token = create_access_token()
    payload = decode_access_token(token)
    assert payload is not None
    assert "exp" in payload


def test_decode_access_token_rejects_garbage(monkeypatch):
    monkeypatch.setattr(settings, "APP_SECRET_KEY", "test-secret")
    assert decode_access_token("not.a.real.token") is None


def test_decode_access_token_rejects_wrong_secret(monkeypatch):
    monkeypatch.setattr(settings, "APP_SECRET_KEY", "secret-a")
    token = create_access_token()
    monkeypatch.setattr(settings, "APP_SECRET_KEY", "secret-b")
    assert decode_access_token(token) is None


def test_require_auth_noop_when_no_password_configured(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD", "")
    # should not raise, even with no Authorization header at all
    auth_module.require_auth(authorization=None)


def test_require_auth_rejects_missing_header_when_password_set(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD", "secret123")
    with pytest.raises(HTTPException) as exc_info:
        auth_module.require_auth(authorization=None)
    assert exc_info.value.status_code == 401


def test_require_auth_accepts_valid_bearer_token(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD", "secret123")
    monkeypatch.setattr(settings, "APP_SECRET_KEY", "test-secret")
    token = create_access_token()
    # should not raise
    auth_module.require_auth(authorization=f"Bearer {token}")


def test_require_auth_rejects_invalid_bearer_token(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD", "secret123")
    monkeypatch.setattr(settings, "APP_SECRET_KEY", "test-secret")
    with pytest.raises(HTTPException) as exc_info:
        auth_module.require_auth(authorization="Bearer garbage-token")
    assert exc_info.value.status_code == 401
