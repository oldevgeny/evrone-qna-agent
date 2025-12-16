"""Knowledge base domain exceptions."""

from qna_agent.exceptions import KnowledgeBaseError


class FileNotFoundInKnowledgeBaseError(KnowledgeBaseError):
    """Raised when a file is not found in the knowledge base."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(f"File '{filename}' not found in knowledge base")


class KnowledgeBaseReadError(KnowledgeBaseError):
    """Raised when reading from knowledge base fails."""

    def __init__(self, filename: str, reason: str) -> None:
        self.filename = filename
        super().__init__(f"Failed to read '{filename}': {reason}")
