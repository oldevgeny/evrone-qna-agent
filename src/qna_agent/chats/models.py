"""Chat SQLAlchemy model."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qna_agent.models import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from qna_agent.messages.models import Message


class Chat(Base, UUIDMixin, TimestampMixin):
    """Chat session model."""

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        default=dict,
        nullable=False,
    )

    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title={self.title!r})>"
