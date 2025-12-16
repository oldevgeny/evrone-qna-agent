"""Message API router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from qna_agent.agent.dependencies import get_agent_service
from qna_agent.agent.service import AgentService
from qna_agent.chats.dependencies import valid_chat_id
from qna_agent.chats.models import Chat
from qna_agent.messages.dependencies import get_message_service
from qna_agent.messages.models import MessageRole
from qna_agent.messages.schemas import (
    ChatCompletionResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from qna_agent.messages.service import MessageService

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.get(
    "",
    response_model=MessageListResponse,
    summary="Get chat messages",
    description="Get all messages for a specific chat session.",
)
async def list_messages(
    chat: Annotated[Chat, Depends(valid_chat_id)],
    service: Annotated[MessageService, Depends(get_message_service)],
) -> MessageListResponse:
    """Get all messages for a chat."""
    messages = await service.get_chat_messages(chat.id)
    total = len(messages)

    return MessageListResponse(
        items=[MessageResponse.model_validate(msg) for msg in messages],
        total=total,
    )


@router.post(
    "",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message and get AI response",
    description="Send a user message and receive an AI-generated response.",
)
async def create_message(
    chat_id: UUID,
    data: MessageCreate,
    chat: Annotated[Chat, Depends(valid_chat_id)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> ChatCompletionResponse:
    """Send a message and get AI response."""
    user_message = await message_service.create(
        chat_id=chat_id,
        role=MessageRole.USER,
        content=data.content,
    )

    history = await message_service.get_chat_history_for_llm(chat_id)
    assistant_response = await agent_service.process_message(
        chat_id=chat_id,
        messages=history,
    )

    assistant_message = await message_service.create(
        chat_id=chat_id,
        role=MessageRole.ASSISTANT,
        content=assistant_response.content,
    )

    return ChatCompletionResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
    )
