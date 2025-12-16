"""Knowledge domain dependencies for FastAPI."""

from qna_agent.knowledge.service import KnowledgeService


def get_knowledge_service() -> KnowledgeService:
    """Dependency to get knowledge service."""
    return KnowledgeService()
