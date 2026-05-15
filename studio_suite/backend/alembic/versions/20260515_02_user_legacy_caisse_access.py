"""Add per-user Legacy CAISSE access flag.

Revision ID: 20260515_02
Revises: 20260515_01
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260515_02"
down_revision = "20260515_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("legacy_caisse_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("users", "legacy_caisse_enabled")
