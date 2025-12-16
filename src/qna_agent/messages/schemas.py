"""Pydantic schemas for messages domain."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from qna_agent.messages.models import MessageRole


class MessageBase(BaseModel):
    """Base message schema with common fields."""

    role: MessageRole = Field(
        description="Message role (user, assistant, system, tool)"
    )
    content: str = Field(min_length=1, description="Message content")


class MessageCreate(BaseModel):
    """Schema for creating a new user message."""

    content: str = Field(
        min_length=1, max_length=32000, description="User message content"
    )


class MessageResponse(MessageBase):
    """Schema for message response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique message identifier (UUID7)")
    chat_id: UUID = Field(description="Parent chat ID")
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None,
        description="Tool calls made by assistant",
    )
    tool_call_id: str | None = Field(
        default=None,
        description="Tool call ID for tool response messages",
    )
    created_at: datetime = Field(description="Message creation timestamp")


class MessageListResponse(BaseModel):
    """Schema for message list response."""

    items: list[MessageResponse] = Field(description="List of messages")
    total: int = Field(ge=0, description="Total number of messages")


class ChatCompletionResponse(BaseModel):
    """Schema for chat completion response with AI message."""

    user_message: MessageResponse = Field(description="The user's message")
    assistant_message: MessageResponse = Field(
        description="The AI assistant's response"
    )
