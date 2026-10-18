from app.config import settings


def test_basic_health_check(client):
    """Test that the liveness probe endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == settings.PROJECT_NAME


def test_detailed_health_check(client):
    """Test that the readiness probe endpoint checks the database and returns 200 OK."""
    response = client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["service"] == settings.PROJECT_NAME


def test_cors_and_openapi_docs(client):
    """Test that OpenAPI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Student Result Portal" in response.text
