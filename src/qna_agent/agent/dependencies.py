"""Agent domain dependencies for FastAPI."""

from typing import Annotated

from fastapi import Depends

from qna_agent.agent.client import LLMClient
from qna_agent.agent.service import AgentService
from qna_agent.knowledge.dependencies import get_knowledge_service
from qna_agent.knowledge.service import KnowledgeService


def get_llm_client() -> LLMClient:
    """Dependency to get LLM client."""
    return LLMClient()


async def get_agent_service(
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> AgentService:
    """Dependency to get agent service."""
    return AgentService(
        llm_client=llm_client,
        knowledge_service=knowledge_service,
    )
