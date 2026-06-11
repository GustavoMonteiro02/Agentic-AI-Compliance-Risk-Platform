from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_bytes: int) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if self.max_body_bytes > 0:
            content_length = request.headers.get("content-length")
            try:
                declared_body_size = int(content_length) if content_length else 0
            except ValueError:
                declared_body_size = 0
            if declared_body_size > self.max_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "request_too_large",
                            "message": "Request body exceeds the configured maximum size.",
                            "max_body_bytes": self.max_body_bytes,
                        }
                    },
                )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, hsts_enabled: bool = False) -> None:
        super().__init__(app)
        self.hsts_enabled = hsts_enabled

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cache-Control", "no-store")
        if self.hsts_enabled:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if self.requests_per_minute <= 0 or request.url.path in {"/health", "/runtime/readiness"}:
            return await call_next(request)

        now = time.monotonic()
        key = self._rate_limit_key(request)
        bucket = self._requests[key]
        while bucket and now - bucket[0] >= self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(self.window_seconds),
                    "RateLimit-Limit": str(self.requests_per_minute),
                    "RateLimit-Remaining": "0",
                },
                content={
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Too many requests for this tenant or caller.",
                        "limit_per_minute": self.requests_per_minute,
                    }
                },
            )

        bucket.append(now)
        response = await call_next(request)
        response.headers.setdefault("RateLimit-Limit", str(self.requests_per_minute))
        response.headers.setdefault("RateLimit-Remaining", str(max(self.requests_per_minute - len(bucket), 0)))
        return response

    def _rate_limit_key(self, request: Request) -> str:
        tenant_id = request.headers.get("x-tenant-id", "default")
        api_key = request.headers.get("x-api-key")
        user = request.headers.get("x-user")
        client = request.client.host if request.client else "unknown"
        caller = api_key or user or client
        digest = hashlib.sha256(caller.encode("utf-8")).hexdigest()[:16]
        return f"{tenant_id}:{digest}"
