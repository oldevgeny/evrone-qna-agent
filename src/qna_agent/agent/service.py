"""Agent service with tool calling loop."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from litellm.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    ServiceUnavailableError,
)
from loguru import logger

from qna_agent.agent.client import LLMClient
from qna_agent.agent.config import get_agent_settings
from qna_agent.agent.exceptions import (
    LLMConnectionError,
    MaxIterationsExceededError,
    ToolExecutionError,
)
from qna_agent.agent.tools import SYSTEM_PROMPT, TOOLS
from qna_agent.knowledge.service import KnowledgeService


@dataclass
class AgentResponse:
    """Response from the agent."""

    content: str
    tool_calls: list[dict[str, Any]] | None = None


class AgentService:
    """Agent service with tool calling capabilities."""

    def __init__(
        self,
        llm_client: LLMClient,
        knowledge_service: KnowledgeService,
    ) -> None:
        self._llm = llm_client
        self._knowledge = knowledge_service
        self._settings = get_agent_settings()

    async def process_message(
        self,
        chat_id: UUID,
        messages: list[dict[str, Any]],
    ) -> AgentResponse:
        """Process a message through the agent with tool calling.

        Args:
            chat_id: The chat ID for tracing
            messages: Chat history in OpenAI format

        Returns:
            AgentResponse with the assistant's response

        Raises:
            MaxIterationsExceededError: If max tool iterations exceeded
        """
        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages,
        ]

        all_tool_calls: list[dict[str, Any]] = []

        for iteration in range(self._settings.max_tool_iterations):
            logger.debug(f"Agent iteration {iteration + 1}")

            try:
                response = await self._llm.chat_completion(
                    messages=full_messages,
                    tools=TOOLS,
                    chat_id=str(chat_id),
                )
            except AuthenticationError as e:
                logger.error(f"LLM authentication failed: {e}")
                raise LLMConnectionError(
                    "LLM service authentication failed. Check API key configuration."
                ) from e
            except RateLimitError as e:
                logger.error(f"LLM rate limit exceeded: {e}")
                raise LLMConnectionError(
                    "LLM service rate limit exceeded. Please try again later."
                ) from e
            except ServiceUnavailableError as e:
                logger.error(f"LLM service unavailable: {e}")
                raise LLMConnectionError(
                    "LLM service is temporarily unavailable."
                ) from e
            except BadRequestError as e:
                logger.error(f"LLM bad request: {e}")
                raise LLMConnectionError(f"LLM request failed: {e}") from e

            choice = response["choices"][0]
            message = choice["message"]

            if choice.get("finish_reason") == "tool_calls" or message.get("tool_calls"):
                tool_calls = message.get("tool_calls", [])
                all_tool_calls.extend(tool_calls)

                full_messages.append(message)

                tool_results = await self._execute_tools(tool_calls)
                full_messages.extend(tool_results)
            else:
                return AgentResponse(
                    content=message.get("content", ""),
                    tool_calls=all_tool_calls if all_tool_calls else None,
                )

        raise MaxIterationsExceededError(self._settings.max_tool_iterations)

    async def _execute_tools(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Execute tool calls in parallel and return results."""
        tasks = [self._execute_tool(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        tool_messages: list[dict[str, Any]] = []
        for tool_call, result in zip(tool_calls, results, strict=True):
            if isinstance(result, Exception):
                content = f"Error: {result}"
                logger.error(f"Tool execution failed: {result}")
            else:
                content = result

            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": content,
                }
            )

        return tool_messages

    async def _execute_tool(self, tool_call: dict[str, Any]) -> str:
        """Execute a single tool call and return the result."""
        function = tool_call.get("function", {})
        name = function.get("name", "")
        arguments_str = function.get("arguments", "{}")

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            raise ToolExecutionError(name, f"Invalid arguments: {e}") from e

        logger.debug(f"Executing tool: {name} with args: {arguments}")

        match name:
            case "search_knowledge_base":
                query = arguments.get("query", "")
                results = await self._knowledge.search(query)
                return json.dumps(results)

            case "list_knowledge_files":
                files = await self._knowledge.list_files()
                return json.dumps(files)

            case "read_knowledge_file":
                filename = arguments.get("filename", "")
                content = await self._knowledge.read_file(filename)
                return content

            case _:
                raise ToolExecutionError(name, "Unknown tool")
