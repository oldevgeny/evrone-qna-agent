"""Tests for chat router endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from qna_agent.agent.service import AgentResponse


# POST /api/v1/chats - Create Chat Tests
@pytest.mark.anyio
async def test_create_chat(client: AsyncClient) -> None:
    """Test creating a new chat with title and metadata."""
    response = await client.post(
        "/api/v1/chats",
        json={"title": "Test Chat", "metadata": {"key": "value"}},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Test Chat"
    assert data["metadata"] == {"key": "value"}
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_chat_minimal(client: AsyncClient) -> None:
    """Test creating a chat with minimal data (empty body)."""
    response = await client.post("/api/v1/chats", json={})
    assert response.status_code == 201

    data = response.json()
    assert data["title"] is None
    assert data["metadata"] == {}


@pytest.mark.anyio
async def test_create_chat_title_max_length(client: AsyncClient) -> None:
    """Test creating a chat with exactly 255 character title."""
    title = "a" * 255
    response = await client.post("/api/v1/chats", json={"title": title})
    assert response.status_code == 201
    assert response.json()["title"] == title


@pytest.mark.anyio
async def test_create_chat_title_exceeds_max(client: AsyncClient) -> None:
    """Test creating a chat with title exceeding 255 characters."""
    title = "a" * 256
    response = await client.post("/api/v1/chats", json={"title": title})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_chat_empty_title(client: AsyncClient) -> None:
    """Test creating a chat with empty string title."""
    response = await client.post("/api/v1/chats", json={"title": ""})
    assert response.status_code == 201
    assert response.json()["title"] == ""


@pytest.mark.anyio
async def test_create_chat_unicode_title(client: AsyncClient) -> None:
    """Test creating a chat with unicode characters in title."""
    title = "Test 日本語 🎉 مرحبا"
    response = await client.post("/api/v1/chats", json={"title": title})
    assert response.status_code == 201
    assert response.json()["title"] == title


@pytest.mark.anyio
async def test_create_chat_nested_metadata(client: AsyncClient) -> None:
    """Test creating a chat with deeply nested metadata."""
    metadata = {
        "level1": {
            "level2": {
                "level3": {"key": "value"},
            },
        },
        "list": [1, 2, 3],
    }
    response = await client.post("/api/v1/chats", json={"metadata": metadata})
    assert response.status_code == 201
    assert response.json()["metadata"] == metadata


@pytest.mark.anyio
async def test_create_chat_null_values_in_metadata(client: AsyncClient) -> None:
    """Test creating a chat with null values in metadata."""
    metadata = {"key": None, "other": "value"}
    response = await client.post("/api/v1/chats", json={"metadata": metadata})
    assert response.status_code == 201
    assert response.json()["metadata"] == metadata


# GET /api/v1/chats - List Chats Tests
@pytest.mark.anyio
async def test_list_chats_empty(client: AsyncClient) -> None:
    """Test listing chats when empty."""
    response = await client.get("/api/v1/chats")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.anyio
async def test_list_chats_with_items(client: AsyncClient) -> None:
    """Test listing chats with items."""
    await client.post("/api/v1/chats", json={"title": "Chat 1"})
    await client.post("/api/v1/chats", json={"title": "Chat 2"})

    response = await client.get("/api/v1/chats")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.anyio
async def test_list_chats_pagination_first_page(client: AsyncClient) -> None:
    """Test listing chats with pagination - first page."""
    for i in range(5):
        await client.post("/api/v1/chats", json={"title": f"Chat {i}"})

    response = await client.get("/api/v1/chats", params={"page": 1, "page_size": 2})
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["pages"] == 3


@pytest.mark.anyio
async def test_list_chats_pagination_second_page(client: AsyncClient) -> None:
    """Test listing chats with pagination - second page."""
    for i in range(5):
        await client.post("/api/v1/chats", json={"title": f"Chat {i}"})

    response = await client.get("/api/v1/chats", params={"page": 2, "page_size": 2})
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 2


@pytest.mark.anyio
async def test_list_chats_pagination_beyond_total(client: AsyncClient) -> None:
    """Test listing chats with page beyond total pages."""
    await client.post("/api/v1/chats", json={"title": "Only Chat"})

    response = await client.get("/api/v1/chats", params={"page": 10, "page_size": 10})
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 1


@pytest.mark.anyio
async def test_list_chats_page_size_boundary(client: AsyncClient) -> None:
    """Test listing chats with max page_size (100)."""
    response = await client.get("/api/v1/chats", params={"page_size": 100})
    assert response.status_code == 200


@pytest.mark.anyio
async def test_list_chats_page_size_exceeds_max(client: AsyncClient) -> None:
    """Test listing chats with page_size exceeding max (101)."""
    response = await client.get("/api/v1/chats", params={"page_size": 101})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_chats_page_zero(client: AsyncClient) -> None:
    """Test listing chats with page=0 (invalid)."""
    response = await client.get("/api/v1/chats", params={"page": 0})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_chats_negative_page(client: AsyncClient) -> None:
    """Test listing chats with negative page number."""
    response = await client.get("/api/v1/chats", params={"page": -1})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_chats_page_size_zero(client: AsyncClient) -> None:
    """Test listing chats with page_size=0 (invalid)."""
    response = await client.get("/api/v1/chats", params={"page_size": 0})
    assert response.status_code == 422


# GET /api/v1/chats/{chat_id} - Get Chat Tests
@pytest.mark.anyio
async def test_get_chat(client: AsyncClient) -> None:
    """Test getting a specific chat."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"title": "My Chat"},
    )
    chat_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == chat_id
    assert data["title"] == "My Chat"


@pytest.mark.anyio
async def test_get_chat_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent chat."""
    fake_id = "01930000-0000-7000-8000-000000000000"
    response = await client.get(f"/api/v1/chats/{fake_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_chat_invalid_uuid_format(client: AsyncClient) -> None:
    """Test getting a chat with invalid UUID format."""
    response = await client.get("/api/v1/chats/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_chat_returns_timestamps(client: AsyncClient) -> None:
    """Test that get chat returns proper timestamps."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}")
    data = response.json()

    assert "created_at" in data
    assert "updated_at" in data
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)


# PATCH /api/v1/chats/{chat_id} - Update Chat Tests
@pytest.mark.anyio
async def test_update_chat(client: AsyncClient) -> None:
    """Test updating a chat's title."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"title": "Original Title"},
    )
    chat_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}",
        json={"title": "Updated Title"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.anyio
async def test_update_chat_metadata(client: AsyncClient) -> None:
    """Test updating a chat's metadata."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"metadata": {"old": "data"}},
    )
    chat_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}",
        json={"metadata": {"new": "data"}},
    )
    assert response.status_code == 200
    assert response.json()["metadata"] == {"new": "data"}


@pytest.mark.anyio
async def test_update_chat_partial_title_only(client: AsyncClient) -> None:
    """Test updating only title, metadata unchanged."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"title": "Original", "metadata": {"keep": "this"}},
    )
    chat_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}",
        json={"title": "New Title"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["metadata"] == {"keep": "this"}


@pytest.mark.anyio
async def test_update_chat_partial_metadata_only(client: AsyncClient) -> None:
    """Test updating only metadata, title unchanged."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"title": "Keep This"},
    )
    chat_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}",
        json={"metadata": {"new": "data"}},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Keep This"
    assert response.json()["metadata"] == {"new": "data"}


@pytest.mark.anyio
async def test_update_chat_null_title(client: AsyncClient) -> None:
    """Test setting title to null via update."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"title": "Has Title"},
    )
    chat_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}",
        json={"title": None},
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_update_chat_empty_body(client: AsyncClient) -> None:
    """Test update with empty body - nothing should change."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"title": "Original"},
    )
    chat_id = create_response.json()["id"]

    response = await client.patch(f"/api/v1/chats/{chat_id}", json={})
    assert response.status_code == 200
    assert response.json()["title"] == "Original"


@pytest.mark.anyio
async def test_update_chat_not_found(client: AsyncClient) -> None:
    """Test updating a non-existent chat."""
    fake_id = "01930000-0000-7000-8000-000000000000"
    response = await client.patch(f"/api/v1/chats/{fake_id}", json={"title": "New"})
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_chat_title_max_length(client: AsyncClient) -> None:
    """Test updating chat with exactly 255 character title."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    title = "a" * 255
    response = await client.patch(f"/api/v1/chats/{chat_id}", json={"title": title})
    assert response.status_code == 200
    assert response.json()["title"] == title


@pytest.mark.anyio
async def test_update_chat_title_exceeds_max(client: AsyncClient) -> None:
    """Test updating chat with title exceeding 255 characters."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    title = "a" * 256
    response = await client.patch(f"/api/v1/chats/{chat_id}", json={"title": title})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_chat_updates_timestamp(client: AsyncClient) -> None:
    """Test that update changes the updated_at timestamp."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]
    original_updated_at = create_response.json()["updated_at"]

    response = await client.patch(
        f"/api/v1/chats/{chat_id}",
        json={"title": "Changed"},
    )
    new_updated_at = response.json()["updated_at"]

    assert new_updated_at >= original_updated_at


# DELETE /api/v1/chats/{chat_id} - Delete Chat Tests
@pytest.mark.anyio
async def test_delete_chat(client: AsyncClient) -> None:
    """Test deleting a chat."""
    create_response = await client.post(
        "/api/v1/chats",
        json={"title": "To Delete"},
    )
    chat_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/chats/{chat_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/chats/{chat_id}")
    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_chat_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent chat."""
    fake_id = "01930000-0000-7000-8000-000000000000"
    response = await client.delete(f"/api/v1/chats/{fake_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_chat_idempotent(client: AsyncClient) -> None:
    """Test deleting a chat twice - first succeeds, second returns 404."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    first_delete = await client.delete(f"/api/v1/chats/{chat_id}")
    assert first_delete.status_code == 204

    second_delete = await client.delete(f"/api/v1/chats/{chat_id}")
    assert second_delete.status_code == 404


@pytest.mark.anyio
async def test_delete_chat_cascades_messages(client: AsyncClient) -> None:
    """Test that deleting a chat also deletes all its messages."""
    create_response = await client.post("/api/v1/chats", json={})
    chat_id = create_response.json()["id"]

    mock_response = AgentResponse(content="Test response")
    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        await client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": "Test message"},
        )

    messages_response = await client.get(f"/api/v1/chats/{chat_id}/messages")
    assert messages_response.json()["total"] == 2

    delete_response = await client.delete(f"/api/v1/chats/{chat_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/chats/{chat_id}/messages")
    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_list_chats_ordered_by_created_at_desc(client: AsyncClient) -> None:
    """Test that chats are listed in descending order by created_at."""
    await client.post("/api/v1/chats", json={"title": "First"})
    await client.post("/api/v1/chats", json={"title": "Second"})
    await client.post("/api/v1/chats", json={"title": "Third"})

    response = await client.get("/api/v1/chats")
    items = response.json()["items"]

    assert items[0]["title"] == "Third"
    assert items[1]["title"] == "Second"
    assert items[2]["title"] == "First"
