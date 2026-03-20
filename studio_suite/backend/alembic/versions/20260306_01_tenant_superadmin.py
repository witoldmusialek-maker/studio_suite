"""add superadmin flag

Revision ID: 20260306_01
Revises: 20260305_02
Create Date: 2026-03-06 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260306_01"
down_revision = "20260305_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN NOT NULL DEFAULT FALSE
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_users_is_superadmin
        ON users(is_superadmin)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_is_superadmin")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_superadmin")
