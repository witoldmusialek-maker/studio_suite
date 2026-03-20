"""sms gateway pairing and devices

Revision ID: 20260314_05
Revises: 20260314_04
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260314_05"
down_revision = "20260314_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sms_gateway_pairing_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("salon_id", sa.Integer(), nullable=False),
        sa.Column("pair_code", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("used_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sms_gateway_pairing_codes_code", "sms_gateway_pairing_codes", ["pair_code"], unique=True)
    op.create_index("ix_sms_gateway_pairing_codes_salon_expiry", "sms_gateway_pairing_codes", ["salon_id", "expires_at"])
    op.create_index(op.f("ix_sms_gateway_pairing_codes_id"), "sms_gateway_pairing_codes", ["id"], unique=False)
    op.create_index(op.f("ix_sms_gateway_pairing_codes_tenant_id"), "sms_gateway_pairing_codes", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_sms_gateway_pairing_codes_salon_id"), "sms_gateway_pairing_codes", ["salon_id"], unique=False)
    op.create_index(op.f("ix_sms_gateway_pairing_codes_pair_code"), "sms_gateway_pairing_codes", ["pair_code"], unique=False)
    op.create_index(op.f("ix_sms_gateway_pairing_codes_expires_at"), "sms_gateway_pairing_codes", ["expires_at"], unique=False)
    op.create_index(op.f("ix_sms_gateway_pairing_codes_is_used"), "sms_gateway_pairing_codes", ["is_used"], unique=False)
    op.create_index(op.f("ix_sms_gateway_pairing_codes_created_by_user_id"), "sms_gateway_pairing_codes", ["created_by_user_id"], unique=False)

    op.create_table(
        "sms_gateway_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("salon_id", sa.Integer(), nullable=False),
        sa.Column("device_uuid", sa.String(length=128), nullable=False),
        sa.Column("device_name", sa.String(length=128), nullable=False),
        sa.Column("endpoint_url", sa.String(length=512), nullable=False),
        sa.Column("auth_token", sa.String(length=128), nullable=False),
        sa.Column("app_version", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_seen_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["salon_id"], ["salons.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "salon_id", "device_uuid", name="uq_sms_gateway_device_tenant_salon_uuid"),
    )
    op.create_index("ix_sms_gateway_devices_salon_active", "sms_gateway_devices", ["salon_id", "is_active"])
    op.create_index(op.f("ix_sms_gateway_devices_id"), "sms_gateway_devices", ["id"], unique=False)
    op.create_index(op.f("ix_sms_gateway_devices_tenant_id"), "sms_gateway_devices", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_sms_gateway_devices_salon_id"), "sms_gateway_devices", ["salon_id"], unique=False)
    op.create_index(op.f("ix_sms_gateway_devices_device_uuid"), "sms_gateway_devices", ["device_uuid"], unique=False)
    op.create_index(op.f("ix_sms_gateway_devices_is_active"), "sms_gateway_devices", ["is_active"], unique=False)
    op.create_index(op.f("ix_sms_gateway_devices_last_seen_at"), "sms_gateway_devices", ["last_seen_at"], unique=False)
    op.create_index(op.f("ix_sms_gateway_devices_created_by_user_id"), "sms_gateway_devices", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sms_gateway_devices_created_by_user_id"), table_name="sms_gateway_devices")
    op.drop_index(op.f("ix_sms_gateway_devices_last_seen_at"), table_name="sms_gateway_devices")
    op.drop_index(op.f("ix_sms_gateway_devices_is_active"), table_name="sms_gateway_devices")
    op.drop_index(op.f("ix_sms_gateway_devices_device_uuid"), table_name="sms_gateway_devices")
    op.drop_index(op.f("ix_sms_gateway_devices_salon_id"), table_name="sms_gateway_devices")
    op.drop_index(op.f("ix_sms_gateway_devices_tenant_id"), table_name="sms_gateway_devices")
    op.drop_index(op.f("ix_sms_gateway_devices_id"), table_name="sms_gateway_devices")
    op.drop_index("ix_sms_gateway_devices_salon_active", table_name="sms_gateway_devices")
    op.drop_table("sms_gateway_devices")

    op.drop_index(op.f("ix_sms_gateway_pairing_codes_created_by_user_id"), table_name="sms_gateway_pairing_codes")
    op.drop_index(op.f("ix_sms_gateway_pairing_codes_is_used"), table_name="sms_gateway_pairing_codes")
    op.drop_index(op.f("ix_sms_gateway_pairing_codes_expires_at"), table_name="sms_gateway_pairing_codes")
    op.drop_index(op.f("ix_sms_gateway_pairing_codes_pair_code"), table_name="sms_gateway_pairing_codes")
    op.drop_index(op.f("ix_sms_gateway_pairing_codes_salon_id"), table_name="sms_gateway_pairing_codes")
    op.drop_index(op.f("ix_sms_gateway_pairing_codes_tenant_id"), table_name="sms_gateway_pairing_codes")
    op.drop_index(op.f("ix_sms_gateway_pairing_codes_id"), table_name="sms_gateway_pairing_codes")
    op.drop_index("ix_sms_gateway_pairing_codes_salon_expiry", table_name="sms_gateway_pairing_codes")
    op.drop_index("ix_sms_gateway_pairing_codes_code", table_name="sms_gateway_pairing_codes")
    op.drop_table("sms_gateway_pairing_codes")
