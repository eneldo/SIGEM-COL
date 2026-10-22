FROM python:3.12.12-slim-bookworm AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/
COPY src/backend/pyproject.toml src/backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --no-editable

COPY src/backend /app/src/backend
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12.12-slim-bookworm

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv
COPY src /app/src
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

RUN mkdir -p /data/evidencias && chown -R app:app /data/evidencias /app

USER app

EXPOSE 8000

CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
