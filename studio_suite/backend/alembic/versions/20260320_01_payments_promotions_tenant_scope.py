"""add tenant scope to payments and promotions

Revision ID: 20260320_01
Revises: 20260314_05
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260320_01"
down_revision = "20260314_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("tenant_id", sa.Integer(), nullable=True, server_default="1"))
    op.execute(
        "UPDATE payments p SET tenant_id = a.tenant_id FROM appointments a "
        "WHERE p.appointment_id = a.id AND p.tenant_id IS NULL"
    )
    op.execute("UPDATE payments SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column("payments", "tenant_id", nullable=False, server_default="1")
    op.create_foreign_key("fk_payments_tenant_id", "payments", "tenants", ["tenant_id"], ["id"])
    op.create_index(op.f("ix_payments_tenant_id"), "payments", ["tenant_id"], unique=False)

    op.add_column("promotions", sa.Column("tenant_id", sa.Integer(), nullable=True, server_default="1"))
    op.execute(
        "UPDATE promotions pr SET tenant_id = s.tenant_id FROM salons s "
        "WHERE pr.salon_id = s.id AND pr.tenant_id IS NULL"
    )
    op.execute("UPDATE promotions SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column("promotions", "tenant_id", nullable=False, server_default="1")
    op.create_foreign_key("fk_promotions_tenant_id", "promotions", "tenants", ["tenant_id"], ["id"])
    op.create_index(op.f("ix_promotions_tenant_id"), "promotions", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_promotions_tenant_id"), table_name="promotions")
    op.drop_constraint("fk_promotions_tenant_id", "promotions", type_="foreignkey")
    op.drop_column("promotions", "tenant_id")

    op.drop_index(op.f("ix_payments_tenant_id"), table_name="payments")
    op.drop_constraint("fk_payments_tenant_id", "payments", type_="foreignkey")
    op.drop_column("payments", "tenant_id")
