"""add_message_updated_at

Revision ID: e67a105d2cdb
Revises: 001
Create Date: 2025-12-16 18:53:01.966694

"""

from alembic import op
import sqlalchemy as sa


revision: str = "e67a105d2cdb"
down_revision: str | None = "001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
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
    op.drop_column("messages", "updated_at")
