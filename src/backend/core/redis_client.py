"""Cliente Redis compartido por health checks y rate limiting."""

from typing import Any
from urllib.parse import quote, urlparse

from .config import settings


def redis_url_with_auth(url: str | None = None, password: str | None = None) -> str:
    url = url if url is not None else settings.REDIS_URL
    password = password if password is not None else settings.REDIS_PASSWORD
    if password and not urlparse(url).password:
        scheme, sep, rest = url.partition("://")
        if sep:
            return f"{scheme}://:{quote(password, safe='')}@{rest}"
    return url


def create_redis_client(url: str | None = None) -> Any:
    from redis import asyncio as redis_asyncio

    return redis_asyncio.from_url(
        redis_url_with_auth(url),
        socket_connect_timeout=1,
        socket_timeout=1,
    )
