"""Tests for Alembic migrations."""

from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
def alembic_config() -> Generator[Config]:
    """Create Alembic config pointing to test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", "sqlite:///:memory:")

    yield config

    engine.dispose()


def test_migrations_upgrade_to_head(alembic_config: Config) -> None:
    """Test that all migrations can be applied."""
    command.upgrade(alembic_config, "head")


def test_migrations_downgrade_to_base(alembic_config: Config) -> None:
    """Test that all migrations can be reverted."""
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")


def test_migrations_upgrade_downgrade_upgrade(alembic_config: Config) -> None:
    """Test full migration cycle."""
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
