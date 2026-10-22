"""Cookie HttpOnly para el refresh token.

El refresh token nunca viaja en el cuerpo de la respuesta ni en el almacenamiento
del navegador: se entrega en una cookie HttpOnly, Secure y SameSite=Strict, con
Path limitado a las rutas de autenticacion para reducir la superficie de exposicion.
"""

from typing import Any

from .config import settings

REFRESH_COOKIE_NAME = "sigem_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def refresh_cookie_max_age() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def set_refresh_cookie(response: Any, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=refresh_cookie_max_age(),
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Any) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def read_refresh_cookie(request: Any) -> str | None:
    value = request.cookies.get(REFRESH_COOKIE_NAME)
    return value or None
