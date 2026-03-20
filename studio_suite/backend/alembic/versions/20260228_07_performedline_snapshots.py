"""expand performedline resources with snapshots

Revision ID: 20260228_07
Revises: 20260228_06
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa


revision = '20260228_07'
down_revision = '20260228_06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('performedline_resources', sa.Column('product_family_snapshot', sa.String(length=100), nullable=True))
    op.add_column('performedline_resources', sa.Column('product_name_snapshot', sa.String(length=255), nullable=True))
    op.add_column('performedline_resources', sa.Column('quantity_unit', sa.String(length=20), nullable=True))
    op.add_column('performedline_resources', sa.Column('unit_cost_snapshot', sa.Numeric(10, 2), nullable=True))
    op.add_column('performedline_resources', sa.Column('total_cost_snapshot', sa.Numeric(10, 2), nullable=True))

    op.execute(
        """
        UPDATE performedline_resources pr
        SET
            product_family_snapshot = sri.product_family,
            product_name_snapshot = COALESCE(lp.name, pr.product_name_snapshot),
            quantity_unit = COALESCE(sri.recipe_unit_label, sri.unit, pr.quantity_unit),
            unit_cost_snapshot = COALESCE(lp.purchase_price, lp.purchase_price_c, lp.catalog_net_price, pr.unit_cost_snapshot),
            total_cost_snapshot = COALESCE(pr.quantity_used * COALESCE(lp.purchase_price, lp.purchase_price_c, lp.catalog_net_price, 0), pr.total_cost_snapshot)
        FROM service_recipe_items sri, legacy_product_catalog_items lp
        WHERE sri.id = pr.recipeitem_id
          AND lp.id = pr.product_id
        """
    )


def downgrade() -> None:
    op.drop_column('performedline_resources', 'total_cost_snapshot')
    op.drop_column('performedline_resources', 'unit_cost_snapshot')
    op.drop_column('performedline_resources', 'quantity_unit')
    op.drop_column('performedline_resources', 'product_name_snapshot')
    op.drop_column('performedline_resources', 'product_family_snapshot')
