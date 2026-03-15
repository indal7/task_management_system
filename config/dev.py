import os
import re
from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development environment settings."""

    DEBUG = False
    SQLALCHEMY_ECHO = False

    # Falls back to the hardcoded dev DB if DATABASE_URL is not set locally.
    # Set DATABASE_URL in your env/.env.dev file to override.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://myuser:MySecurePassword123%21@dev-database.c1qe2o6s6oix.ap-south-1.rds.amazonaws.com:5432/myapp?sslmode=require',
    )

    # Cache settings for development
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/1'  # Use DB 1 for dev
    CACHE_DEFAULT_TIMEOUT = 60  # Shorter timeout for dev

    LOG_TO_STDOUT = True

    # Allow any localhost origin in development (covers any port the Angular
    # dev server or other local tooling might choose, e.g. 4200, 56675, …).
    CORS_ORIGINS = [re.compile(r'http://localhost(:\d+)?')]
