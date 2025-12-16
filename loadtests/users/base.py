"""Base user class with common functionality."""

from locust import HttpUser, between


class BaseAPIUser(HttpUser):
    """Base class for API users with common configuration.

    Provides shared functionality for all user classes including
    chat management helpers and common configuration.
    """

    abstract = True
    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Setup before starting tasks."""
        self.chat_ids: list[str] = []

    def create_chat(self, title: str | None = None) -> str | None:
        """Create a chat and return its ID.

        Args:
            title: Optional title for the chat.

        Returns:
            The chat ID if creation succeeded, None otherwise.
        """
        payload = {"title": title} if title else {}

        with self.client.post(
            "/api/v1/chats",
            json=payload,
            name="/api/v1/chats [POST]",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                chat_id = response.json().get("id")
                self.chat_ids.append(chat_id)
                response.success()
                return chat_id
            else:
                response.failure(f"Failed to create chat: {response.status_code}")
                return None

    def get_random_chat_id(self) -> str | None:
        """Get a random chat ID from the user's chats.

        Creates a new chat if none exist.

        Returns:
            A chat ID or None if creation failed.
        """
        if not self.chat_ids:
            return self.create_chat()
        import random

        return random.choice(self.chat_ids)
