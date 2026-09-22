from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import secrets


def _generate_default_secret() -> str:
    """Generate a cryptographically random secret key for development only."""
    return secrets.token_urlsafe(64)


class Settings(BaseSettings):
    # App
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    APP_NAME: str = Field(default="SIGEM Colombia", alias="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", alias="APP_VERSION")
    DEBUG: bool = Field(default=True, alias="DEBUG")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sigem:sigem_password@localhost:5432/sigem_db",
        alias="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # Database credentials (for docker-compose)
    POSTGRES_USER: str = Field(default="sigem", alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="sigem_password", alias="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="sigem_db", alias="POSTGRES_DB")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    REDIS_PASSWORD: str = Field(default="", alias="REDIS_PASSWORD")

    # Security
    SECRET_KEY: str = Field(
        default_factory=_generate_default_secret,
        alias="SECRET_KEY"
    )
    JWT_SECRET_KEY: str = Field(
        default_factory=_generate_default_secret,
        alias="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Passwords
    PASSWORD_HASH_ALGORITHM: str = Field(default="argon2id", alias="PASSWORD_HASH_ALGORITHM")
    PASSWORD_MIN_LENGTH: int = Field(default=15, alias="PASSWORD_MIN_LENGTH")
    TEMPORARY_PASSWORD_EXPIRY_HOURS: int = Field(default=24, alias="TEMPORARY_PASSWORD_EXPIRY_HOURS")

    # MFA
    MFA_ISSUER: str = Field(default="SIGEM Colombia", alias="MFA_ISSUER")
    MFA_ENABLED: bool = Field(default=True, alias="MFA_ENABLED")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    RATE_LIMIT_LOGIN_ATTEMPTS: int = Field(default=5, alias="RATE_LIMIT_LOGIN_ATTEMPTS")
    RATE_LIMIT_LOGIN_WINDOW_MINUTES: int = Field(default=15, alias="RATE_LIMIT_LOGIN_WINDOW_MINUTES")

    # Storage
    STORAGE_PATH: str = Field(default="/data/evidencias", alias="STORAGE_PATH")
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")

    # URLs
    FRONTEND_URL: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    BACKEND_URL: str = Field(default="http://localhost:8000", alias="BACKEND_URL")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
        alias="CORS_ORIGINS"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", alias="LOG_FORMAT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
