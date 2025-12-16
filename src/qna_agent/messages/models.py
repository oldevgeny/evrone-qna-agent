"""Message SQLAlchemy model."""

from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qna_agent.models import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from qna_agent.chats.models import Chat


class MessageRole(StrEnum):
    """Message role enum matching OpenAI API."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(Base, UUIDMixin, TimestampMixin):
    """Chat message model."""

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    tool_call_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    chat: Mapped[Chat] = relationship("Chat", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, chat_id={self.chat_id})>"

    def to_openai_format(self) -> dict[str, Any]:
        """Convert message to OpenAI API format for LLM history.

        Note: tool_calls are excluded because we don't persist
        the corresponding tool response messages. Including tool_calls
        without tool responses would cause OpenAI API validation errors.
        Tool calls are still stored in the database for audit/debugging.
        """
        msg: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        return msg
