"""Chat domain exceptions."""

from uuid import UUID

from qna_agent.exceptions import NotFoundError


class ChatNotFoundError(NotFoundError):
    """Raised when a chat is not found."""

    def __init__(self, chat_id: UUID) -> None:
        self.chat_id = chat_id
        super().__init__(f"Chat {chat_id} not found")
