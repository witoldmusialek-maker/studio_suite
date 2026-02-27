"""add service recipe items and planned issue line support

Revision ID: 20260227_01
Revises: 
Create Date: 2026-02-27 18:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260227_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("service_recipe_items"):
        op.create_table(
            "service_recipe_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("service_id", sa.Integer(), sa.ForeignKey("service_catalog_items.id", ondelete="CASCADE"), nullable=False),
            sa.Column("product_family", sa.String(length=100), nullable=True),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("legacy_product_catalog_items.id"), nullable=True),
            sa.Column("planned_quantity", sa.Numeric(10, 3), nullable=False),
            sa.Column("unit", sa.String(length=20), nullable=False),
            sa.Column("note", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        )
        op.create_index("ix_service_recipe_items_service_id", "service_recipe_items", ["service_id"])

    columns = {col["name"] for col in inspector.get_columns("inventory_issue_lines")}
    if "recipe_item_id" not in columns:
        op.add_column("inventory_issue_lines", sa.Column("recipe_item_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "inventory_issue_lines_recipe_item_id_fkey",
            "inventory_issue_lines",
            "service_recipe_items",
            ["recipe_item_id"],
            ["id"],
        )
        op.create_index("ix_inventory_issue_lines_recipe_item", "inventory_issue_lines", ["recipe_item_id"])

    op.alter_column("inventory_issue_lines", "product_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("inventory_issue_lines", "quantity_actual", existing_type=sa.Numeric(14, 4), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("inventory_issue_lines")}

    op.alter_column("inventory_issue_lines", "quantity_actual", existing_type=sa.Numeric(14, 4), nullable=False)
    op.alter_column("inventory_issue_lines", "product_id", existing_type=sa.Integer(), nullable=False)

    if "recipe_item_id" in columns:
        op.drop_index("ix_inventory_issue_lines_recipe_item", table_name="inventory_issue_lines")
        op.drop_constraint("inventory_issue_lines_recipe_item_id_fkey", "inventory_issue_lines", type_="foreignkey")
        op.drop_column("inventory_issue_lines", "recipe_item_id")

    if inspector.has_table("service_recipe_items"):
        op.drop_index("ix_service_recipe_items_service_id", table_name="service_recipe_items")
        op.drop_table("service_recipe_items")
