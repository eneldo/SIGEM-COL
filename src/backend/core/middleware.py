import logging
import time
from collections import defaultdict
from collections.abc import Sequence
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from .config import settings

logger = logging.getLogger(__name__)

LOGIN_RATE_LIMIT_PATHS: tuple[str, ...] = (
    "/api/v1/auth/login",
    "/api/v1/auth/mfa/",
)


def get_client_ip(request: Request, trust_proxy_headers: bool = False) -> str:
    if trust_proxy_headers:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            first_hop = forwarded_for.split(",")[0].strip()
            if first_hop:
                return first_hop
    if request.client:
        return request.client.host
    return "unknown"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limiter in-memory por IP: bucket general y bucket mas estricto para auth."""

    def __init__(
        self,
        app: ASGIApp,
        default_max_requests: int = 600,
        login_max_requests: int = 10,
        window_seconds: int = 60,
        login_path_prefixes: Sequence[str] = LOGIN_RATE_LIMIT_PATHS,
    ):
        super().__init__(app)
        self.default_max_requests = default_max_requests
        self.login_max_requests = login_max_requests
        self.window_seconds = max(1, window_seconds)
        self.login_path_prefixes = tuple(login_path_prefixes)
        self.counters: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _cleanup(self) -> None:
        now = time.time()
        if now - self._last_cleanup < self.window_seconds * 2:
            return
        self._last_cleanup = now
        cutoff = now - self.window_seconds
        for key in list(self.counters.keys()):
            self.counters[key] = [t for t in self.counters[key] if t > cutoff]
            if not self.counters[key]:
                del self.counters[key]

    def _bucket_for(self, path: str, client_ip: str) -> tuple[str, int]:
        if path.startswith(self.login_path_prefixes):
            return f"login:{client_ip}", self.login_max_requests
        return f"default:{client_ip}", self.default_max_requests

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        self._cleanup()

        client_ip = get_client_ip(request, settings.TRUST_PROXY_HEADERS)
        bucket_key, max_requests = self._bucket_for(request.url.path, client_ip)
        now = time.time()
        cutoff = now - self.window_seconds

        timestamps = [t for t in self.counters[bucket_key] if t > cutoff]
        self.counters[bucket_key] = timestamps

        if len(timestamps) >= max_requests:
            retry_after = int(timestamps[0] + self.window_seconds - now) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. Intente más tarde."},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        timestamps.append(now)
        response: Response = await call_next(request)
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and status."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.time()
        request_id = getattr(request.state, "request_id", str(uuid4()))
        client_ip = get_client_ip(request, settings.TRUST_PROXY_HEADERS)

        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.time() - start) * 1000
            logger.error(
                "request_error",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "ip": client_ip,
                    "elapsed_ms": round(elapsed, 2),
                },
            )
            raise

        elapsed = (time.time() - start) * 1000
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ip": client_ip,
            "elapsed_ms": round(elapsed, 2),
        }

        if response.status_code >= 500:
            logger.error("request_error", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("request_client_error", extra=log_data)
        else:
            logger.info("request", extra=log_data)

        return response
