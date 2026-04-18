# =============================================================================
#  VFS Global Appointment Bot — Production Dockerfile
#
#  Multi-stage build:
#    Stage 1 (builder) — installs Python deps into a clean venv
#    Stage 2 (runtime) — copies only the venv + source; installs Playwright
#                        browser binaries into the final image
#
#  Target platform  : linux/amd64 (matches GitHub Actions & GCP Cloud Run)
#  Base image       : python:3.11-slim-bookworm (Debian 12, minimal footprint)
# =============================================================================

# ── Stage 1: Dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build tools only in this stage (not in final image)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into an isolated venv
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip --quiet \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

# --------------------------------------------------------------------------
# Playwright's Chromium requires specific system libraries.
# This is the official list for Debian/Ubuntu headless environments.
# --------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        # Chromium runtime dependencies
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libpango-1.0-0 \
        libcairo2 \
        libatspi2.0-0 \
        libwayland-client0 \
        # Font support (prevents blank pages on some VFS pages)
        fonts-liberation \
        fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Copy Python venv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Make venv the default Python/pip
ENV PATH="/opt/venv/bin:$PATH"

# Install Playwright Chromium browser binary
# PLAYWRIGHT_BROWSERS_PATH controls where binaries land inside the image
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium

# --------------------------------------------------------------------------
# Non-root user for security (Cloud Run & GKE best practice)
# --------------------------------------------------------------------------
RUN groupadd --gid 1001 botuser \
    && useradd --uid 1001 --gid botuser --shell /bin/bash --create-home botuser \
    && chown -R botuser:botuser /ms-playwright

# Create required runtime directories with correct ownership
RUN mkdir -p /app/session /app/logs \
    && chown -R botuser:botuser /app

WORKDIR /app

# Copy application source (respects .dockerignore)
COPY --chown=botuser:botuser . .

# Switch to non-root user
USER botuser

# --------------------------------------------------------------------------
# Runtime environment defaults
# These can all be overridden at container start via --env or Cloud Run secrets
# --------------------------------------------------------------------------
ENV HEADLESS=true \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# --------------------------------------------------------------------------
# Cloud Run note:
#   Cloud Run invokes the container on demand (HTTP trigger or Job).
#   We run check_once.py as a one-shot Cloud Run Job (not a long-lived server).
#   The CMD below is the default; override it at deploy time if needed.
# --------------------------------------------------------------------------
CMD ["python", "check_once.py"]
