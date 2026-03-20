"""add staff photo blob columns

Revision ID: 20260314_04
Revises: 20260314_03
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260314_04"
down_revision = "20260314_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("staff_members", sa.Column("public_photo_data", sa.LargeBinary(), nullable=True))
    op.add_column("staff_members", sa.Column("public_photo_content_type", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("staff_members", "public_photo_content_type")
    op.drop_column("staff_members", "public_photo_data")
