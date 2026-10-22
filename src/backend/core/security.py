"""Security module - JWT, password hashing, token management"""

import base64
import hashlib
import os
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

import jwt
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, ValidationError

from .config import settings


class TokenClaims(BaseModel):
    model_config = ConfigDict(extra="allow")

    sub: UUID
    municipio_id: UUID
    type: Literal["access", "refresh", "mfa"]
    exp: int
    sid: UUID | None = None
    jti: UUID | None = None
    username: str | None = None


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__type="id",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    return str(pwd_context.hash(password))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid4())})
    return str(jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))


def create_refresh_token(data: dict[str, Any], jti: str | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti or str(uuid4())})
    return str(jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))


def create_mfa_token(data: dict[str, Any]) -> str:
    """Short-lived token for the second MFA step of the login flow.

    type != "access" so it can never be used to call protected endpoints.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=5)
    to_encode.update({"exp": expire, "type": "mfa"})
    return str(jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        claims = TokenClaims.model_validate(payload)
        return {
            **payload,
            "sub": str(claims.sub),
            "municipio_id": str(claims.municipio_id),
            "sid": str(claims.sid) if claims.sid else None,
            "jti": str(claims.jti) if claims.jti else None,
        }
    except (jwt.InvalidTokenError, ValidationError, TypeError, ValueError):
        return None


def _encryption_key() -> bytes:
    value = settings.ENCRYPTION_KEY.encode("utf-8")
    return hashlib.sha256(value).digest()


def encrypt_totp_secret(secret: str) -> str:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_encryption_key()).encrypt(nonce, secret.encode("utf-8"), b"totp:v1")
    payload = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"enc:v1:{payload}"


def decrypt_totp_secret(value: str) -> str:
    if not value.startswith("enc:v1:"):
        return value
    try:
        payload = base64.urlsafe_b64decode(value.removeprefix("enc:v1:").encode("ascii"))
        return AESGCM(_encryption_key()).decrypt(payload[:12], payload[12:], b"totp:v1").decode()
    except (InvalidTag, ValueError, UnicodeDecodeError) as exc:
        raise ValueError("No fue posible descifrar el secreto MFA") from exc


def generate_temporary_password(length: int = 24) -> str:
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return password
