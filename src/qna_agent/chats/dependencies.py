"""Chat domain dependencies for FastAPI."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from qna_agent.chats.models import Chat
from qna_agent.chats.service import ChatService
from qna_agent.database import get_session


async def get_chat_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChatService:
    """Dependency to get chat service."""
    return ChatService(session)


async def valid_chat_id(
    chat_id: Annotated[UUID, Path(description="Chat ID")],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> Chat:
    """Dependency that validates chat exists and returns it."""
    return await service.get(chat_id)
