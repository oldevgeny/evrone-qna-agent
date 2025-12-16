"""LiteLLM client wrapper with Langfuse integration."""

import os
from typing import Any

import litellm
from litellm import ModelResponse, acompletion  # type: ignore[attr-defined]
from loguru import logger

from qna_agent.agent.config import get_agent_settings
from qna_agent.agent.exceptions import LLMConnectionError, LLMResponseError


class LLMClient:
    """LiteLLM client with Langfuse observability."""

    def __init__(self) -> None:
        self._settings = get_agent_settings()
        self._configure_langfuse()

    def _configure_langfuse(self) -> None:
        """Configure Langfuse callbacks for LLM observability."""
        if self._settings.langfuse_public_key and self._settings.langfuse_secret_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = self._settings.langfuse_public_key
            os.environ["LANGFUSE_SECRET_KEY"] = self._settings.langfuse_secret_key
            os.environ["LANGFUSE_HOST"] = self._settings.langfuse_host

            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]
            logger.info("Langfuse observability enabled")
        else:
            logger.warning(
                "Langfuse credentials not configured, observability disabled"
            )

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        chat_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request to the LLM.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tool definitions
            chat_id: Optional chat ID for Langfuse tracing

        Returns:
            The LLM response

        Raises:
            LLMConnectionError: If connection to LLM fails
            LLMResponseError: If LLM returns an invalid response
        """
        try:
            kwargs: dict[str, Any] = {
                "model": self._settings.litellm_model,
                "messages": messages,
                "api_base": self._settings.litellm_api_base,
                "api_key": self._settings.litellm_api_key,
                "temperature": self._settings.temperature,
                "max_tokens": self._settings.max_tokens,
            }

            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            if chat_id:
                kwargs["metadata"] = {
                    "trace_user_id": chat_id,
                    "session_id": chat_id,
                    "generation_name": "qna-agent",
                }

            response: ModelResponse = await acompletion(**kwargs)  # type: ignore[assignment]

            if not response or not response.choices:
                raise LLMResponseError("Empty response from LLM")

            return response.model_dump()

        except litellm.exceptions.APIConnectionError as e:
            logger.error(f"LLM connection error: {e}")
            raise LLMConnectionError(f"Failed to connect to LLM: {e}") from e
        except litellm.exceptions.APIError as e:
            logger.error(f"LLM API error: {e}")
            raise LLMResponseError(f"LLM API error: {e}") from e
