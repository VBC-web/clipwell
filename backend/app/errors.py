from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class AppError(Exception):
    """An expected, client-safe service error."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        retry_after: int | None = None,
        platform: str | None = None,
        normalized_url: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after
        self.platform = platform
        self.normalized_url = normalized_url
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.retry_after is not None:
            error["retryAfterSeconds"] = self.retry_after
        if self.platform:
            error["platform"] = self.platform
        if self.details:
            error["details"] = self.details
        return {"error": error}


@dataclass(slots=True)
class ErrorInfo:
    code: str
    message: str
    status_code: int
