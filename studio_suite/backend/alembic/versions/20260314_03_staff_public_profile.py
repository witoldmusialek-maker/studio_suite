"""add public profile fields for staff

Revision ID: 20260314_03
Revises: 20260314_02
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260314_03"
down_revision = "20260314_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("staff_members", sa.Column("public_bio", sa.Text(), nullable=True))
    op.add_column("staff_members", sa.Column("public_photo_url", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("staff_members", "public_photo_url")
    op.drop_column("staff_members", "public_bio")
