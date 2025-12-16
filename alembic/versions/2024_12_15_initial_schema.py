"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-12-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _use_postgres_sql() -> bool:
    """Check if PostgreSQL SQL should be used.

    Returns True for PostgreSQL or offline mode (for squawk-compatible SQL).
    """
    ctx = op.get_context()
    return ctx.dialect.name == "postgresql" or ctx.as_sql


def upgrade() -> None:
    if _use_postgres_sql():
        op.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id UUID NOT NULL,
                title TEXT,
                metadata JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                CONSTRAINT pk_chats PRIMARY KEY (id)
            )
        """)

        op.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id UUID NOT NULL,
                chat_id UUID NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls JSONB,
                tool_call_id TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                CONSTRAINT pk_messages PRIMARY KEY (id),
                CONSTRAINT fk_messages_chat_id_chats
                    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)

        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_chat_id "
            "ON messages (chat_id)"
        )
    else:
        op.create_table(
            "chats",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_chats")),
        )

        op.create_table(
            "messages",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("chat_id", sa.Uuid(), nullable=False),
            sa.Column("role", sa.Text(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("tool_calls", sa.JSON(), nullable=True),
            sa.Column("tool_call_id", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["chat_id"],
                ["chats.id"],
                name=op.f("fk_messages_chat_id_chats"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        )
        op.create_index(
            op.f("ix_messages_chat_id"), "messages", ["chat_id"], unique=False
        )


def downgrade() -> None:
    if _use_postgres_sql():
        op.execute("DROP INDEX IF EXISTS ix_messages_chat_id")
        op.execute("DROP TABLE IF EXISTS messages")
        op.execute("DROP TABLE IF EXISTS chats")
    else:
        op.drop_index(op.f("ix_messages_chat_id"), table_name="messages")
        op.drop_table("messages")
        op.drop_table("chats")
