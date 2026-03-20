"""add optional flag to service recipe items

Revision ID: 20260228_05
Revises: 20260228_04
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260228_05"
down_revision = "20260228_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "service_recipe_items",
        sa.Column("is_optional", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.alter_column("service_recipe_items", "is_optional", server_default=None)


def downgrade() -> None:
    op.drop_column("service_recipe_items", "is_optional")
