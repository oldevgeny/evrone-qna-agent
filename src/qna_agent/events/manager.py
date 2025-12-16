"""Event manager for SSE pub/sub."""

import asyncio
from collections import defaultdict
from typing import Any
from uuid import UUID

from loguru import logger


class EventManager:
    """Manager for Server-Sent Events pub/sub."""

    def __init__(self) -> None:
        self._subscribers: dict[UUID, list[asyncio.Queue[dict[str, Any]]]] = (
            defaultdict(list)
        )
        self._lock = asyncio.Lock()

    async def subscribe(self, chat_id: UUID) -> asyncio.Queue[dict[str, Any]]:
        """Subscribe to events for a specific chat.

        Args:
            chat_id: The chat ID to subscribe to

        Returns:
            An asyncio Queue that will receive events
        """
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async with self._lock:
            self._subscribers[chat_id].append(queue)
            logger.debug(f"New subscriber for chat {chat_id}")

        return queue

    async def unsubscribe(
        self,
        chat_id: UUID,
        queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        """Unsubscribe from events for a specific chat.

        Args:
            chat_id: The chat ID to unsubscribe from
            queue: The queue to remove
        """
        async with self._lock:
            if chat_id in self._subscribers:
                try:
                    self._subscribers[chat_id].remove(queue)
                    logger.debug(f"Unsubscribed from chat {chat_id}")
                except ValueError:
                    pass

                if not self._subscribers[chat_id]:
                    del self._subscribers[chat_id]

    async def publish(self, chat_id: UUID, event: dict[str, Any]) -> None:
        """Publish an event to all subscribers of a chat.

        Args:
            chat_id: The chat ID to publish to
            event: The event data to publish
        """
        async with self._lock:
            subscribers = self._subscribers.get(chat_id, [])

        for queue in subscribers:
            try:
                await queue.put(event)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for chat {chat_id}, event dropped")


event_manager = EventManager()
