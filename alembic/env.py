"""Alembic environment configuration for async migrations."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from qna_agent.chats.models import Chat
from qna_agent.config import get_settings
from qna_agent.messages.models import Message
from qna_agent.models import Base

config = context.config

POSTGRES_LOCK_TIMEOUT = "4s"
POSTGRES_STATEMENT_TIMEOUT = "30s"

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from settings."""
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def set_postgres_timeouts(connection: Connection) -> None:
    """Set PostgreSQL timeouts for safe migrations."""
    dialect = connection.dialect.name
    if dialect == "postgresql":
        connection.execute(text(f"SET lock_timeout = '{POSTGRES_LOCK_TIMEOUT}'"))
        connection.execute(text(f"SET statement_timeout = '{POSTGRES_STATEMENT_TIMEOUT}'"))


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection."""
    set_postgres_timeouts(connection)
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
