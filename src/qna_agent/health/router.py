"""Health check router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from qna_agent.config import get_settings
from qna_agent.database import get_session
from qna_agent.health.schemas import DetailedHealthResponse, HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Returns basic health status of the API.",
)
async def health() -> HealthResponse:
    """Basic health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
    )


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Kubernetes liveness probe. Returns OK if process is alive.",
)
async def liveness() -> HealthResponse:
    """Liveness probe for Kubernetes."""
    settings = get_settings()
    return HealthResponse(
        status="alive",
        version=settings.app_version,
    )


@router.get(
    "/ready",
    response_model=DetailedHealthResponse,
    summary="Readiness probe",
    description="Kubernetes readiness probe. Checks database and dependencies.",
)
async def readiness(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DetailedHealthResponse:
    """Readiness probe for Kubernetes."""
    settings = get_settings()

    db_status = "healthy"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    kb_status = "healthy"
    if not settings.knowledge_base_path.exists():
        kb_status = "missing"

    return DetailedHealthResponse(
        status="ready" if db_status == "healthy" else "not_ready",
        version=settings.app_version,
        database=db_status,
        knowledge_base=kb_status,
    )
