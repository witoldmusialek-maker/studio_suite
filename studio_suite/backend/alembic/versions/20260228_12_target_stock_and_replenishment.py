"""target stock per salon and replenishment suggestions

Revision ID: 20260228_12
Revises: 20260228_11
Create Date: 2026-02-28 23:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260228_12"
down_revision = "20260228_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "salon_product_target_stocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("salon_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("target_quantity", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["legacy_product_catalog_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("salon_id", "product_id", name="uq_salon_product_target_stock"),
    )
    op.create_index(op.f("ix_salon_product_target_stocks_id"), "salon_product_target_stocks", ["id"], unique=False)
    op.create_index(op.f("ix_salon_product_target_stocks_salon_id"), "salon_product_target_stocks", ["salon_id"], unique=False)
    op.create_index(op.f("ix_salon_product_target_stocks_product_id"), "salon_product_target_stocks", ["product_id"], unique=False)
    op.create_index(
        "ix_salon_product_target_stocks_salon_product",
        "salon_product_target_stocks",
        ["salon_id", "product_id"],
        unique=False,
    )

    op.create_table(
        "replenishment_suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("salon_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("target_quantity", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("actual_quantity", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("suggested_quantity", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="OPEN"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["legacy_product_catalog_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_replenishment_suggestions_id"), "replenishment_suggestions", ["id"], unique=False)
    op.create_index(op.f("ix_replenishment_suggestions_salon_id"), "replenishment_suggestions", ["salon_id"], unique=False)
    op.create_index(op.f("ix_replenishment_suggestions_product_id"), "replenishment_suggestions", ["product_id"], unique=False)
    op.create_index(op.f("ix_replenishment_suggestions_status"), "replenishment_suggestions", ["status"], unique=False)
    op.create_index(op.f("ix_replenishment_suggestions_generated_at"), "replenishment_suggestions", ["generated_at"], unique=False)
    op.create_index(op.f("ix_replenishment_suggestions_resolved_at"), "replenishment_suggestions", ["resolved_at"], unique=False)
    op.create_index(
        "ix_replenishment_suggestions_salon_status",
        "replenishment_suggestions",
        ["salon_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_replenishment_suggestions_product_status",
        "replenishment_suggestions",
        ["product_id", "status"],
        unique=False,
    )

    conn = op.get_bind()
    salons = conn.execute(sa.text("SELECT id, code, lower(name) AS lname FROM salons")).mappings().all()
    for salon in salons:
        salon_id = salon["id"]
        code = (salon["code"] or "").strip()
        lname = salon["lname"] or ""
        source_col = "stock_mx04"
        if code == "05" or "pulaw" in lname:
            source_col = "stock_mx03"
        elif code == "12" or "kras" in lname:
            source_col = "stock_mx04"
        elif code == "07" or "odyn" in lname:
            source_col = "stock_mx07"

        conn.execute(
            sa.text(
                f"""
                INSERT INTO salon_product_target_stocks (salon_id, product_id, target_quantity)
                SELECT :salon_id, id, COALESCE({source_col}, 0)
                FROM legacy_product_catalog_items
                WHERE COALESCE({source_col}, 0) > 0
                ON CONFLICT (salon_id, product_id) DO UPDATE
                  SET target_quantity = EXCLUDED.target_quantity,
                      updated_at = now()
                """
            ),
            {"salon_id": salon_id},
        )


def downgrade() -> None:
    op.drop_index("ix_replenishment_suggestions_product_status", table_name="replenishment_suggestions")
    op.drop_index("ix_replenishment_suggestions_salon_status", table_name="replenishment_suggestions")
    op.drop_index(op.f("ix_replenishment_suggestions_resolved_at"), table_name="replenishment_suggestions")
    op.drop_index(op.f("ix_replenishment_suggestions_generated_at"), table_name="replenishment_suggestions")
    op.drop_index(op.f("ix_replenishment_suggestions_status"), table_name="replenishment_suggestions")
    op.drop_index(op.f("ix_replenishment_suggestions_product_id"), table_name="replenishment_suggestions")
    op.drop_index(op.f("ix_replenishment_suggestions_salon_id"), table_name="replenishment_suggestions")
    op.drop_index(op.f("ix_replenishment_suggestions_id"), table_name="replenishment_suggestions")
    op.drop_table("replenishment_suggestions")

    op.drop_index("ix_salon_product_target_stocks_salon_product", table_name="salon_product_target_stocks")
    op.drop_index(op.f("ix_salon_product_target_stocks_product_id"), table_name="salon_product_target_stocks")
    op.drop_index(op.f("ix_salon_product_target_stocks_salon_id"), table_name="salon_product_target_stocks")
    op.drop_index(op.f("ix_salon_product_target_stocks_id"), table_name="salon_product_target_stocks")
    op.drop_table("salon_product_target_stocks")
