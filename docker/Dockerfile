# syntax=docker/dockerfile:1
# ==============================================================================
# Multi-stage Dockerfile – supports development and production build targets.
#
# Build targets:
#   development  – Flask dev server + hot-reload; used by docker-compose.dev.yml
#   production   – Gunicorn + gevent; optimised slim image for EC2 / ECS
#
# Examples:
#   docker build --target development -t taskmanager:dev .
#   docker build --target production  -t taskmanager:prod .
# ==============================================================================

# ── Stage 1: base ─────────────────────────────────────────────────────────────
# Shared OS-level runtime dependencies kept in a thin layer.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: builder ──────────────────────────────────────────────────────────
# Installs production Python packages; keeps gcc/build tools out of the final
# runtime image to reduce attack surface and image size.
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt

RUN pip install --prefix=/install --no-cache-dir \
        -r requirements/base.txt \
        -r requirements/production.txt

# ── Stage 3: development ──────────────────────────────────────────────────────
# Full dev-dependency image used for local development via docker-compose.dev.yml.
# Source code is bind-mounted at runtime, so COPY . is a fallback only.
FROM base AS development

ENV FLASK_ENV=development \
    FLASK_APP=app.py \
    FLASK_DEBUG=1

# gcc is needed to compile some dev packages (e.g. psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
COPY requirements/dev.txt requirements/dev.txt

RUN pip install --no-cache-dir \
        -r requirements/base.txt \
        -r requirements/dev.txt

# Copy application code (overridden by volume mount in docker-compose.dev.yml)
COPY . .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]

# ── Stage 4: production ───────────────────────────────────────────────────────
# Minimal production image – copies pre-built packages from the builder stage
# so no compiler toolchain is included in the final image.
FROM base AS production

ENV FLASK_ENV=production \
    FLASK_APP=wsgi:app

# Copy pre-built Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Copy and configure the production entrypoint (runs migrations, then gunicorn)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "wsgi:app"]
