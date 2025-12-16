"""add_message_updated_at

Revision ID: e67a105d2cdb
Revises: 001
Create Date: 2025-12-16 18:53:01.966694

"""

import sqlalchemy as sa
from alembic import op

revision: str = "e67a105d2cdb"
down_revision: str | None = "001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def _use_postgres_sql() -> bool:
    """Check if PostgreSQL SQL should be used.

    Returns True for PostgreSQL or offline mode (for squawk-compatible SQL).
    """
    ctx = op.get_context()
    return ctx.dialect.name == "postgresql" or ctx.as_sql


def upgrade() -> None:
    if _use_postgres_sql():
        op.execute("""
            ALTER TABLE messages
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)
    else:
        op.add_column(
            "messages",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    if _use_postgres_sql():
        op.execute("ALTER TABLE messages DROP COLUMN IF EXISTS updated_at")
    else:
        op.drop_column("messages", "updated_at")
