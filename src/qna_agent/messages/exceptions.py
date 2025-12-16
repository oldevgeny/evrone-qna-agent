"""Message domain exceptions."""

from uuid import UUID

from qna_agent.exceptions import NotFoundError


class MessageNotFoundError(NotFoundError):
    """Raised when a message is not found."""

    def __init__(self, message_id: UUID) -> None:
        self.message_id = message_id
        super().__init__(f"Message {message_id} not found")
