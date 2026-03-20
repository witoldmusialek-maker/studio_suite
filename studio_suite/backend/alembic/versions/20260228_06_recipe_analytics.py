"""expand service recipe items for analytic snapshots

Revision ID: 20260228_06
Revises: 20260228_05
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa


revision = '20260228_06'
down_revision = '20260228_05'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('service_recipe_items', sa.Column('variant_code', sa.String(length=32), nullable=True))
    op.add_column('service_recipe_items', sa.Column('position', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('service_recipe_items', sa.Column('product_label_snapshot', sa.String(length=255), nullable=True))
    op.add_column('service_recipe_items', sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('service_recipe_items', sa.Column('quantity_mode', sa.String(length=16), nullable=False, server_default='EXACT'))
    op.add_column('service_recipe_items', sa.Column('planned_min', sa.Numeric(10, 3), nullable=True))
    op.add_column('service_recipe_items', sa.Column('planned_default', sa.Numeric(10, 3), nullable=True))
    op.add_column('service_recipe_items', sa.Column('planned_max', sa.Numeric(10, 3), nullable=True))
    op.add_column('service_recipe_items', sa.Column('recipe_unit_label', sa.String(length=20), nullable=True))
    op.add_column('service_recipe_items', sa.Column('package_unit_count', sa.Numeric(10, 3), nullable=True))
    op.add_column('service_recipe_items', sa.Column('package_unit_label', sa.String(length=20), nullable=True))
    op.add_column('service_recipe_items', sa.Column('package_size_value', sa.Numeric(10, 3), nullable=True))
    op.add_column('service_recipe_items', sa.Column('package_size_unit', sa.String(length=20), nullable=True))
    op.add_column('service_recipe_items', sa.Column('inventory_mode', sa.String(length=24), nullable=False, server_default='PER_SERVICE'))
    op.create_index('ix_service_recipe_items_variant_code', 'service_recipe_items', ['variant_code'], unique=False)

    op.execute('UPDATE service_recipe_items SET planned_default = planned_quantity WHERE planned_default IS NULL')
    op.execute('UPDATE service_recipe_items SET recipe_unit_label = unit WHERE recipe_unit_label IS NULL')
    op.execute('UPDATE service_recipe_items SET position = 1 WHERE position IS NULL')

    op.alter_column('service_recipe_items', 'position', server_default=None)
    op.alter_column('service_recipe_items', 'is_required', server_default=None)
    op.alter_column('service_recipe_items', 'quantity_mode', server_default=None)
    op.alter_column('service_recipe_items', 'inventory_mode', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_service_recipe_items_variant_code', table_name='service_recipe_items')
    op.drop_column('service_recipe_items', 'inventory_mode')
    op.drop_column('service_recipe_items', 'package_size_unit')
    op.drop_column('service_recipe_items', 'package_size_value')
    op.drop_column('service_recipe_items', 'package_unit_label')
    op.drop_column('service_recipe_items', 'package_unit_count')
    op.drop_column('service_recipe_items', 'recipe_unit_label')
    op.drop_column('service_recipe_items', 'planned_max')
    op.drop_column('service_recipe_items', 'planned_default')
    op.drop_column('service_recipe_items', 'planned_min')
    op.drop_column('service_recipe_items', 'quantity_mode')
    op.drop_column('service_recipe_items', 'is_required')
    op.drop_column('service_recipe_items', 'product_label_snapshot')
    op.drop_column('service_recipe_items', 'position')
    op.drop_column('service_recipe_items', 'variant_code')
