"""Standalone mock LLM server for load testing.

This server mimics the OpenAI API format to allow load testing
the application without incurring LLM API costs or dealing with
external service latency variability.

Run with: uv run uvicorn loadtests.mock_llm_server:app --host 0.0.0.0 --port 8001
"""

import asyncio
import os
import uuid
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Mock LLM Server",
    description="OpenAI-compatible mock server for load testing",
    version="1.0.0",
)


class ChatMessage(BaseModel):
    """Chat message in OpenAI format."""

    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str
    messages: list[ChatMessage]
    tools: list[dict[str, Any]] | None = None
    temperature: float = 0.7
    max_tokens: int = 4096


class ChatCompletionChoice(BaseModel):
    """Single choice in completion response."""

    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str
    object: str = "chat.completion"
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage


MOCK_DELAY_MS = int(os.getenv("MOCK_LLM_DELAY_MS", "100"))
MOCK_RESPONSE = os.getenv(
    "MOCK_LLM_RESPONSE",
    "This is a mocked AI response for load testing purposes.",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """Handle chat completion with simulated delay.

    This endpoint mimics the OpenAI chat completions API format,
    returning a canned response after a configurable delay.
    """
    await asyncio.sleep(MOCK_DELAY_MS / 1000)

    prompt_tokens = sum(len(str(m.content or "")) // 4 for m in request.messages)
    completion_tokens = len(MOCK_RESPONSE) // 4

    return ChatCompletionResponse(
        id=f"chatcmpl-mock-{uuid.uuid4().hex[:12]}",
        model=request.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=MOCK_RESPONSE,
                ),
                finish_reason="stop",
            ),
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
