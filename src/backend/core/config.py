from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings

DEV_SECRET_KEY_PLACEHOLDER = "dev-only-secret-key-do-not-use-in-production"
DEV_JWT_SECRET_PLACEHOLDER = "dev-only-jwt-secret-do-not-use-in-production"

_DEV_SECRET_PLACEHOLDERS = frozenset(
    {
        DEV_SECRET_KEY_PLACEHOLDER,
        DEV_JWT_SECRET_PLACEHOLDER,
        "change-this-to-a-random-secret-key-min-32-chars",
        "change-this-to-another-random-secret-key-min-32-chars",
        "change-me",
        "changeme",
        "secret",
        "dev-secret",
    }
)

_DEV_DATABASE_PASSWORD_MARKERS = (
    "sigem_password",
    "devpass2026",
    "dev-pass-2026",
    "password-dev",
)

_PRODUCTION_ENVIRONMENTS = frozenset({"production", "prod"})
_PLACEHOLDER_MARKERS = ("change_me", "changeme", ".example", "example.com")


def _contains_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return any(marker in normalized for marker in _PLACEHOLDER_MARKERS)


class Settings(BaseSettings):
    # App
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    APP_NAME: str = Field(default="SIGEM Colombia", alias="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", alias="APP_VERSION")
    DEBUG: bool = Field(default=True, alias="DEBUG")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sigem:sigem_password@localhost:5432/sigem_db",
        alias="DATABASE_URL",
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
    SECRET_KEY: str = Field(default=DEV_SECRET_KEY_PLACEHOLDER, alias="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(default=DEV_JWT_SECRET_PLACEHOLDER, alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Passwords
    PASSWORD_HASH_ALGORITHM: str = Field(default="argon2id", alias="PASSWORD_HASH_ALGORITHM")
    PASSWORD_MIN_LENGTH: int = Field(default=15, alias="PASSWORD_MIN_LENGTH")
    TEMPORARY_PASSWORD_EXPIRY_HOURS: int = Field(
        default=24, alias="TEMPORARY_PASSWORD_EXPIRY_HOURS"
    )

    # MFA
    MFA_ISSUER: str = Field(default="SIGEM Colombia", alias="MFA_ISSUER")
    MFA_ENABLED: bool = Field(default=True, alias="MFA_ENABLED")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    RATE_LIMIT_DEFAULT_REQUESTS: int = Field(default=600, alias="RATE_LIMIT_DEFAULT_REQUESTS")
    RATE_LIMIT_LOGIN_ATTEMPTS: int = Field(default=10, alias="RATE_LIMIT_LOGIN_ATTEMPTS")
    RATE_LIMIT_LOGIN_WINDOW_MINUTES: int = Field(
        default=15, alias="RATE_LIMIT_LOGIN_WINDOW_MINUTES"
    )
    RATE_LIMIT_WINDOW: int = Field(default=60, alias="RATE_LIMIT_WINDOW")
    TRUST_PROXY_HEADERS: bool = Field(default=False, alias="TRUST_PROXY_HEADERS")

    # Storage
    STORAGE_PATH: str = Field(default="/data/evidencias", alias="STORAGE_PATH")
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    EVIDENCE_IMAGE_MAX_DIMENSION: int = Field(default=2200, alias="EVIDENCE_IMAGE_MAX_DIMENSION")
    EVIDENCE_JPEG_QUALITY: int = Field(default=82, alias="EVIDENCE_JPEG_QUALITY")
    EVIDENCE_PDF_IMAGE_QUALITY: int = Field(default=78, alias="EVIDENCE_PDF_IMAGE_QUALITY")

    # URLs
    FRONTEND_URL: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    BACKEND_URL: str = Field(default="http://localhost:8000", alias="BACKEND_URL")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
        alias="CORS_ORIGINS",
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", alias="LOG_FORMAT")

    # Metrics
    METRICS_ENABLED: bool = Field(default=True, alias="METRICS_ENABLED")
    METRICS_TOKEN: str | None = Field(default=None, alias="METRICS_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        environments = {
            (self.ENVIRONMENT or "").strip().lower(),
            (self.APP_ENV or "").strip().lower(),
        }
        return bool(environments & _PRODUCTION_ENVIRONMENTS)

    def validate_production(self) -> None:
        if not self.is_production:
            return

        problems: list[str] = []

        if self.DEBUG:
            problems.append("DEBUG debe ser 'false' en producción")

        for field_name in ("SECRET_KEY", "JWT_SECRET_KEY"):
            value = str(getattr(self, field_name) or "")
            if (
                len(value) < 32
                or value.strip().lower() in _DEV_SECRET_PLACEHOLDERS
                or _contains_placeholder(value)
            ):
                problems.append(
                    f"{field_name} debe definirse con un valor de al menos 32 caracteres "
                    "que no sea el placeholder de desarrollo"
                )

        if self.SECRET_KEY == self.JWT_SECRET_KEY:
            problems.append("SECRET_KEY y JWT_SECRET_KEY deben ser diferentes")

        database_url = (self.DATABASE_URL or "").strip()
        parsed_database = urlparse(database_url)
        if not database_url:
            problems.append("DATABASE_URL no puede estar vacío en producción")
        elif any(
            marker in database_url.lower() for marker in _DEV_DATABASE_PASSWORD_MARKERS
        ) or _contains_placeholder(database_url):
            problems.append("DATABASE_URL contiene una contraseña de desarrollo")
        elif parsed_database.username != "sigem_app":
            problems.append("DATABASE_URL debe usar el rol restringido sigem_app")

        redis_url = (self.REDIS_URL or "").strip()
        if not self.REDIS_PASSWORD or _contains_placeholder(self.REDIS_PASSWORD):
            problems.append("REDIS_PASSWORD debe definirse con un valor real")
        if not redis_url or not urlparse(redis_url).password or _contains_placeholder(redis_url):
            problems.append("REDIS_URL debe incluir autenticación y no usar placeholders")

        for field_name in ("FRONTEND_URL", "BACKEND_URL"):
            value = str(getattr(self, field_name) or "")
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.hostname or _contains_placeholder(value):
                problems.append(f"{field_name} debe ser una URL HTTPS real")

        cors_origins = self.CORS_ORIGINS or []
        if "*" in cors_origins or any(
            urlparse(origin).scheme != "https" or _contains_placeholder(origin)
            for origin in cors_origins
        ):
            problems.append("CORS_ORIGINS debe contener únicamente orígenes HTTPS explícitos")

        if not self.MFA_ENABLED:
            problems.append("MFA_ENABLED debe estar activo en producción")
        if not self.RATE_LIMIT_ENABLED:
            problems.append("RATE_LIMIT_ENABLED debe estar activo en producción")
        if self.METRICS_ENABLED and (
            not self.METRICS_TOKEN or _contains_placeholder(self.METRICS_TOKEN)
        ):
            problems.append("METRICS_TOKEN debe definirse cuando las métricas están activas")

        if problems:
            raise RuntimeError("Configuración de producción inválida: " + "; ".join(problems))


settings = Settings()
