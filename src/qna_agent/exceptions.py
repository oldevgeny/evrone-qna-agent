"""Base exception classes for QnA Agent API."""


class QnAAgentError(Exception):
    """Base exception for all QnA Agent errors."""


class NotFoundError(QnAAgentError):
    """Resource not found."""


class ValidationError(QnAAgentError):
    """Validation failed."""


class LLMError(QnAAgentError):
    """LLM-related error."""


class KnowledgeBaseError(QnAAgentError):
    """Knowledge base operation error."""
