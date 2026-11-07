from __future__ import annotations

import ipaddress
import math
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request

from .config import Settings
from .errors import AppError


class SlidingWindowLimiter:
    """Small in-process limiter. Each API instance keeps its own counters."""

    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._windows: dict[tuple[str, str], Deque[float]] = defaultdict(deque)
        self._last_cleanup = time.monotonic()

    def check(self, key: str, bucket: str, limit: int) -> None:
        if limit <= 0:
            return

        now = time.monotonic()
        cutoff = now - self.window_seconds
        window = self._windows[(key, bucket)]

        while window and window[0] <= cutoff:
            window.popleft()

        if len(window) >= limit:
            retry_after = max(1, math.ceil(self.window_seconds - (now - window[0])))
            raise AppError(
                "rate_limited",
                "Too many requests from this connection. Give it a minute and try again.",
                status_code=429,
                retry_after=retry_after,
            )

        window.append(now)
        self._maybe_cleanup(now)

    def _maybe_cleanup(self, now: float) -> None:
        if now - self._last_cleanup < 300:
            return
        self._last_cleanup = now
        cutoff = now - self.window_seconds
        stale = []
        for key, window in self._windows.items():
            while window and window[0] <= cutoff:
                window.popleft()
            if not window:
                stale.append(key)
        for key in stale:
            del self._windows[key]


def get_client_ip(request: Request, settings: Settings) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            candidate = forwarded.split(",", 1)[0].strip()
            try:
                return str(ipaddress.ip_address(candidate))
            except ValueError:
                pass

    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def allow_request(
    limiter: SlidingWindowLimiter,
    request: Request,
    settings: Settings,
    bucket: str,
    limit: int,
) -> None:
    limiter.check(get_client_ip(request, settings), bucket, limit)
