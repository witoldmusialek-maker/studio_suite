"""normalize legacy numeric service segments to text markers

Revision ID: 20260305_02
Revises: 20260305_01
Create Date: 2026-03-05 12:50:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260305_02"
down_revision = "20260305_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
            UPDATE service_catalog_items
               SET service_type_code = CASE
                 WHEN TRIM(COALESCE(service_type_code, '')) = '1' THEN 'PANI'
                 WHEN TRIM(COALESCE(service_type_code, '')) = '2' THEN 'PAN'
                 WHEN TRIM(COALESCE(service_type_code, '')) = '3' THEN 'ESTETYKA'
                 WHEN TRIM(COALESCE(service_type_code, '')) = '4' THEN 'SPRZEDAZ'
                 ELSE service_type_code
               END
             WHERE TRIM(COALESCE(service_type_code, '')) IN ('1', '2', '3', '4')
            """
        )
    )

    conn.execute(
        sa.text(
            """
            UPDATE service_catalog_items
               SET service_type_code = CASE
                 WHEN TRIM(legacy_code) ~ '^[0-9]+$' AND CAST(TRIM(legacy_code) AS INTEGER) BETWEEN 1 AND 99 THEN 'PANI'
                 WHEN TRIM(legacy_code) ~ '^[0-9]+$' AND CAST(TRIM(legacy_code) AS INTEGER) BETWEEN 101 AND 199 THEN 'PAN'
                 WHEN TRIM(legacy_code) ~ '^[0-9]+$' AND CAST(TRIM(legacy_code) AS INTEGER) BETWEEN 200 AND 299 THEN 'SPRZEDAZ'
                 WHEN TRIM(legacy_code) ~ '^[0-9]+$' AND CAST(TRIM(legacy_code) AS INTEGER) BETWEEN 300 AND 399 THEN 'ESTETYKA'
                 ELSE service_type_code
               END
             WHERE service_type_code IS NULL
                OR TRIM(service_type_code) = ''
                OR UPPER(TRIM(service_type_code)) NOT IN ('PANI', 'PAN', 'ESTETYKA', 'SPRZEDAZ')
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE service_catalog_items
               SET service_type_code = CASE
                 WHEN service_type_code = 'PANI' THEN '1'
                 WHEN service_type_code = 'PAN' THEN '2'
                 WHEN service_type_code = 'ESTETYKA' THEN '3'
                 WHEN service_type_code = 'SPRZEDAZ' THEN '4'
                 ELSE service_type_code
               END
             WHERE service_type_code IN ('PANI', 'PAN', 'ESTETYKA', 'SPRZEDAZ')
            """
        )
    )
