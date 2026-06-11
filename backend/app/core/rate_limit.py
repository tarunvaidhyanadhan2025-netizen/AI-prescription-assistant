"""
Rate limiting middleware — sliding window per client IP.
Configurable via env vars. No Redis required (in-memory).
For production with multiple workers, replace with Redis-backed store.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable, Deque

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter.

    Default: 60 requests / 60 seconds per IP.
    Upload endpoint: 10 requests / 60 seconds per IP (heavier operation).
    Analysis endpoint: 30 requests / 60 seconds per IP.
    """

    # (max_requests, window_seconds) per path prefix
    LIMITS: dict[str, tuple[int, int]] = {
        "/api/v1/upload": (10, 60),
        "/api/v1/analysis": (30, 60),
        "/api/v1/health": (120, 60),
    }
    DEFAULT_LIMIT = (60, 60)

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self._enabled = enabled
        # client_ip -> path_prefix -> deque of timestamps
        self._windows: dict[str, dict[str, Deque[float]]] = defaultdict(
            lambda: defaultdict(deque)
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._enabled:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Find matching limit rule
        max_req, window = self.DEFAULT_LIMIT
        for prefix, limit in self.LIMITS.items():
            if path.startswith(prefix):
                max_req, window = limit
                break

        # Sliding window check
        now = time.monotonic()
        bucket = self._windows[client_ip][path]

        # Remove expired timestamps
        while bucket and bucket[0] < now - window:
            bucket.popleft()

        if len(bucket) >= max_req:
            retry_after = int(window - (now - bucket[0])) + 1
            logger.warning(f"Rate limit hit: {client_ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Try again in {retry_after}s.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(max_req - len(bucket))
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        # Respect X-Forwarded-For if behind a proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
