"""
Tests for health-check endpoints.
"""


def test_health_check(client):
    """GET /health returns 200 with status=healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "task-management-api"


def test_health_check_db(client):
    """GET /health/db returns 200 when the database is reachable."""
    response = client.get("/health/db")
    # In testing mode we use SQLite in-memory, so the DB is always available.
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
