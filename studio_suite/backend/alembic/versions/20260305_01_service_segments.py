"""backfill service segment markers from legacy service codes

Revision ID: 20260305_01
Revises: 20260228_12
Create Date: 2026-03-05 12:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260305_01"
down_revision = "20260228_12"
branch_labels = None
depends_on = None


SEGMENTS = ("PANI", "PAN", "ESTETYKA", "SPRZEDAZ")


def upgrade() -> None:
    conn = op.get_bind()

    # Normalize known values first.
    conn.execute(
        sa.text(
            """
            UPDATE service_catalog_items
               SET service_type_code = UPPER(TRIM(service_type_code))
             WHERE service_type_code IS NOT NULL
            """
        )
    )

    # Infer missing or invalid markers from numeric legacy code ranges.
    conn.execute(
        sa.text(
            """
            UPDATE service_catalog_items
               SET service_type_code = CASE
                 WHEN legacy_code ~ '^[0-9]+$' AND CAST(legacy_code AS INTEGER) BETWEEN 1 AND 99 THEN 'PANI'
                 WHEN legacy_code ~ '^[0-9]+$' AND CAST(legacy_code AS INTEGER) BETWEEN 101 AND 199 THEN 'PAN'
                 WHEN legacy_code ~ '^[0-9]+$' AND CAST(legacy_code AS INTEGER) BETWEEN 200 AND 299 THEN 'SPRZEDAZ'
                 WHEN legacy_code ~ '^[0-9]+$' AND CAST(legacy_code AS INTEGER) BETWEEN 300 AND 399 THEN 'ESTETYKA'
                 ELSE service_type_code
               END
             WHERE service_type_code IS NULL
                OR service_type_code NOT IN ('PANI', 'PAN', 'ESTETYKA', 'SPRZEDAZ')
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE service_catalog_items
               SET service_type_code = NULL
             WHERE service_type_code IN ('PANI', 'PAN', 'ESTETYKA', 'SPRZEDAZ')
            """
        )
    )
