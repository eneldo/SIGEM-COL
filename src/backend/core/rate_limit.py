"""Backends de rate limiting: memoria local y contador compartido en Redis.

En producción el límite debe ser compartido por todos los contenedores del stack;
por eso Redis es el backend por defecto y la memoria local queda como degradación
para el tráfico general y para entornos de desarrollo.
"""

import logging
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after: int = 0


class RateLimitBackend(Protocol):
    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        """Registra un intento y devuelve si debe permitirse."""


class InMemoryRateLimitBackend:
    """Contador por proceso. Adecuado para desarrollo y pruebas."""

    def __init__(self) -> None:
        self.counters: dict[str, list[float]] = {}
        self._last_cleanup = 0.0

    def _cleanup(self, window_seconds: int) -> None:
        import time

        now = time.time()
        if now - self._last_cleanup < window_seconds * 2:
            return
        self._last_cleanup = now
        cutoff = now - window_seconds
        for key in list(self.counters.keys()):
            self.counters[key] = [t for t in self.counters[key] if t > cutoff]
            if not self.counters[key]:
                del self.counters[key]

    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        import time

        self._cleanup(window_seconds)
        now = time.time()
        cutoff = now - window_seconds
        timestamps = [t for t in self.counters.get(key, []) if t > cutoff]
        if len(timestamps) >= limit:
            retry_after = int(timestamps[0] + window_seconds - now) + 1
            self.counters[key] = timestamps
            return RateLimitDecision(allowed=False, retry_after=max(retry_after, 1))
        timestamps.append(now)
        self.counters[key] = timestamps
        return RateLimitDecision(allowed=True)


class RedisRateLimitBackend:
    """Contador compartido entre procesos mediante INCR + EXPIRE.

    Los errores de Redis se propagan al middleware, que decide la politica de
    degradacion segun el bucket afectado.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    async def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitDecision:
        counter = await self.client.incr(key)
        if counter == 1:
            await self.client.expire(key, window_seconds)
        if counter > limit:
            return RateLimitDecision(allowed=False, retry_after=window_seconds)
        return RateLimitDecision(allowed=True)


def build_rate_limit_backend(is_production: bool, redis_url: str | None = None) -> Any:
    if not is_production:
        return InMemoryRateLimitBackend()
    from .redis_client import create_redis_client

    return RedisRateLimitBackend(create_redis_client(redis_url))
