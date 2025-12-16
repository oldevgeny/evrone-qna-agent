"""Pydantic schemas for events domain."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


class EventPayload(BaseModel):
    """Base event payload schema."""

    event_type: str = Field(description="Type of event")
    data: dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="Event timestamp",
    )


class ChatEvent(EventPayload):
    """Chat-specific event."""

    chat_id: UUID = Field(description="Chat ID this event belongs to")


class MessageCreatedEvent(ChatEvent):
    """Event emitted when a new message is created."""

    event_type: str = "message.created"
    message_id: UUID = Field(description="ID of the created message")
    role: str = Field(description="Message role (user, assistant, etc.)")


class AgentProcessingEvent(ChatEvent):
    """Event emitted when agent is processing."""

    event_type: str = "agent.processing"
    status: str = Field(description="Processing status")
