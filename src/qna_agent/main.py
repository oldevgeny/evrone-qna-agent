"""FastAPI application factory with middleware and exception handlers."""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from qna_agent.chats.router import router as chats_router
from qna_agent.config import get_settings
from qna_agent.events.router import router as events_router
from qna_agent.exceptions import (
    KnowledgeBaseError,
    LLMError,
    NotFoundError,
    ValidationError,
)
from qna_agent.health.router import router as health_router
from qna_agent.messages.router import router as messages_router


def configure_logging() -> None:
    """Configure Loguru logging."""
    settings = get_settings()

    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )

    if not settings.debug:
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level=settings.log_level,
            serialize=True,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan context manager."""
    configure_logging()
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    if not settings.knowledge_base_path.exists():
        settings.knowledge_base_path.mkdir(parents=True)
        logger.info(f"Created knowledge base directory: {settings.knowledge_base_path}")

    yield

    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="QnA Agent API - Chat-based question answering with OpenAI function calling",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(  # type: ignore[misc]
        request: Request, exc: NotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(  # type: ignore[misc]
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(LLMError)
    async def llm_error_handler(  # type: ignore[misc]
        request: Request, exc: LLMError
    ) -> JSONResponse:
        logger.error(f"LLM error: {exc}")
        return JSONResponse(
            status_code=503,
            content={"detail": "AI service temporarily unavailable"},
        )

    @app.exception_handler(KnowledgeBaseError)
    async def kb_error_handler(  # type: ignore[misc]
        request: Request, exc: KnowledgeBaseError
    ) -> JSONResponse:
        logger.error(f"Knowledge base error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    app.include_router(health_router)
    app.include_router(chats_router, prefix="/api/v1")
    app.include_router(messages_router, prefix="/api/v1")
    app.include_router(events_router, prefix="/api/v1")

    return app


app = create_app()
