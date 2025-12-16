"""Pytest fixtures for async testing."""

from collections.abc import AsyncGenerator
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from qna_agent.agent.service import AgentResponse
from qna_agent.database import get_session
from qna_agent.main import app
from qna_agent.models import Base

# Test constants
FAKE_UUID = "01930000-0000-7000-8000-000000000000"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest.fixture
async def async_engine() -> AsyncGenerator[Any]:
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session(
    async_engine: Any,
) -> AsyncGenerator[AsyncSession]:
    """Create an async session for testing."""
    async_session_factory = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Create an async HTTP client for testing."""

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def created_chat(client: AsyncClient) -> dict[str, Any]:
    """Create a chat and return its response data."""
    response = await client.post("/api/v1/chats", json={})
    return response.json()


@pytest.fixture
def mock_agent_response() -> AgentResponse:
    """Create a default mock agent response."""
    return AgentResponse(content="Mocked response")


@contextmanager
def mock_agent_service(response: AgentResponse | None = None):
    """Context manager to mock AgentService.process_message."""
    mock_response = response or AgentResponse(content="Mocked response")
    with patch(
        "qna_agent.agent.service.AgentService.process_message",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock:
        yield mock
