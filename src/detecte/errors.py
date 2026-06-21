"""Detecte SDK error hierarchy. Mirrors @detecte/sdk."""

from __future__ import annotations

from typing import Any


class DetecteError(Exception):
    """Base class for all Detecte errors."""

    code: str = "detecte_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class DetecteApiError(DetecteError):
    """A non-2xx HTTP response from the API."""

    code = "api_error"

    def __init__(
        self,
        message: str,
        *,
        status: int,
        body: Any = None,
        code: str | None = None,
    ):
        super().__init__(message, code=code or "api_error")
        self.status = status
        self.body = body


class DetecteAuthError(DetecteApiError):
    code = "auth_error"


class DetecteValidationError(DetecteApiError):
    code = "validation_error"


class DetecteRateLimitError(DetecteApiError):
    code = "rate_limit_exceeded"

    def __init__(
        self,
        message: str,
        *,
        status: int = 429,
        retry_after_ms: int | None = None,
        body: Any = None,
    ):
        super().__init__(message, status=status, body=body, code="rate_limit_exceeded")
        self.retry_after_ms = retry_after_ms


class DetecteNetworkError(DetecteError):
    code = "network_error"


class DetecteTimeoutError(DetecteNetworkError):
    code = "timeout"
