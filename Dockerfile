# ──────────────────────────────────────────────────────────────────────────────
# CAPTCHA Solver Testbed — Dockerfile
# Targets python:3.11-slim (Debian Bookworm).
# DejaVuSans-Bold is installed explicitly for the captcha library on Linux.
# data/images/ is baked in at build time → grid images survive Render restarts.
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Install font for ImageCaptcha (DejaVuSans-Bold) and curl (health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and assets
COPY app/           ./app/
COPY templates/     ./templates/
COPY static/        ./static/
COPY data/          ./data/

# SQLite DB lives at runtime only (ephemeral on Render free tier — by design).
# For persistent users set DATABASE_URL to a Postgres connection string.

# Non-root user for security
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Uvicorn: 2 workers is reasonable for free-tier RAM (~512 MB)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--access-log"]
