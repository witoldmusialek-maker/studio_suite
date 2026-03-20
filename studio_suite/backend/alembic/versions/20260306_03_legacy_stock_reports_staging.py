"""legacy stock report staging tables

Revision ID: 20260306_03
Revises: 20260306_02
Create Date: 2026-03-06 20:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260306_03"
down_revision = "20260306_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "legacy_stock_report_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_archive_path", sa.String(length=512), nullable=False),
        sa.Column("source_archive_name", sa.String(length=255), nullable=False),
        sa.Column("source_archive_sha256", sa.String(length=64), nullable=True),
        sa.Column("source_archive_size_bytes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legacy_stock_report_batches_id"), "legacy_stock_report_batches", ["id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_batches_tenant_id"), "legacy_stock_report_batches", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_batches_source_archive_name"), "legacy_stock_report_batches", ["source_archive_name"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_batches_source_archive_sha256"), "legacy_stock_report_batches", ["source_archive_sha256"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_batches_imported_at"), "legacy_stock_report_batches", ["imported_at"], unique=False)

    op.create_table(
        "legacy_stock_report_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("salon_id", sa.Integer(), nullable=True),
        sa.Column("salon_label", sa.String(length=128), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_ext", sa.String(length=16), nullable=False),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("report_year", sa.Integer(), nullable=True),
        sa.Column("report_month", sa.Integer(), nullable=True),
        sa.Column("report_generated_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parse_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["legacy_stock_report_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_id", "file_name", name="uq_legacy_stock_report_files_batch_file"),
    )
    op.create_index(op.f("ix_legacy_stock_report_files_id"), "legacy_stock_report_files", ["id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_batch_id"), "legacy_stock_report_files", ["batch_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_tenant_id"), "legacy_stock_report_files", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_salon_id"), "legacy_stock_report_files", ["salon_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_salon_label"), "legacy_stock_report_files", ["salon_label"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_file_name"), "legacy_stock_report_files", ["file_name"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_file_ext"), "legacy_stock_report_files", ["file_ext"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_report_type"), "legacy_stock_report_files", ["report_type"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_report_year"), "legacy_stock_report_files", ["report_year"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_report_month"), "legacy_stock_report_files", ["report_month"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_report_generated_at"), "legacy_stock_report_files", ["report_generated_at"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_parse_status"), "legacy_stock_report_files", ["parse_status"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_files_imported_at"), "legacy_stock_report_files", ["imported_at"], unique=False)
    op.create_index("ix_legacy_stock_report_files_salon_type", "legacy_stock_report_files", ["salon_id", "report_type"], unique=False)

    op.create_table(
        "legacy_stock_report_rows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_file_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("salon_id", sa.Integer(), nullable=True),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=True),
        sa.Column("product_name_pl", sa.String(length=255), nullable=True),
        sa.Column("product_name", sa.String(length=255), nullable=True),
        sa.Column("family_code", sa.String(length=128), nullable=True),
        sa.Column("package_label", sa.String(length=64), nullable=True),
        sa.Column("catalog_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("sale_price_gross", sa.Numeric(12, 4), nullable=True),
        sa.Column("unit_count", sa.Numeric(14, 4), nullable=True),
        sa.Column("counted_units_pcs", sa.Numeric(14, 4), nullable=True),
        sa.Column("counted_units_dose", sa.Numeric(14, 4), nullable=True),
        sa.Column("counted_weight_gross", sa.Numeric(14, 4), nullable=True),
        sa.Column("counted_packages", sa.Numeric(14, 4), nullable=True),
        sa.Column("balance_open", sa.Numeric(14, 4), nullable=True),
        sa.Column("balance_pz", sa.Numeric(14, 4), nullable=True),
        sa.Column("balance_wz_rw", sa.Numeric(14, 4), nullable=True),
        sa.Column("balance_adjustment", sa.Numeric(14, 4), nullable=True),
        sa.Column("balance_close", sa.Numeric(14, 4), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.Column("mapped_product_id", sa.Integer(), nullable=True),
        sa.Column("mapping_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["report_file_id"], ["legacy_stock_report_files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.ForeignKeyConstraint(["mapped_product_id"], ["legacy_product_catalog_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_file_id", "row_index", name="uq_legacy_stock_report_rows_file_row"),
    )
    op.create_index(op.f("ix_legacy_stock_report_rows_id"), "legacy_stock_report_rows", ["id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_report_file_id"), "legacy_stock_report_rows", ["report_file_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_tenant_id"), "legacy_stock_report_rows", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_salon_id"), "legacy_stock_report_rows", ["salon_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_row_index"), "legacy_stock_report_rows", ["row_index"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_product_code"), "legacy_stock_report_rows", ["product_code"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_family_code"), "legacy_stock_report_rows", ["family_code"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_mapped_product_id"), "legacy_stock_report_rows", ["mapped_product_id"], unique=False)
    op.create_index(op.f("ix_legacy_stock_report_rows_imported_at"), "legacy_stock_report_rows", ["imported_at"], unique=False)
    op.create_index("ix_legacy_stock_report_rows_mapped_product", "legacy_stock_report_rows", ["mapped_product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_legacy_stock_report_rows_mapped_product", table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_imported_at"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_mapped_product_id"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_family_code"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_product_code"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_row_index"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_salon_id"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_tenant_id"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_report_file_id"), table_name="legacy_stock_report_rows")
    op.drop_index(op.f("ix_legacy_stock_report_rows_id"), table_name="legacy_stock_report_rows")
    op.drop_table("legacy_stock_report_rows")

    op.drop_index("ix_legacy_stock_report_files_salon_type", table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_imported_at"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_parse_status"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_report_generated_at"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_report_month"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_report_year"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_report_type"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_file_ext"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_file_name"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_salon_label"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_salon_id"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_tenant_id"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_batch_id"), table_name="legacy_stock_report_files")
    op.drop_index(op.f("ix_legacy_stock_report_files_id"), table_name="legacy_stock_report_files")
    op.drop_table("legacy_stock_report_files")

    op.drop_index(op.f("ix_legacy_stock_report_batches_imported_at"), table_name="legacy_stock_report_batches")
    op.drop_index(op.f("ix_legacy_stock_report_batches_source_archive_sha256"), table_name="legacy_stock_report_batches")
    op.drop_index(op.f("ix_legacy_stock_report_batches_source_archive_name"), table_name="legacy_stock_report_batches")
    op.drop_index(op.f("ix_legacy_stock_report_batches_tenant_id"), table_name="legacy_stock_report_batches")
    op.drop_index(op.f("ix_legacy_stock_report_batches_id"), table_name="legacy_stock_report_batches")
    op.drop_table("legacy_stock_report_batches")
