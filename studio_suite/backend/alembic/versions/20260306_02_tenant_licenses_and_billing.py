"""tenant licenses and billing fields

Revision ID: 20260306_02
Revises: 20260306_01
Create Date: 2026-03-06 18:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260306_02"
down_revision = "20260306_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_plan VARCHAR(32) NOT NULL DEFAULT 'BASIC'"
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(16) NOT NULL DEFAULT 'monthly'"
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS monthly_base_price NUMERIC(10,2) NOT NULL DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_email VARCHAR(255)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_module_licenses (
          id SERIAL PRIMARY KEY,
          tenant_id INTEGER NOT NULL REFERENCES tenants(id),
          module_code VARCHAR(64) NOT NULL,
          is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
          monthly_price NUMERIC(10,2) NOT NULL DEFAULT 0,
          notes VARCHAR(255),
          created_at TIMESTAMPTZ DEFAULT now(),
          updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_module_licenses_tenant_id ON tenant_module_licenses(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_module_licenses_module_code ON tenant_module_licenses(module_code)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_module_licenses_tenant_module ON tenant_module_licenses(tenant_id, module_code)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenant_module_licenses_tenant_module")
    op.execute("DROP INDEX IF EXISTS ix_tenant_module_licenses_module_code")
    op.execute("DROP INDEX IF EXISTS ix_tenant_module_licenses_tenant_id")
    op.execute("DROP TABLE IF EXISTS tenant_module_licenses")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_email")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS monthly_base_price")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_cycle")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS billing_plan")
