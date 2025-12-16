"""Tests for global exception handlers."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from qna_agent.exceptions import (
    KnowledgeBaseError,
    LLMError,
    ValidationError,
)


@pytest.mark.anyio
async def test_not_found_error_returns_404(client: AsyncClient) -> None:
    """Test that NotFoundError returns 404 with detail message."""
    fake_id = "01930000-0000-7000-8000-000000000000"
    response = await client.get(f"/api/v1/chats/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


@pytest.mark.anyio
async def test_validation_error_returns_400(client: AsyncClient) -> None:
    """Test that ValidationError returns 400 with detail message."""
    with patch(
        "qna_agent.chats.service.ChatService.create",
        new_callable=AsyncMock,
        side_effect=ValidationError("Invalid data provided"),
    ):
        response = await client.post(
            "/api/v1/chats",
            json={"title": "Test"},
        )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid data provided" in data["detail"]


@pytest.mark.anyio
async def test_llm_error_returns_503(client: AsyncClient) -> None:
    """Test that LLMError returns 503 with generic message."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        side_effect=LLMError("Internal LLM failure"),
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello"},
        )

    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "AI service temporarily unavailable"


@pytest.mark.anyio
async def test_knowledge_base_error_returns_500(client: AsyncClient) -> None:
    """Test that KnowledgeBaseError returns 500 with detail message."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        side_effect=KnowledgeBaseError("Knowledge base corrupted"),
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello"},
        )

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Knowledge base corrupted" in data["detail"]
