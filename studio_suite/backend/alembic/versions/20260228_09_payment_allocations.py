"""add payment allocations and discount snapshots

Revision ID: 20260228_09
Revises: 20260228_08
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa


revision = '20260228_09'
down_revision = '20260228_08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('payments', sa.Column('discount_reason_snapshot', sa.String(length=64), nullable=True))
    op.add_column('payments', sa.Column('promotion_name_snapshot', sa.String(length=255), nullable=True))

    op.create_table(
        'payment_allocations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('payment_id', sa.Integer(), sa.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('method', sa.String(length=16), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('voucher_reference', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('ix_payment_allocations_payment_id', 'payment_allocations', ['payment_id'], unique=False)
    op.create_index('ix_payment_allocations_method', 'payment_allocations', ['method'], unique=False)
    op.create_index('ix_payment_allocations_payment_method', 'payment_allocations', ['payment_id', 'method'], unique=False)

    op.execute(
        """
        INSERT INTO payment_allocations (payment_id, method, amount)
        SELECT id, method, amount
        FROM payments
        """
    )
    op.execute(
        """
        UPDATE payments
        SET discount_reason_snapshot = CASE
            WHEN client_card_id IS NOT NULL AND discount_total > 0 THEN 'client_card'
            WHEN discount_total > 0 THEN 'discount'
            ELSE NULL
        END
        """
    )


def downgrade() -> None:
    op.drop_index('ix_payment_allocations_payment_method', table_name='payment_allocations')
    op.drop_index('ix_payment_allocations_method', table_name='payment_allocations')
    op.drop_index('ix_payment_allocations_payment_id', table_name='payment_allocations')
    op.drop_table('payment_allocations')
    op.drop_column('payments', 'promotion_name_snapshot')
    op.drop_column('payments', 'discount_reason_snapshot')
