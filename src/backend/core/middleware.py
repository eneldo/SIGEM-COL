import logging
import re
import time
from collections.abc import Sequence
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import settings
from .rate_limit import InMemoryRateLimitBackend, RateLimitBackend

logger = logging.getLogger(__name__)

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

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
        supplied_id = request.headers.get("X-Request-ID", "")
        request_id = supplied_id if REQUEST_ID_PATTERN.fullmatch(supplied_id) else str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limiter por IP: bucket general y bucket mas estricto para auth.

    El backend por defecto es compartido (Redis en produccion). Si el backend
    compartido no responde, el trafico general degrada al contador local y el
    bucket de autenticacion falla cerrado cuando `fail_closed_login` esta activo.
    """

    def __init__(
        self,
        app,
        default_max_requests: int = 600,
        login_max_requests: int = 10,
        window_seconds: int = 60,
        login_window_seconds: int | None = None,
        login_path_prefixes: Sequence[str] = LOGIN_RATE_LIMIT_PATHS,
        backend: RateLimitBackend | None = None,
        fail_closed_login: bool = True,
    ):
        super().__init__(app)
        self.default_max_requests = default_max_requests
        self.login_max_requests = login_max_requests
        self.window_seconds = max(1, window_seconds)
        self.login_window_seconds = max(
            1, login_window_seconds if login_window_seconds else window_seconds
        )
        self.login_path_prefixes = tuple(login_path_prefixes)
        self.backend = backend if backend is not None else InMemoryRateLimitBackend()
        self.fallback = InMemoryRateLimitBackend()
        self.fail_closed_login = fail_closed_login

    def _bucket_for(self, path: str, client_ip: str) -> tuple[str, int, int, bool]:
        if path.startswith(self.login_path_prefixes):
            return (
                f"login:{client_ip}",
                self.login_max_requests,
                self.login_window_seconds,
                True,
            )
        return f"default:{client_ip}", self.default_max_requests, self.window_seconds, False

    @staticmethod
    def _too_many_requests(retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Intente más tarde."},
            headers={"Retry-After": str(max(retry_after, 1))},
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = get_client_ip(request, settings.TRUST_PROXY_HEADERS)
        bucket_key, max_requests, window_seconds, is_login = self._bucket_for(
            request.url.path, client_ip
        )

        try:
            decision = await self.backend.hit(bucket_key, max_requests, window_seconds)
        except Exception:
            logger.warning("rate_limit_backend_unavailable", extra={"bucket": bucket_key})
            if is_login and self.fail_closed_login:
                return self._too_many_requests(window_seconds)
            decision = await self.fallback.hit(bucket_key, max_requests, window_seconds)

        if not decision.allowed:
            return self._too_many_requests(decision.retry_after or window_seconds)

        return await call_next(request)


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
