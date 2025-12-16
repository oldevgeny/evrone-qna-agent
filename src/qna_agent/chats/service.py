"""Chat service with business logic."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from qna_agent.chats.exceptions import ChatNotFoundError
from qna_agent.chats.models import Chat
from qna_agent.chats.schemas import ChatCreate, ChatUpdate


class ChatService:
    """Service for chat operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ChatCreate) -> Chat:
        """Create a new chat session."""
        chat = Chat(
            title=data.title,
            metadata_=data.metadata,
        )
        self._session.add(chat)
        await self._session.flush()
        await self._session.refresh(chat)
        return chat

    async def get(self, chat_id: UUID) -> Chat:
        """Get a chat by ID. Raises ChatNotFoundError if not found."""
        result = await self._session.execute(select(Chat).where(Chat.id == chat_id))
        chat = result.scalar_one_or_none()
        if chat is None:
            raise ChatNotFoundError(chat_id)
        return chat

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Chat], int]:
        """List chats with pagination. Returns (chats, total_count)."""
        offset = (page - 1) * page_size

        count_result = await self._session.execute(
            select(func.count()).select_from(Chat)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(Chat)
            .order_by(Chat.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        chats = list(result.scalars().all())

        return chats, total

    async def update(self, chat_id: UUID, data: ChatUpdate) -> Chat:
        """Update a chat. Raises ChatNotFoundError if not found."""
        chat = await self.get(chat_id)

        if data.title is not None:
            chat.title = data.title
        if data.metadata is not None:
            chat.metadata_ = data.metadata

        await self._session.flush()
        await self._session.refresh(chat)
        return chat

    async def delete(self, chat_id: UUID) -> None:
        """Delete a chat. Raises ChatNotFoundError if not found."""
        chat = await self.get(chat_id)
        await self._session.delete(chat)
        await self._session.flush()
