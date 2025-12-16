"""Pydantic schemas for chats domain."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    """Schema for creating a new chat."""

    title: str | None = Field(
        default=None,
        max_length=255,
        description="Optional title for the chat session",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the chat",
    )


class ChatUpdate(BaseModel):
    """Schema for updating a chat."""

    title: str | None = Field(
        default=None,
        max_length=255,
        description="New title for the chat session",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Updated metadata for the chat",
    )


class ChatResponse(BaseModel):
    """Schema for chat response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique chat identifier (UUID7)")
    title: str | None = Field(description="Chat title")
    metadata: dict[str, Any] = Field(
        description="Additional metadata for the chat",
        validation_alias="metadata_",
    )
    created_at: datetime = Field(description="Chat creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ChatListResponse(BaseModel):
    """Schema for paginated chat list response."""

    items: list[ChatResponse] = Field(description="List of chats")
    total: int = Field(ge=0, description="Total number of chats")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")
