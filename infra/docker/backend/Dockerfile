# Backend Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system app && useradd --system --ingroup app --create-home app

# Install Python dependencies
COPY src/backend/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir -e .

# Copy application code
COPY src/backend /app/src/backend
COPY migrations /app/migrations

# Create storage directory and set ownership
RUN mkdir -p /data/evidencias && chown -R app:app /data/evidencias /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Run the application (no --reload in production)
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
