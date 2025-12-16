"""Agent domain exceptions."""

from qna_agent.exceptions import LLMError


class LLMConnectionError(LLMError):
    """Raised when connection to LLM fails."""


class LLMResponseError(LLMError):
    """Raised when LLM returns an invalid response."""


class ToolExecutionError(LLMError):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class MaxIterationsExceededError(LLMError):
    """Raised when agent exceeds maximum tool iterations."""

    def __init__(self, max_iterations: int) -> None:
        self.max_iterations = max_iterations
        super().__init__(f"Agent exceeded maximum iterations ({max_iterations})")
