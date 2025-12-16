"""Tests for events router endpoints (SSE)."""

import anyio
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_sse_connection_success(client: AsyncClient) -> None:
    """Test SSE connection to valid chat returns 200 with correct content type."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    async def check_stream() -> None:
        async with client.stream(
            "GET",
            f"/api/v1/chats/{chat_id}/events",
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    with anyio.move_on_after(2):
        await check_stream()


@pytest.mark.anyio
async def test_sse_chat_not_found(client: AsyncClient) -> None:
    """Test SSE connection to non-existent chat returns 404."""
    fake_id = "01930000-0000-7000-8000-000000000000"

    response = await client.get(f"/api/v1/chats/{fake_id}/events")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_sse_invalid_uuid(client: AsyncClient) -> None:
    """Test SSE connection with invalid UUID returns 422."""
    response = await client.get("/api/v1/chats/not-a-uuid/events")
    assert response.status_code == 422
