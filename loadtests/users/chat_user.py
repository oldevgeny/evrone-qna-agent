"""Chat-focused user scenarios."""

import random

from locust import task

from loadtests.users.base import BaseAPIUser


class ChatUser(BaseAPIUser):
    """User that primarily interacts with chat endpoints.

    Simulates users who create, browse, update, and manage chat sessions
    without necessarily sending many messages.
    """

    weight = 3  # Relative weight for mixed scenarios

    @task(5)
    def create_chat(self) -> None:
        """Create a new chat session."""
        title = f"Load Test Chat {random.randint(1, 10000)}"
        super().create_chat(title=title)

    @task(10)
    def list_chats(self) -> None:
        """List chats with pagination."""
        page = random.randint(1, 5)
        page_size = random.choice([10, 20, 50])

        self.client.get(
            f"/api/v1/chats?page={page}&page_size={page_size}",
            name="/api/v1/chats [GET]",
        )

    @task(8)
    def get_chat(self) -> None:
        """Get a specific chat by ID."""
        chat_id = self.get_random_chat_id()
        if not chat_id:
            return

        self.client.get(
            f"/api/v1/chats/{chat_id}",
            name="/api/v1/chats/{chat_id} [GET]",
        )

    @task(2)
    def update_chat(self) -> None:
        """Update a chat's title."""
        chat_id = self.get_random_chat_id()
        if not chat_id:
            return

        self.client.patch(
            f"/api/v1/chats/{chat_id}",
            json={"title": f"Updated Title {random.randint(1, 1000)}"},
            name="/api/v1/chats/{chat_id} [PATCH]",
        )

    @task(1)
    def delete_chat(self) -> None:
        """Delete a chat."""
        if not self.chat_ids:
            return

        chat_id = self.chat_ids.pop()
        self.client.delete(
            f"/api/v1/chats/{chat_id}",
            name="/api/v1/chats/{chat_id} [DELETE]",
        )
