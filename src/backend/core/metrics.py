import re
import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

http_requests_total = Counter(
    "http_requests_total",
    "Total de peticiones HTTP procesadas",
    ["method", "path_template", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Duracion de las peticiones HTTP en segundos",
    ["method", "path_template"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

_UUID_PATH_PATTERN = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_NUMERIC_SEGMENT_PATTERN = re.compile(r"/\d+(?=/|$)")
_HEX_SEGMENT_PATTERN = re.compile(r"/[0-9a-fA-F]{16,}(?=/|$)")

METRICS_EXCLUDED_PATH = "/metrics"


def normalize_path(path: str) -> str:
    normalized = _UUID_PATH_PATTERN.sub("/{id}", path)
    normalized = _HEX_SEGMENT_PATTERN.sub("/{id}", normalized)
    return _NUMERIC_SEGMENT_PATTERN.sub("/{id}", normalized)


def path_template_for(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path
    return normalize_path(request.url.path)


def record_http_request(request: Request, status: int, duration_seconds: float) -> None:
    method = request.method
    path_template = path_template_for(request)
    http_requests_total.labels(method=method, path_template=path_template, status=str(status)).inc()
    http_request_duration_seconds.labels(method=method, path_template=path_template).observe(
        duration_seconds
    )


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        if request.url.path != METRICS_EXCLUDED_PATH:
            record_http_request(request, response.status_code, time.perf_counter() - start)
        return response
