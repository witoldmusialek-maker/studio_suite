"""add pricing snapshots to appointment performed lines

Revision ID: 20260228_08
Revises: 20260228_07
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa


revision = '20260228_08'
down_revision = '20260228_07'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('appointment_performed_lines', sa.Column('service_name_snapshot', sa.String(length=255), nullable=True))
    op.add_column('appointment_performed_lines', sa.Column('list_price_snapshot', sa.Numeric(10, 2), nullable=True))
    op.add_column('appointment_performed_lines', sa.Column('discount_allocated_snapshot', sa.Numeric(10, 2), nullable=True))
    op.add_column('appointment_performed_lines', sa.Column('sold_as_bundle', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('appointment_performed_lines', sa.Column('bundle_id_snapshot', sa.Integer(), nullable=True))
    op.create_index('ix_appointment_performed_lines_bundle_id_snapshot', 'appointment_performed_lines', ['bundle_id_snapshot'], unique=False)
    op.create_foreign_key(
        'fk_appointment_performed_lines_bundle_id_snapshot',
        'appointment_performed_lines',
        'bundle_catalog',
        ['bundle_id_snapshot'],
        ['id'],
    )

    op.execute(
        """
        UPDATE appointment_performed_lines apl
        SET
            service_name_snapshot = sc.name,
            list_price_snapshot = COALESCE(sc.default_price, apl.price_snapshot),
            discount_allocated_snapshot = GREATEST(COALESCE(sc.default_price, apl.price_snapshot) - apl.price_snapshot, 0),
            sold_as_bundle = CASE WHEN a.bundle_id IS NOT NULL THEN TRUE ELSE FALSE END,
            bundle_id_snapshot = a.bundle_id
        FROM service_catalog_items sc, appointments a
        WHERE sc.id = apl.service_id
          AND a.id = apl.appointment_id
        """
    )

    op.alter_column('appointment_performed_lines', 'sold_as_bundle', server_default=None)


def downgrade() -> None:
    op.drop_constraint('fk_appointment_performed_lines_bundle_id_snapshot', 'appointment_performed_lines', type_='foreignkey')
    op.drop_index('ix_appointment_performed_lines_bundle_id_snapshot', table_name='appointment_performed_lines')
    op.drop_column('appointment_performed_lines', 'bundle_id_snapshot')
    op.drop_column('appointment_performed_lines', 'sold_as_bundle')
    op.drop_column('appointment_performed_lines', 'discount_allocated_snapshot')
    op.drop_column('appointment_performed_lines', 'list_price_snapshot')
    op.drop_column('appointment_performed_lines', 'service_name_snapshot')
