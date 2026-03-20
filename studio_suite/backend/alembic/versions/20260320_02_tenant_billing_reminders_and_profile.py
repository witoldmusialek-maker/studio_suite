"""tenant billing reminders and profile fields

Revision ID: 20260320_02
Revises: 20260320_01
Create Date: 2026-03-20 11:50:00.000000
"""

from alembic import op


revision = "20260320_02"
down_revision = "20260320_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS description TEXT")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS legal_name VARCHAR(255)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tax_id VARCHAR(64)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_address_line1 VARCHAR(255)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_address_line2 VARCHAR(255)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_postal_code VARCHAR(32)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_city VARCHAR(128)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_country VARCHAR(64) NOT NULL DEFAULT 'PL'")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_contact_name VARCHAR(128)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_contact_phone VARCHAR(64)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_due_days INTEGER NOT NULL DEFAULT 14")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_billing_invoices (
          id SERIAL PRIMARY KEY,
          tenant_id INTEGER NOT NULL REFERENCES tenants(id),
          period_year INTEGER NOT NULL,
          period_month INTEGER NOT NULL,
          issue_date DATE NOT NULL,
          due_date DATE NOT NULL,
          currency VARCHAR(3) NOT NULL DEFAULT 'PLN',
          base_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
          modules_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
          total_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
          status VARCHAR(24) NOT NULL DEFAULT 'OPEN',
          line_items_json TEXT,
          notes VARCHAR(255),
          sent_at TIMESTAMPTZ NULL,
          paid_at TIMESTAMPTZ NULL,
          created_at TIMESTAMPTZ DEFAULT now(),
          updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_billing_invoices_tenant_period "
        "ON tenant_billing_invoices(tenant_id, period_year, period_month)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tenant_billing_invoices_due_date "
        "ON tenant_billing_invoices(due_date)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_billing_reminder_logs (
          id SERIAL PRIMARY KEY,
          tenant_id INTEGER NOT NULL REFERENCES tenants(id),
          invoice_id INTEGER NOT NULL REFERENCES tenant_billing_invoices(id),
          reminder_kind VARCHAR(64) NOT NULL,
          channel VARCHAR(16) NOT NULL DEFAULT 'EMAIL',
          recipient VARCHAR(255),
          status VARCHAR(24) NOT NULL DEFAULT 'SENT',
          error_message VARCHAR(255),
          sent_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_billing_reminder_logs_invoice_kind "
        "ON tenant_billing_reminder_logs(invoice_id, reminder_kind)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenant_billing_reminder_logs_invoice_kind")
    op.execute("DROP TABLE IF EXISTS tenant_billing_reminder_logs")
    op.execute("DROP INDEX IF EXISTS ix_tenant_billing_invoices_due_date")
    op.execute("DROP INDEX IF EXISTS ix_tenant_billing_invoices_tenant_period")
    op.execute("DROP TABLE IF EXISTS tenant_billing_invoices")

    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_due_days")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_contact_phone")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_contact_name")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_country")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_city")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_postal_code")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_address_line2")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_address_line1")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS tax_id")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS legal_name")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS description")
