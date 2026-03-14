import os
from .base import BaseConfig


class ProductionConfig(BaseConfig):
    """Production environment settings.

    All sensitive values MUST be provided via environment variables.
    No hardcoded secrets or connection strings.
    """

    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False

    # ── Database ──────────────────────────────────────────────────────────────
    # Provide via DATABASE_URL environment variable.
    # Example: postgresql://user:pass@host:5432/dbname?sslmode=require
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    # ── Cache / Redis ─────────────────────────────────────────────────────────
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL", "redis://localhost:6379/1")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300))

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Example: CORS_ORIGINS=https://app.example.com
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")
    LOG_TO_STDOUT = os.getenv("LOG_TO_STDOUT", "true").lower() == "true"

    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        # Fail fast if required secrets are missing
        required_vars = ["DATABASE_URL", "SECRET_KEY", "JWT_SECRET_KEY"]
        missing = [v for v in required_vars if not os.getenv(v)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables for production: {', '.join(missing)}"
            )
        # In production, propagate errors to WSGI server instead of Flask's
        # built-in error handler so Gunicorn/uWSGI can manage them.
        import logging
        gunicorn_logger = logging.getLogger("gunicorn.error")
        if gunicorn_logger.handlers:
            app.logger.handlers = gunicorn_logger.handlers
            app.logger.setLevel(gunicorn_logger.level)

