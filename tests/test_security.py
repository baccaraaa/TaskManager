"""Direct unit tests for app.core.security module."""
import pytest
from datetime import timedelta
from jose import jwt
from fastapi import HTTPException

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.core.config import settings


def test_password_hash_and_verify():
    password = "mysecretpassword"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_default_expiry():
    token = create_access_token(data={"sub": "testuser"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["type"] == "access"


def test_create_access_token_custom_expiry():
    token = create_access_token(
        data={"sub": "testuser"}, expires_delta=timedelta(minutes=5)
    )
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["type"] == "access"


def test_create_refresh_token_default_expiry():
    token = create_refresh_token(data={"sub": "testuser"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["type"] == "refresh"


def test_create_refresh_token_custom_expiry():
    token = create_refresh_token(
        data={"sub": "testuser"}, expires_delta=timedelta(days=1)
    )
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["type"] == "refresh"


def test_verify_token_access():
    token = create_access_token(data={"sub": "testuser"})
    payload = verify_token(token, token_type="access")
    assert payload["sub"] == "testuser"


def test_verify_token_wrong_type():
    token = create_access_token(data={"sub": "testuser"})
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, token_type="refresh")
    assert exc_info.value.status_code == 401
    assert "Invalid token type" in exc_info.value.detail


def test_verify_token_invalid():
    with pytest.raises(HTTPException) as exc_info:
        verify_token("invalid-token")
    assert exc_info.value.status_code == 401


def test_create_password_reset_token():
    token = create_password_reset_token("user@example.com")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["email"] == "user@example.com"
    assert payload["type"] == "password_reset"


def test_verify_password_reset_token_valid():
    token = create_password_reset_token("user@example.com")
    email = verify_password_reset_token(token)
    assert email == "user@example.com"


def test_verify_password_reset_token_invalid():
    result = verify_password_reset_token("invalid-token")
    assert result is None


def test_verify_password_reset_token_wrong_type():
    # An access token should not be accepted as a password reset token
    token = create_access_token(data={"sub": "testuser"})
    result = verify_password_reset_token(token)
    assert result is None
