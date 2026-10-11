"""
Integration and API tests for health, readiness, error handling, and CORS.
"""

from unittest.mock import patch
import httpx
import pytest
from app.core.exceptions import DatabaseException


@pytest.mark.asyncio
async def test_health_liveness(async_client: httpx.AsyncClient):
    """Liveness probe must return 200 OK without requiring database connection."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_readiness_success(async_client: httpx.AsyncClient):
    """Readiness probe returns 200 OK when Neon PostgreSQL is reachable."""
    response = await async_client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "host" in data


@pytest.mark.asyncio
async def test_health_readiness_database_failure(async_client: httpx.AsyncClient):
    """
    Readiness probe returns 503 Service Unavailable when database fails.
    Must not expose credentials or connection strings in error payload.
    """
    with patch(
        "app.api.routes.health.check_database_readiness",
        side_effect=DatabaseException("Neon Cloud PostgreSQL is unreachable."),
    ):
        response = await async_client.get("/api/v1/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unready"
        assert data["database"] == "disconnected"
        assert "Neon Cloud PostgreSQL is unreachable." in data["message"]
        # Ensure no passwords or raw credentials appear
        assert "password" not in str(data).lower()
        assert "postgres://" not in str(data).lower()


@pytest.mark.asyncio
async def test_health_integrations_status(async_client: httpx.AsyncClient):
    """Integrations endpoint returns non-sensitive status report."""
    response = await async_client.get("/api/v1/health/integrations")
    assert response.status_code == 200
    data = response.json()
    assert "integrations" in data
    assert "cloudinary" in data["integrations"]
    assert "elevenlabs" in data["integrations"]
    assert "gemini" in data["integrations"]


@pytest.mark.asyncio
async def test_cors_preflight(async_client: httpx.AsyncClient):
    """CORS middleware returns allowed origin headers for allowlisted origins."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    response = await async_client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
