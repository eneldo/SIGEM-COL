import time
import logging
from collections import defaultdict
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter per IP address."""

    def __init__(self, app, max_requests: int = 50000, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _cleanup(self):
        now = time.time()
        if now - self._last_cleanup < self.window_seconds * 2:
            return
        self._last_cleanup = now
        cutoff = now - self.window_seconds
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
            if not self.requests[ip]:
                del self.requests[ip]

    async def dispatch(self, request: Request, call_next) -> Response:
        self._cleanup()

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - self.window_seconds

        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > cutoff]

        if len(self.requests[client_ip]) >= self.max_requests:
            retry_after = int(self.requests[client_ip][0] + self.window_seconds - now) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas solicitudes. Intente más tarde."},
                headers={"Retry-After": str(retry_after)},
            )

        self.requests[client_ip].append(now)
        return await call_next(request)


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and status."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        request_id = getattr(request.state, "request_id", str(uuid4()))
        client_ip = request.client.host if request.client else "unknown"

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
