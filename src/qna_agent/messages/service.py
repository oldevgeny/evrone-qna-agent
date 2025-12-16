"""Message service with business logic."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from qna_agent.messages.models import Message, MessageRole


class MessageService:
    """Service for message operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        chat_id: UUID,
        role: MessageRole,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_call_id: str | None = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def get_chat_messages(
        self,
        chat_id: UUID,
        limit: int | None = None,
    ) -> list[Message]:
        """Get all messages for a chat, ordered by creation time."""
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
        )
        if limit:
            query = query.limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_chat_messages(self, chat_id: UUID) -> int:
        """Count messages in a chat."""
        result = await self._session.execute(
            select(func.count()).select_from(Message).where(Message.chat_id == chat_id)
        )
        return result.scalar_one()

    async def get_chat_history_for_llm(
        self,
        chat_id: UUID,
        max_messages: int = 50,
    ) -> list[dict[str, Any]]:
        """Get chat history in OpenAI API format."""
        messages = await self.get_chat_messages(chat_id, limit=max_messages)
        return [msg.to_openai_format() for msg in messages]
