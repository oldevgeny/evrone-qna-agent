"""Tests for ChatService."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from qna_agent.chats.exceptions import ChatNotFoundError
from qna_agent.chats.schemas import ChatCreate, ChatUpdate
from qna_agent.chats.service import ChatService


@pytest.fixture
def chat_service(async_session: AsyncSession) -> ChatService:
    """Create ChatService with test session."""
    return ChatService(async_session)


@pytest.mark.anyio
async def test_create_chat_defaults(chat_service: ChatService) -> None:
    """Test creating a chat with default values."""
    data = ChatCreate()

    chat = await chat_service.create(data)

    assert chat.id is not None
    assert chat.title is None
    assert chat.metadata_ == {}
    assert chat.created_at is not None
    assert chat.updated_at is not None


@pytest.mark.anyio
async def test_create_chat_with_data(chat_service: ChatService) -> None:
    """Test creating a chat with title and metadata."""
    data = ChatCreate(title="Test Chat", metadata={"key": "value"})

    chat = await chat_service.create(data)

    assert chat.title == "Test Chat"
    assert chat.metadata_ == {"key": "value"}


@pytest.mark.anyio
async def test_get_chat_not_found(chat_service: ChatService) -> None:
    """Test getting a non-existent chat raises ChatNotFoundError."""
    fake_id = uuid4()

    with pytest.raises(ChatNotFoundError) as exc_info:
        await chat_service.get(fake_id)

    assert exc_info.value.chat_id == fake_id


@pytest.mark.anyio
async def test_list_chats_pagination_offset(chat_service: ChatService) -> None:
    """Test that list pagination calculates offset correctly."""
    for i in range(5):
        await chat_service.create(ChatCreate(title=f"Chat {i}"))

    chats, total = await chat_service.list(page=2, page_size=2)

    assert total == 5
    assert len(chats) == 2


@pytest.mark.anyio
async def test_list_chats_ordered_by_created_at_desc(
    chat_service: ChatService,
) -> None:
    """Test that list returns chats ordered by created_at descending."""
    await chat_service.create(ChatCreate(title="First"))
    await chat_service.create(ChatCreate(title="Second"))
    await chat_service.create(ChatCreate(title="Third"))

    chats, _ = await chat_service.list()

    assert chats[0].title == "Third"
    assert chats[1].title == "Second"
    assert chats[2].title == "First"


@pytest.mark.anyio
async def test_update_partial_fields(chat_service: ChatService) -> None:
    """Test that update only changes non-None fields."""
    chat = await chat_service.create(
        ChatCreate(title="Original", metadata={"original": True})
    )

    updated = await chat_service.update(
        chat.id,
        ChatUpdate(title="Updated"),
    )

    assert updated.title == "Updated"
    assert updated.metadata_ == {"original": True}


@pytest.mark.anyio
async def test_update_metadata_only(chat_service: ChatService) -> None:
    """Test updating only metadata."""
    chat = await chat_service.create(ChatCreate(title="Keep This"))

    updated = await chat_service.update(
        chat.id,
        ChatUpdate(metadata={"new": "data"}),
    )

    assert updated.title == "Keep This"
    assert updated.metadata_ == {"new": "data"}


@pytest.mark.anyio
async def test_delete_not_found(chat_service: ChatService) -> None:
    """Test deleting a non-existent chat raises ChatNotFoundError."""
    fake_id = uuid4()

    with pytest.raises(ChatNotFoundError):
        await chat_service.delete(fake_id)


@pytest.mark.anyio
async def test_delete_success(chat_service: ChatService) -> None:
    """Test successful chat deletion."""
    chat = await chat_service.create(ChatCreate())

    await chat_service.delete(chat.id)

    with pytest.raises(ChatNotFoundError):
        await chat_service.get(chat.id)
