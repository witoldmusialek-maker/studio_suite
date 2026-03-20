"""performed line resources

Revision ID: 20260228_02
Revises: 20260228_01_payments_and_cards
Create Date: 2026-02-28 13:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260228_02"
down_revision = "20260228_01_payments_and_cards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performedline_resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("performedline_id", sa.Integer(), nullable=False),
        sa.Column("recipeitem_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity_used", sa.Numeric(10, 3), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["performedline_id"], ["appointment_performed_lines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipeitem_id"], ["service_recipe_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["legacy_product_catalog_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("performedline_id", "recipeitem_id", name="uq_performedline_resources_line_recipe"),
    )
    op.create_index("ix_performedline_resources_line", "performedline_resources", ["performedline_id"])
    op.create_index("ix_performedline_resources_product", "performedline_resources", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_performedline_resources_product", table_name="performedline_resources")
    op.drop_index("ix_performedline_resources_line", table_name="performedline_resources")
    op.drop_table("performedline_resources")
