"""Pydantic schemas for health domain."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Basic health check response."""

    status: str = Field(description="Health status")
    version: str = Field(description="API version")


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response."""

    database: str = Field(description="Database connection status")
    knowledge_base: str = Field(description="Knowledge base status")
