"""Integration tests for the agent with real LLM calls.

These tests require valid API credentials and are skipped by default.
Run with: pytest -m integration
"""

import os

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
@pytest.mark.skipif(
    not os.getenv("LITELLM_API_KEY"),
    reason="LITELLM_API_KEY not set",
)
async def test_agent_responds_to_message(client: AsyncClient) -> None:
    """Test that the agent responds to a user message."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "Hello, what can you help me with?"},
    )

    assert response.status_code == 201
    data = response.json()

    assert "user_message" in data
    assert "assistant_message" in data
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"
    assert len(data["assistant_message"]["content"]) > 0


@pytest.mark.anyio
@pytest.mark.skipif(
    not os.getenv("LITELLM_API_KEY"),
    reason="LITELLM_API_KEY not set",
)
async def test_agent_uses_knowledge_base(client: AsyncClient) -> None:
    """Test that the agent can search the knowledge base."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "List the available documents in the knowledge base"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["assistant_message"]["content"] is not None
