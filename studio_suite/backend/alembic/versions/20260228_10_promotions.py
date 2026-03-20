"""add promotions entity and payment link

Revision ID: 20260228_10
Revises: 20260228_09
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa


revision = '20260228_10'
down_revision = '20260228_09'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'promotions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('promotion_type', sa.String(length=32), nullable=False, server_default='fixed_discount'),
        sa.Column('value', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('salon_id', sa.Integer(), sa.ForeignKey('salons.id'), nullable=True),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('service_catalog_items.id'), nullable=True),
        sa.Column('bundle_id', sa.Integer(), sa.ForeignKey('bundle_catalog.id'), nullable=True),
        sa.Column('customer_tier', sa.String(length=32), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_promotions_name', 'promotions', ['name'], unique=False)
    op.create_index('ix_promotions_validity', 'promotions', ['valid_from', 'valid_to'], unique=False)
    op.create_index('ix_promotions_salon_id', 'promotions', ['salon_id'], unique=False)
    op.create_index('ix_promotions_service_id', 'promotions', ['service_id'], unique=False)
    op.create_index('ix_promotions_bundle_id', 'promotions', ['bundle_id'], unique=False)
    op.create_index('ix_promotions_customer_tier', 'promotions', ['customer_tier'], unique=False)

    op.add_column('payments', sa.Column('promotion_id', sa.Integer(), nullable=True))
    op.create_index('ix_payments_promotion_id', 'payments', ['promotion_id'], unique=False)
    op.create_foreign_key('fk_payments_promotion_id', 'payments', 'promotions', ['promotion_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint('fk_payments_promotion_id', 'payments', type_='foreignkey')
    op.drop_index('ix_payments_promotion_id', table_name='payments')
    op.drop_column('payments', 'promotion_id')
    op.drop_index('ix_promotions_customer_tier', table_name='promotions')
    op.drop_index('ix_promotions_bundle_id', table_name='promotions')
    op.drop_index('ix_promotions_service_id', table_name='promotions')
    op.drop_index('ix_promotions_salon_id', table_name='promotions')
    op.drop_index('ix_promotions_validity', table_name='promotions')
    op.drop_index('ix_promotions_name', table_name='promotions')
    op.drop_table('promotions')
