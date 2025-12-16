"""SSE events router."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from qna_agent.chats.dependencies import valid_chat_id
from qna_agent.chats.models import Chat
from qna_agent.events.manager import event_manager

router = APIRouter(prefix="/chats/{chat_id}/events", tags=["events"])


async def event_generator(chat_id: UUID) -> AsyncGenerator[dict[str, str]]:
    """Generate SSE events for a chat."""
    queue = await event_manager.subscribe(chat_id)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield {
                    "event": event.get("event_type", "message"),
                    "data": json.dumps(event),
                }
            except TimeoutError:
                yield {"event": "ping", "data": ""}

    finally:
        await event_manager.unsubscribe(chat_id, queue)


@router.get(
    "",
    summary="Subscribe to chat events",
    description="Server-Sent Events stream for real-time chat updates.",
    response_class=EventSourceResponse,
)
async def subscribe_to_events(
    chat: Annotated[Chat, Depends(valid_chat_id)],
) -> EventSourceResponse:
    """Subscribe to SSE events for a chat."""
    return EventSourceResponse(event_generator(chat.id))
