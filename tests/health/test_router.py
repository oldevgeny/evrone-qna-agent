"""Tests for health router endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_check_returns_ok(client: AsyncClient) -> None:
    """Test basic health check returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_health_check_includes_version(client: AsyncClient) -> None:
    """Test health check includes version field."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)


@pytest.mark.anyio
async def test_liveness_returns_ok(client: AsyncClient) -> None:
    """Test liveness probe returns alive status."""
    response = await client.get("/health/live")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "alive"
    assert "version" in data


@pytest.mark.anyio
async def test_readiness_healthy(client: AsyncClient) -> None:
    """Test readiness probe when all dependencies are healthy."""
    response = await client.get("/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "healthy"
    assert "knowledge_base" in data
    assert "version" in data


@pytest.mark.anyio
async def test_readiness_database_unhealthy(client: AsyncClient) -> None:
    """Test readiness probe when database connection fails."""
    with patch(
        "qna_agent.health.router.AsyncSession.execute",
        new_callable=AsyncMock,
        side_effect=Exception("DB connection failed"),
    ):
        response = await client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["database"] == "unhealthy"
        assert data["status"] == "not_ready"
