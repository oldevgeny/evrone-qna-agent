"""Tests for MessageService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from qna_agent.chats.models import Chat
from qna_agent.messages.models import MessageRole
from qna_agent.messages.service import MessageService


@pytest.fixture
async def chat_in_db(async_session: AsyncSession) -> Chat:
    """Create a chat in the database for message tests."""
    chat = Chat(title="Test Chat")
    async_session.add(chat)
    await async_session.flush()
    await async_session.refresh(chat)
    return chat


@pytest.fixture
def message_service(async_session: AsyncSession) -> MessageService:
    """Create MessageService with test session."""
    return MessageService(async_session)


@pytest.mark.anyio
async def test_create_message_with_role(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test creating messages with different roles."""
    for role in MessageRole:
        message = await message_service.create(
            chat_id=chat_in_db.id,
            role=role,
            content=f"Test {role.value} message",
        )

        assert message.id is not None
        assert message.role == role
        assert message.chat_id == chat_in_db.id


@pytest.mark.anyio
async def test_create_message_with_tool_calls(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test creating a message with tool calls."""
    tool_calls = [{"id": "call_1", "function": {"name": "test"}}]

    message = await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.ASSISTANT,
        content="",
        tool_calls=tool_calls,
    )

    assert message.tool_calls == tool_calls


@pytest.mark.anyio
async def test_get_chat_messages_ordered(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test that messages are returned in ASC order by created_at."""
    await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.USER,
        content="First",
    )
    await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.ASSISTANT,
        content="Second",
    )
    await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.USER,
        content="Third",
    )

    messages = await message_service.get_chat_messages(chat_in_db.id)

    assert len(messages) == 3
    assert messages[0].content == "First"
    assert messages[1].content == "Second"
    assert messages[2].content == "Third"


@pytest.mark.anyio
async def test_get_chat_history_for_llm_format(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test that get_chat_history_for_llm returns OpenAI format."""
    await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.USER,
        content="Hello",
    )
    await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.ASSISTANT,
        content="Hi there!",
    )

    history = await message_service.get_chat_history_for_llm(chat_in_db.id)

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hello"}
    assert history[1] == {"role": "assistant", "content": "Hi there!"}


@pytest.mark.anyio
async def test_get_chat_history_limit(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test that get_chat_history_for_llm respects max_messages."""
    for i in range(10):
        await message_service.create(
            chat_id=chat_in_db.id,
            role=MessageRole.USER,
            content=f"Message {i}",
        )

    history = await message_service.get_chat_history_for_llm(
        chat_in_db.id,
        max_messages=5,
    )

    assert len(history) == 5


@pytest.mark.anyio
async def test_count_chat_messages(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test counting messages in a chat."""
    for _ in range(5):
        await message_service.create(
            chat_id=chat_in_db.id,
            role=MessageRole.USER,
            content="Test",
        )

    count = await message_service.count_chat_messages(chat_in_db.id)

    assert count == 5


@pytest.mark.anyio
async def test_count_chat_messages_empty(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test counting messages in an empty chat."""
    count = await message_service.count_chat_messages(chat_in_db.id)

    assert count == 0


@pytest.mark.anyio
async def test_get_chat_history_includes_tool_calls(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test that OpenAI format includes tool_calls when present."""
    tool_calls = [{"id": "call_1", "function": {"name": "test"}}]

    await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.ASSISTANT,
        content="Using tool",
        tool_calls=tool_calls,
    )

    history = await message_service.get_chat_history_for_llm(chat_in_db.id)

    assert history[0]["tool_calls"] == tool_calls


@pytest.mark.anyio
async def test_get_chat_history_includes_tool_call_id(
    message_service: MessageService,
    chat_in_db: Chat,
) -> None:
    """Test that OpenAI format includes tool_call_id when present."""
    await message_service.create(
        chat_id=chat_in_db.id,
        role=MessageRole.TOOL,
        content="Tool result",
        tool_call_id="call_1",
    )

    history = await message_service.get_chat_history_for_llm(chat_in_db.id)

    assert history[0]["tool_call_id"] == "call_1"
