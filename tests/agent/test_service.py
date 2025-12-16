"""Tests for AgentService."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from qna_agent.agent.exceptions import MaxIterationsExceededError, ToolExecutionError
from qna_agent.agent.service import AgentResponse, AgentService


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    return MagicMock()


@pytest.fixture
def mock_knowledge_service() -> MagicMock:
    """Create a mock knowledge service."""
    return MagicMock()


@pytest.fixture
def agent_service(
    mock_llm_client: MagicMock,
    mock_knowledge_service: MagicMock,
) -> AgentService:
    """Create AgentService with mocked dependencies."""
    with patch("qna_agent.agent.service.get_agent_settings") as mock_settings:
        mock_settings.return_value.max_tool_iterations = 10
        return AgentService(mock_llm_client, mock_knowledge_service)


@pytest.mark.anyio
async def test_process_message_simple_response(
    agent_service: AgentService,
    mock_llm_client: MagicMock,
) -> None:
    """Test processing a message with no tool calls."""
    mock_llm_client.chat_completion = AsyncMock(
        return_value={
            "choices": [
                {
                    "message": {"content": "Hello!"},
                    "finish_reason": "stop",
                }
            ]
        }
    )

    response = await agent_service.process_message(
        chat_id=uuid4(),
        messages=[{"role": "user", "content": "Hi"}],
    )

    assert isinstance(response, AgentResponse)
    assert response.content == "Hello!"
    assert response.tool_calls is None


@pytest.mark.anyio
async def test_process_message_with_tool_calls(
    agent_service: AgentService,
    mock_llm_client: MagicMock,
    mock_knowledge_service: MagicMock,
) -> None:
    """Test processing a message that requires tool calls."""
    mock_knowledge_service.list_files = AsyncMock(
        return_value=[{"filename": "test.txt", "size": 100}]
    )

    mock_llm_client.chat_completion = AsyncMock(
        side_effect=[
            {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "function": {
                                        "name": "list_knowledge_files",
                                        "arguments": "{}",
                                    },
                                }
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {"content": "Found files!"},
                        "finish_reason": "stop",
                    }
                ]
            },
        ]
    )

    response = await agent_service.process_message(
        chat_id=uuid4(),
        messages=[{"role": "user", "content": "List files"}],
    )

    assert response.content == "Found files!"
    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1


@pytest.mark.anyio
async def test_process_message_max_iterations(
    mock_llm_client: MagicMock,
    mock_knowledge_service: MagicMock,
) -> None:
    """Test that MaxIterationsExceededError is raised after too many tool calls."""
    with patch("qna_agent.agent.service.get_agent_settings") as mock_settings:
        mock_settings.return_value.max_tool_iterations = 2
        service = AgentService(mock_llm_client, mock_knowledge_service)

    mock_knowledge_service.list_files = AsyncMock(return_value=[])

    mock_llm_client.chat_completion = AsyncMock(
        return_value={
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "function": {
                                    "name": "list_knowledge_files",
                                    "arguments": "{}",
                                },
                            }
                        ]
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
    )

    with pytest.raises(MaxIterationsExceededError) as exc_info:
        await service.process_message(
            chat_id=uuid4(),
            messages=[{"role": "user", "content": "List files"}],
        )

    assert exc_info.value.max_iterations == 2


@pytest.mark.anyio
async def test_execute_tool_search_knowledge(
    agent_service: AgentService,
    mock_knowledge_service: MagicMock,
) -> None:
    """Test executing search_knowledge_base tool."""
    mock_knowledge_service.search = AsyncMock(
        return_value=[{"filename": "test.txt", "snippet": "...test..."}]
    )

    result = await agent_service._execute_tool(
        {
            "id": "call_1",
            "function": {
                "name": "search_knowledge_base",
                "arguments": '{"query": "test"}',
            },
        }
    )

    assert "test.txt" in result
    mock_knowledge_service.search.assert_called_once_with("test")


@pytest.mark.anyio
async def test_execute_tool_list_files(
    agent_service: AgentService,
    mock_knowledge_service: MagicMock,
) -> None:
    """Test executing list_knowledge_files tool."""
    mock_knowledge_service.list_files = AsyncMock(
        return_value=[{"filename": "doc.md", "size": 500}]
    )

    result = await agent_service._execute_tool(
        {
            "id": "call_1",
            "function": {
                "name": "list_knowledge_files",
                "arguments": "{}",
            },
        }
    )

    assert "doc.md" in result
    mock_knowledge_service.list_files.assert_called_once()


@pytest.mark.anyio
async def test_execute_tool_read_file(
    agent_service: AgentService,
    mock_knowledge_service: MagicMock,
) -> None:
    """Test executing read_knowledge_file tool."""
    mock_knowledge_service.read_file = AsyncMock(return_value="File content here")

    result = await agent_service._execute_tool(
        {
            "id": "call_1",
            "function": {
                "name": "read_knowledge_file",
                "arguments": '{"filename": "test.txt"}',
            },
        }
    )

    assert result == "File content here"
    mock_knowledge_service.read_file.assert_called_once_with("test.txt")


@pytest.mark.anyio
async def test_execute_tool_unknown(agent_service: AgentService) -> None:
    """Test executing an unknown tool raises ToolExecutionError."""
    with pytest.raises(ToolExecutionError) as exc_info:
        await agent_service._execute_tool(
            {
                "id": "call_1",
                "function": {
                    "name": "unknown_tool",
                    "arguments": "{}",
                },
            }
        )

    assert "Unknown tool" in str(exc_info.value)


@pytest.mark.anyio
async def test_execute_tool_invalid_json(agent_service: AgentService) -> None:
    """Test executing a tool with invalid JSON arguments."""
    with pytest.raises(ToolExecutionError) as exc_info:
        await agent_service._execute_tool(
            {
                "id": "call_1",
                "function": {
                    "name": "search_knowledge_base",
                    "arguments": "not valid json",
                },
            }
        )

    assert "Invalid arguments" in str(exc_info.value)
