"""Message domain dependencies for FastAPI."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from qna_agent.database import get_session
from qna_agent.messages.service import MessageService


async def get_message_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MessageService:
    """Dependency to get message service."""
    return MessageService(session)
