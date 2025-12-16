"""Async SQLAlchemy database configuration."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from qna_agent.config import get_settings


def _create_engine() -> AsyncEngine:
    """Create async SQLAlchemy engine based on database URL."""
    settings = get_settings()

    connect_args: dict[str, Any] = {}
    pool_kwargs: dict[str, Any] = {}

    if "sqlite" in settings.database_url:
        connect_args["check_same_thread"] = False
    else:
        pool_kwargs = {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }

    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args=connect_args,
        **pool_kwargs,
    )


engine = _create_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
    """Enable WAL mode for SQLite for better concurrent read performance."""
    settings = get_settings()
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Dependency that provides an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
