"""add user sessions table

Revision ID: 20260228_04
Revises: 20260228_03_notifications
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260228_04"
down_revision = "20260228_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("salon_id", sa.Integer(), nullable=True),
        sa.Column("session_key", sa.String(length=64), nullable=False),
        sa.Column("user_role", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_key"),
    )
    op.create_index(op.f("ix_user_sessions_id"), "user_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_user_sessions_last_seen"), "user_sessions", ["last_seen"], unique=False)
    op.create_index(op.f("ix_user_sessions_salon_id"), "user_sessions", ["salon_id"], unique=False)
    op.create_index(op.f("ix_user_sessions_session_key"), "user_sessions", ["session_key"], unique=True)
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"], unique=False)
    op.create_index("ix_user_sessions_user_last_seen", "user_sessions", ["user_id", "last_seen"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_sessions_user_last_seen", table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_session_key"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_salon_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_last_seen"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_id"), table_name="user_sessions")
    op.drop_table("user_sessions")
