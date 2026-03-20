"""add allow_overlap to appointments

Revision ID: 20260314_02
Revises: 20260314_01
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260314_02"
down_revision = "20260314_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("allow_overlap", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("appointments", "allow_overlap")
