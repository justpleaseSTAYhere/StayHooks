"""Domain-specific exceptions raised by stayhere_webhooks."""

from __future__ import annotations

from typing import Any, Optional


class StayHereError(Exception):
    """Base error for the StayHere webhook SDK."""


class StayHereHTTPError(StayHereError):
    """Represents a non-2xx HTTP response from the StayHere server."""

    def __init__(self, status: int, message: str, payload: Optional[Any] = None):
        super().__init__(message)
        self.status = status
        self.payload = payload

    def __str__(self) -> str:  # pragma: no cover - repr sugar
        base = super().__str__()
        return f"{base} (status={self.status})"


class StayHereAuthError(StayHereHTTPError):
    """Raised when an authenticated endpoint is hit without valid credentials."""


class StayHereWebhookInvokeError(StayHereError):
    """Raised when a webhook invocation fails before reaching the StayHere server."""

    def __init__(self, message: str, *, payload: Optional[Any] = None):
        super().__init__(message)
        self.payload = payload


class StayHereValidationError(StayHereError):
    """Raised when user-supplied arguments are invalid before making a request."""
