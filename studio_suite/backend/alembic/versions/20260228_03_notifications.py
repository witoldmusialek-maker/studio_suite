"""notifications

Revision ID: 20260228_03
Revises: 20260228_02
Create Date: 2026-02-28 14:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260228_03"
down_revision = "20260228_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=False),
        sa.Column("notification_type", sa.String(length=32), nullable=False, server_default="confirmation"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("message", sa.String(length=512), nullable=False),
        sa.Column("provider_message_id", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_appointment_type", "notifications", ["appointment_id", "notification_type"])
    op.create_index("ix_notifications_status_created", "notifications", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_status_created", table_name="notifications")
    op.drop_index("ix_notifications_appointment_type", table_name="notifications")
    op.drop_table("notifications")
