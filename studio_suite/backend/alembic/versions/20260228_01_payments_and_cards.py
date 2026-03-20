"""payments and cards

Revision ID: 20260228_01_payments_and_cards
Revises: 20260227_01_service_recipe_items
Create Date: 2026-02-28 08:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260228_01_payments_and_cards"
down_revision = "20260227_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("discount_pct", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("expiry", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", name="uq_client_cards_client"),
    )
    op.create_index("ix_client_cards_client_id", "client_cards", ["client_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("salon_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=True),
        sa.Column("client_card_id", sa.Integer(), nullable=True),
        sa.Column("method", sa.String(16), nullable=False, server_default="cash"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("service_gross", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("retail_gross", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("discount_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("paid_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.ForeignKeyConstraint(["client_card_id"], ["client_cards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_salon_time", "payments", ["salon_id", "paid_at"])
    op.create_index("ix_payments_method", "payments", ["method"])

    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("expiry", sa.Date(), nullable=True),
        sa.Column("used_on_payment_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["service_catalog_items.id"]),
        sa.ForeignKeyConstraint(["used_on_payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invitations_client_expiry", "invitations", ["client_id", "expiry"])

    op.create_table(
        "payment_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("item_kind", sa.String(16), nullable=False, server_default="service"),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("invitation_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_gross", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["service_catalog_items.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["legacy_product_catalog_items.id"]),
        sa.ForeignKeyConstraint(["invitation_id"], ["invitations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_lines_payment_kind", "payment_lines", ["payment_id", "item_kind"])


def downgrade() -> None:
    op.drop_index("ix_payment_lines_payment_kind", table_name="payment_lines")
    op.drop_table("payment_lines")
    op.drop_index("ix_invitations_client_expiry", table_name="invitations")
    op.drop_table("invitations")
    op.drop_index("ix_payments_method", table_name="payments")
    op.drop_index("ix_payments_salon_time", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_client_cards_client_id", table_name="client_cards")
    op.drop_table("client_cards")
