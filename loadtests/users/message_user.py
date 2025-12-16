"""Message and AI conversation user scenarios."""

import random

from locust import task

from loadtests.users.base import BaseAPIUser

SAMPLE_MESSAGES = [
    "What is the capital of France?",
    "Explain quantum computing in simple terms.",
    "List the files in the knowledge base.",
    "Search for information about machine learning.",
    "What can you help me with?",
    "Summarize the key points from the documentation.",
    "How do I get started with this system?",
    "What topics are covered in the knowledge base?",
    "Tell me about the Council of Architects.",
    "What are the main threats to the multiverse?",
]


class MessageUser(BaseAPIUser):
    """User that focuses on message/conversation endpoints.

    This represents the critical path - users who actively engage in
    conversations with the AI agent. These requests involve LLM calls
    (or mocked LLM calls) and are the most resource-intensive.
    """

    weight = 5  # Higher weight - this is the critical path

    def on_start(self) -> None:
        """Create initial chat for messaging."""
        super().on_start()
        self.create_chat(title="Message User Chat")

    @task(10)
    def send_message(self) -> None:
        """Send a message and receive AI response (critical path).

        This is the most important endpoint to test as it involves
        the full agent processing pipeline.
        """
        chat_id = self.get_random_chat_id()
        if not chat_id:
            return

        message = random.choice(SAMPLE_MESSAGES)

        with self.client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"content": message},
            name="/api/v1/chats/{chat_id}/messages [POST]",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                data = response.json()
                if "assistant_message" in data and "user_message" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(5)
    def list_messages(self) -> None:
        """Get message history for a chat."""
        chat_id = self.get_random_chat_id()
        if not chat_id:
            return

        self.client.get(
            f"/api/v1/chats/{chat_id}/messages",
            name="/api/v1/chats/{chat_id}/messages [GET]",
        )

    @task(2)
    def create_new_chat(self) -> None:
        """Occasionally create new chat sessions."""
        self.create_chat(title=f"Conversation {random.randint(1, 1000)}")
