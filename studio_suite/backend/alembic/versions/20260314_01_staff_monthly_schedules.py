"""add staff monthly schedules

Revision ID: 20260314_01
Revises: 20260306_04
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260314_01"
down_revision = "20260306_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_monthly_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("staff_id", sa.Integer(), nullable=False),
        sa.Column("salon_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("time_from", sa.Time(), nullable=False),
        sa.Column("time_to", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_members.id"]),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("staff_id", "salon_id", "work_date", "time_from", "time_to", name="uq_staff_monthly_schedule_slot"),
    )
    op.create_index("ix_staff_monthly_schedules_staff_date", "staff_monthly_schedules", ["staff_id", "work_date"])
    op.create_index("ix_staff_monthly_schedules_salon_date", "staff_monthly_schedules", ["salon_id", "work_date"])
    op.create_index("ix_staff_monthly_schedules_work_date", "staff_monthly_schedules", ["work_date"])


def downgrade() -> None:
    op.drop_index("ix_staff_monthly_schedules_work_date", table_name="staff_monthly_schedules")
    op.drop_index("ix_staff_monthly_schedules_salon_date", table_name="staff_monthly_schedules")
    op.drop_index("ix_staff_monthly_schedules_staff_date", table_name="staff_monthly_schedules")
    op.drop_table("staff_monthly_schedules")
