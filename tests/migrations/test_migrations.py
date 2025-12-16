"""Tests for Alembic migrations."""

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from alembic import command
from alembic.config import Config

from qna_agent.config import get_settings


@pytest.fixture
def alembic_config() -> Generator[Config]:
    """Create Alembic config pointing to test database."""
    get_settings.cache_clear()

    config = Config("alembic.ini")

    with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
        yield config

    get_settings.cache_clear()


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
