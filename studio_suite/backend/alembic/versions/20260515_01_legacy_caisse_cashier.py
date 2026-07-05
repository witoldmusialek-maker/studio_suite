"""legacy caisse cashier tables and nullable cashier payments

Revision ID: 20260515_01
Revises: 20260320_02
Create Date: 2026-05-15 12:00:00.000000
"""

from alembic import op


revision = "20260515_01"
down_revision = "20260320_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE payments ALTER COLUMN appointment_id DROP NOT NULL")
    op.execute("ALTER TABLE payments ALTER COLUMN client_id DROP NOT NULL")
    op.execute("ALTER TABLE sale_lines ALTER COLUMN product_id DROP NOT NULL")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS service_id INTEGER REFERENCES service_catalog_items(id)")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS staff_id INTEGER REFERENCES staff_members(id)")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS line_kind VARCHAR(24) NOT NULL DEFAULT 'product'")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS legacy_worker_code_snapshot VARCHAR(16)")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS legacy_service_code_snapshot VARCHAR(32)")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS label_snapshot VARCHAR(255)")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS bundle_id INTEGER REFERENCES bundle_catalog(id)")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS bundle_code_snapshot VARCHAR(16)")
    op.execute("ALTER TABLE sale_lines ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sale_lines_sale_service ON sale_lines(sale_id, service_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sale_lines_sale_staff ON sale_lines(sale_id, staff_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sale_lines_kind ON sale_lines(line_kind)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cashier_cash_sessions (
          id SERIAL PRIMARY KEY,
          tenant_id INTEGER NOT NULL REFERENCES tenants(id),
          salon_id INTEGER NOT NULL REFERENCES salons(id),
          business_date DATE NOT NULL,
          opening_cash NUMERIC(12,2) NOT NULL DEFAULT 0,
          closing_cash NUMERIC(12,2),
          status VARCHAR(16) NOT NULL DEFAULT 'OPEN',
          opened_by_user_id INTEGER REFERENCES users(id),
          closed_by_user_id INTEGER REFERENCES users(id),
          opened_at TIMESTAMPTZ DEFAULT now(),
          closed_at TIMESTAMPTZ,
          created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_cashier_cash_sessions_tenant_salon_date ON cashier_cash_sessions(tenant_id, salon_id, business_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cashier_cash_sessions_salon_date ON cashier_cash_sessions(salon_id, business_date)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cashier_expenses (
          id SERIAL PRIMARY KEY,
          tenant_id INTEGER NOT NULL REFERENCES tenants(id),
          salon_id INTEGER NOT NULL REFERENCES salons(id),
          expense_date DATE NOT NULL,
          staff_id INTEGER REFERENCES staff_members(id),
          created_by_user_id INTEGER NOT NULL REFERENCES users(id),
          expense_type VARCHAR(32) NOT NULL DEFAULT 'misc',
          family VARCHAR(128),
          label VARCHAR(255) NOT NULL,
          amount_gross NUMERIC(12,2) NOT NULL DEFAULT 0,
          vat_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
          amount_net NUMERIC(12,2) NOT NULL DEFAULT 0,
          created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_cashier_expenses_salon_date ON cashier_expenses(salon_id, expense_date)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS staff_presence_entries (
          id SERIAL PRIMARY KEY,
          tenant_id INTEGER NOT NULL REFERENCES tenants(id),
          salon_id INTEGER NOT NULL REFERENCES salons(id),
          staff_id INTEGER NOT NULL REFERENCES staff_members(id),
          presence_date DATE NOT NULL,
          status VARCHAR(24) NOT NULL DEFAULT 'PRESENT',
          time_from TIME,
          time_to TIME,
          created_at TIMESTAMPTZ DEFAULT now(),
          updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_staff_presence_tenant_salon_staff_date ON staff_presence_entries(tenant_id, salon_id, staff_id, presence_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_staff_presence_salon_date ON staff_presence_entries(salon_id, presence_date)")

    op.execute(
        """
        INSERT INTO tenant_module_licenses (tenant_id, module_code, is_enabled, monthly_price, notes)
        SELECT id, 'LEGACY_CAISSE', TRUE, 0, 'Transitional salon cashier module'
        FROM tenants
        ON CONFLICT (tenant_id, module_code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS staff_presence_entries")
    op.execute("DROP TABLE IF EXISTS cashier_expenses")
    op.execute("DROP TABLE IF EXISTS cashier_cash_sessions")
    op.execute("DROP INDEX IF EXISTS ix_sale_lines_kind")
    op.execute("DROP INDEX IF EXISTS ix_sale_lines_sale_staff")
    op.execute("DROP INDEX IF EXISTS ix_sale_lines_sale_service")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS discount_amount")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS bundle_code_snapshot")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS bundle_id")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS label_snapshot")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS legacy_service_code_snapshot")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS legacy_worker_code_snapshot")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS line_kind")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS staff_id")
    op.execute("ALTER TABLE sale_lines DROP COLUMN IF EXISTS service_id")
