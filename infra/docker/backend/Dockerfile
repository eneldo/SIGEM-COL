# Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY src/backend/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir -e .

COPY src/backend /app/src/backend
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

RUN mkdir -p /data/evidencias && chown -R app:app /data/evidencias /app

USER app

EXPOSE 8000

CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
