from .base import BaseConfig


class TestingConfig(BaseConfig):
    """Configuration for the automated test suite.

    Uses SQLite in-memory so tests run without a real database server.
    Disables Redis caching so no external service is required.
    """

    TESTING = True
    DEBUG = False

    # Use SQLite in-memory for tests — no database server needed
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False

    # Disable Redis; use a simple in-process dictionary instead
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 60

    # Disable CSRF for testing API endpoints
    WTF_CSRF_ENABLED = False

    # Use fixed secrets so tests are reproducible
    SECRET_KEY = "testing-secret-key"
    JWT_SECRET_KEY = "testing-jwt-secret-key"

    # Keep JWT expiry short for tests
    JWT_ACCESS_TOKEN_EXPIRES = 300

    # Suppress logging noise during tests
    LOG_LEVEL = "WARNING"
    LOG_TO_STDOUT = False

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False
