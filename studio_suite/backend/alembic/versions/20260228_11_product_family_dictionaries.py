"""product family dictionaries

Revision ID: 20260228_11
Revises: 20260228_10
Create Date: 2026-02-28 22:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260228_11"
down_revision = "20260228_10"
branch_labels = None
depends_on = None


DEFAULT_FAMILIES = [
    ("SZAMPON", "SZAMPON", "Szampony zabiegowe", 10),
    ("FARBA", "FARBA", "Farby i koloryzacja", 20),
    ("MASKA", "MASKA", "Maski zabiegowe", 30),
    ("OXYDANTY", "OXYDANTY", "Utleniacze i aktywatory", 40),
    ("ARTYKULY_JEDNORAZOWE", "ARTYKUŁY JEDNORAZOWE", "Jednorazowe materialy pomocnicze", 50),
]

DEFAULT_RULES = {
    "SZAMPON": ["SZAMPON", "SHAMPOO"],
    "FARBA": ["FARBA", "MAJIREL", "COLOR"],
    "MASKA": ["MASKA"],
    "OXYDANTY": ["OXYD", "UTLEN", "AKTYWAT"],
    "ARTYKULY_JEDNORAZOWE": ["ARTYKU", "JEDNORAZ", "AKCESOR", "RĘKAW", "REKAW", "PELERYN", "FOLIA", "CZEPEK", "PAPIER", "WATA", "RĘCZNIK", "RECZNIK"],
}


def upgrade() -> None:
    op.create_table(
        "product_family_dictionaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_product_family_dictionaries_code"),
    )
    op.create_index(op.f("ix_product_family_dictionaries_id"), "product_family_dictionaries", ["id"], unique=False)
    op.create_index(op.f("ix_product_family_dictionaries_code"), "product_family_dictionaries", ["code"], unique=False)

    op.create_table(
        "product_family_legacy_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("match_token", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["family_id"], ["product_family_dictionaries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_family_legacy_rules_id"), "product_family_legacy_rules", ["id"], unique=False)
    op.create_index(op.f("ix_product_family_legacy_rules_family_id"), "product_family_legacy_rules", ["family_id"], unique=False)
    op.create_index(op.f("ix_product_family_legacy_rules_match_token"), "product_family_legacy_rules", ["match_token"], unique=False)
    op.create_index("ix_product_family_legacy_rules_family_sort", "product_family_legacy_rules", ["family_id", "sort_order"], unique=False)

    conn = op.get_bind()
    family_table = sa.table(
        "product_family_dictionaries",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    rule_table = sa.table(
        "product_family_legacy_rules",
        sa.column("family_id", sa.Integer),
        sa.column("match_token", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        family_table,
        [
            {
                "id": index + 1,
                "code": code,
                "name": name,
                "description": description,
                "sort_order": sort_order,
                "is_active": True,
            }
            for index, (code, name, description, sort_order) in enumerate(DEFAULT_FAMILIES)
        ],
    )

    rule_rows = []
    family_id_by_code = {code: index + 1 for index, (code, _name, _desc, _sort) in enumerate(DEFAULT_FAMILIES)}
    for family_code, tokens in DEFAULT_RULES.items():
        family_id = family_id_by_code[family_code]
        for position, token in enumerate(tokens, start=1):
            rule_rows.append(
                {
                    "family_id": family_id,
                    "match_token": token,
                    "sort_order": position * 10,
                    "is_active": True,
                }
            )
    op.bulk_insert(rule_table, rule_rows)

    conn.execute(sa.text("SELECT setval('product_family_dictionaries_id_seq', (SELECT COALESCE(MAX(id), 1) FROM product_family_dictionaries), true)"))


def downgrade() -> None:
    op.drop_index("ix_product_family_legacy_rules_family_sort", table_name="product_family_legacy_rules")
    op.drop_index(op.f("ix_product_family_legacy_rules_match_token"), table_name="product_family_legacy_rules")
    op.drop_index(op.f("ix_product_family_legacy_rules_family_id"), table_name="product_family_legacy_rules")
    op.drop_index(op.f("ix_product_family_legacy_rules_id"), table_name="product_family_legacy_rules")
    op.drop_table("product_family_legacy_rules")
    op.drop_index(op.f("ix_product_family_dictionaries_code"), table_name="product_family_dictionaries")
    op.drop_index(op.f("ix_product_family_dictionaries_id"), table_name="product_family_dictionaries")
    op.drop_table("product_family_dictionaries")
