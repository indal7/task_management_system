"""
Pytest configuration and shared fixtures.

The test suite uses SQLite in-memory via TestingConfig so no external
database or Redis instance is required.
"""
import pytest

from app import create_app, db as _db
from config.testing import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Create application instance for the whole test session."""
    application = create_app(TestingConfig)
    application.config["TESTING"] = True

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Flask test client with a fresh transaction per test."""
    with app.test_client() as test_client:
        with app.app_context():
            yield test_client


@pytest.fixture(scope="function")
def db(app):
    """Provide the database session and roll back after each test."""
    with app.app_context():
        yield _db
        _db.session.rollback()
        _db.session.remove()
