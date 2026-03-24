"""Tests for custom exception classes and handlers."""
import pytest
from app.core.exceptions import AppException, NotFoundError, ForbiddenError, ConflictError


def test_app_exception():
    exc = AppException(status_code=500, detail="Something went wrong")
    assert exc.status_code == 500
    assert exc.detail == "Something went wrong"


def test_not_found_error():
    exc = NotFoundError()
    assert exc.status_code == 404
    assert exc.detail == "Resource not found"


def test_not_found_error_custom_detail():
    exc = NotFoundError(detail="User not found")
    assert exc.status_code == 404
    assert exc.detail == "User not found"


def test_forbidden_error():
    exc = ForbiddenError()
    assert exc.status_code == 403
    assert exc.detail == "Not enough permissions"


def test_conflict_error():
    exc = ConflictError()
    assert exc.status_code == 409
    assert exc.detail == "Resource already exists"
