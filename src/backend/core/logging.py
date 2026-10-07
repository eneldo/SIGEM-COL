import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_STANDARD_RECORD_ATTRIBUTES = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)

_FORWARDED_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "uvicorn.lifespan",
    "sqlalchemy.engine",
    "sqlalchemy.engine.Engine",
)


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list | tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}
    return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_ATTRIBUTES or key.startswith("_"):
                continue
            payload[key] = _safe_value(value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _resolve_level(log_level: str) -> int:
    level = logging.getLevelName((log_level or "INFO").strip().upper())
    return level if isinstance(level, int) else logging.INFO


def _build_formatter(log_format: str) -> logging.Formatter:
    if (log_format or "json").strip().lower() == "json":
        return JsonFormatter()
    return logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


class _AppStreamHandler(logging.StreamHandler[Any]):
    def __init__(self) -> None:
        super().__init__(sys.stdout)


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    level = _resolve_level(log_level)
    formatter = _build_formatter(log_format)

    handler = _AppStreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    for existing in list(root.handlers):
        if isinstance(existing, _AppStreamHandler):
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    for name in _FORWARDED_LOGGERS:
        forwarded_logger = logging.getLogger(name)
        for existing in list(forwarded_logger.handlers):
            forwarded_logger.removeHandler(existing)
        forwarded_logger.propagate = True
        forwarded_logger.setLevel(level)
