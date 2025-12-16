"""Chat API router."""

import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from qna_agent.chats.dependencies import get_chat_service, valid_chat_id
from qna_agent.chats.models import Chat
from qna_agent.chats.schemas import (
    ChatCreate,
    ChatListResponse,
    ChatResponse,
    ChatUpdate,
)
from qna_agent.chats.service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat",
    description="Create a new chat session. Returns the created chat.",
)
async def create_chat(
    data: ChatCreate,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> Chat:
    """Create a new chat session."""
    return await service.create(data)


@router.get(
    "",
    response_model=ChatListResponse,
    summary="List all chats",
    description="Get a paginated list of all chat sessions.",
)
async def list_chats(
    service: Annotated[ChatService, Depends(get_chat_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> ChatListResponse:
    """List all chat sessions with pagination."""
    chats, total = await service.list(page=page, page_size=page_size)
    pages = math.ceil(total / page_size) if total > 0 else 0

    return ChatListResponse(
        items=[ChatResponse.model_validate(chat) for chat in chats],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
    summary="Get chat details",
    description="Get details of a specific chat session.",
)
async def get_chat(
    chat: Annotated[Chat, Depends(valid_chat_id)],
) -> Chat:
    """Get a chat session by ID."""
    return chat


@router.patch(
    "/{chat_id}",
    response_model=ChatResponse,
    summary="Update chat",
    description="Update a chat session's title or metadata.",
)
async def update_chat(
    chat_id: UUID,
    data: ChatUpdate,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> Chat:
    """Update a chat session."""
    return await service.update(chat_id, data)


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete chat",
    description="Delete a chat session and all its messages.",
)
async def delete_chat(
    chat_id: UUID,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> None:
    """Delete a chat session."""
    await service.delete(chat_id)
