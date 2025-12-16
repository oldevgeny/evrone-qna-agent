"""Tests for message router endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from qna_agent.agent.exceptions import (
    LLMConnectionError,
    LLMResponseError,
    MaxIterationsExceededError,
)
from qna_agent.agent.service import AgentResponse


# GET /api/v1/chats/{chat_id}/messages - List Messages Tests
@pytest.mark.anyio
async def test_list_messages_empty(client: AsyncClient) -> None:
    """Test listing messages for an empty chat."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}/messages")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.anyio
async def test_list_messages_not_found(client: AsyncClient) -> None:
    """Test listing messages for non-existent chat."""
    fake_id = "01930000-0000-7000-8000-000000000000"
    response = await client.get(f"/api/v1/chats/{fake_id}/messages")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_messages_invalid_uuid(client: AsyncClient) -> None:
    """Test listing messages with invalid UUID format."""
    response = await client.get("/api/v1/chats/not-a-uuid/messages")
    assert response.status_code == 422


# POST /api/v1/chats/{chat_id}/messages - Send Message Tests
@pytest.mark.anyio
async def test_send_message_success(client: AsyncClient) -> None:
    """Test sending a message and receiving AI response."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Hello! How can I help you?")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello"},
        )

    assert response.status_code == 201
    data = response.json()

    assert "user_message" in data
    assert "assistant_message" in data
    assert data["user_message"]["content"] == "Hello"
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["content"] == "Hello! How can I help you?"
    assert data["assistant_message"]["role"] == "assistant"


@pytest.mark.anyio
async def test_send_message_chat_not_found(client: AsyncClient) -> None:
    """Test sending a message to non-existent chat."""
    fake_id = "01930000-0000-7000-8000-000000000000"
    response = await client.post(
        f"/api/v1/chats/{fake_id}/messages",
        json={"content": "Hello"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_send_message_empty_content(client: AsyncClient) -> None:
    """Test sending a message with empty content."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": ""},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_send_message_content_min_length(client: AsyncClient) -> None:
    """Test sending a message with single character content."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Response")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "a"},
        )

    assert response.status_code == 201


@pytest.mark.anyio
async def test_send_message_content_max_length(client: AsyncClient) -> None:
    """Test sending a message with exactly 32000 characters."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Response to long message")
    long_content = "a" * 32000

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": long_content},
        )

    assert response.status_code == 201


@pytest.mark.anyio
async def test_send_message_content_exceeds_max(client: AsyncClient) -> None:
    """Test sending a message exceeding 32000 characters."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    long_content = "a" * 32001

    response = await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": long_content},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_send_message_unicode_content(client: AsyncClient) -> None:
    """Test sending a message with unicode characters."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Unicode response 日本語")
    unicode_content = "Hello 日本語 🎉 مرحبا 中文"

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": unicode_content},
        )

    assert response.status_code == 201
    assert response.json()["user_message"]["content"] == unicode_content


@pytest.mark.anyio
async def test_send_message_whitespace_only(client: AsyncClient) -> None:
    """Test sending a message with whitespace only."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Response")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "   "},
        )

    assert response.status_code == 201


@pytest.mark.anyio
async def test_send_message_special_characters(client: AsyncClient) -> None:
    """Test sending a message with special/potentially dangerous characters."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Safe response")
    special_content = '<script>alert("xss")</script> OR 1=1; DROP TABLE users;'

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": special_content},
        )

    assert response.status_code == 201
    assert response.json()["user_message"]["content"] == special_content


@pytest.mark.anyio
async def test_send_message_creates_both_messages(client: AsyncClient) -> None:
    """Test that send message creates both user and assistant messages in DB."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="AI Response")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "User message"},
        )

    list_response = await client.get(f"/api/v1/chats/{chat_id}/messages")
    data = list_response.json()

    assert data["total"] == 2
    assert data["items"][0]["role"] == "user"
    assert data["items"][1]["role"] == "assistant"


@pytest.mark.anyio
async def test_send_message_roles_correct(client: AsyncClient) -> None:
    """Test that message roles are correctly assigned."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Assistant response")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "User content"},
        )

    data = response.json()
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"


# LLM Error Scenarios (mocked)
@pytest.mark.anyio
async def test_send_message_llm_unavailable(client: AsyncClient) -> None:
    """Test sending a message when LLM connection fails."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        side_effect=LLMConnectionError("Connection refused"),
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello"},
        )

    assert response.status_code == 503
    assert "AI service temporarily unavailable" in response.json()["detail"]


@pytest.mark.anyio
async def test_send_message_llm_response_error(client: AsyncClient) -> None:
    """Test sending a message when LLM returns invalid response."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        side_effect=LLMResponseError("Invalid response format"),
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello"},
        )

    assert response.status_code == 503


@pytest.mark.anyio
async def test_send_message_max_iterations_exceeded(client: AsyncClient) -> None:
    """Test sending a message when agent exceeds max iterations."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        side_effect=MaxIterationsExceededError(10),
    ):
        response = await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Hello"},
        )

    assert response.status_code == 503


@pytest.mark.anyio
async def test_list_messages_with_items(client: AsyncClient) -> None:
    """Test listing messages after sending multiple messages."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response1 = AgentResponse(content="Response 1")
    mock_response2 = AgentResponse(content="Response 2")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        side_effect=[mock_response1, mock_response2],
    ):
        await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Message 1"},
        )
        await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Message 2"},
        )

    response = await client.get(f"/api/v1/chats/{chat_id}/messages")
    data = response.json()

    assert data["total"] == 4
    assert len(data["items"]) == 4


@pytest.mark.anyio
async def test_list_messages_ordered_by_created_at(client: AsyncClient) -> None:
    """Test that messages are returned in chronological order."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response1 = AgentResponse(content="First response")
    mock_response2 = AgentResponse(content="Second response")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        side_effect=[mock_response1, mock_response2],
    ):
        await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "First message"},
        )
        await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Second message"},
        )

    response = await client.get(f"/api/v1/chats/{chat_id}/messages")
    items = response.json()["items"]

    assert items[0]["content"] == "First message"
    assert items[1]["content"] == "First response"
    assert items[2]["content"] == "Second message"
    assert items[3]["content"] == "Second response"


@pytest.mark.anyio
async def test_list_messages_includes_all_fields(client: AsyncClient) -> None:
    """Test that list messages response includes all expected fields."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Response")

    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Test"},
        )

    response = await client.get(f"/api/v1/chats/{chat_id}/messages")
    message = response.json()["items"][0]

    assert "id" in message
    assert "chat_id" in message
    assert "role" in message
    assert "content" in message
    assert "created_at" in message
    assert "tool_calls" in message
    assert "tool_call_id" in message
