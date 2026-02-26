"""
Core domain models for salon scheduling and legacy-imported reporting data.
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.sql import func

from app.database import Base


class Salon(Base):
    __tablename__ = "salons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StaffRole(Base):
    __tablename__ = "staff_roles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StaffMember(Base):
    __tablename__ = "staff_members"
    __table_args__ = (
        UniqueConstraint("salon_id", "legacy_code", name="uq_staff_members_salon_legacy_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("staff_roles.id"), nullable=True, index=True)
    legacy_code = Column(String(16), nullable=True, index=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    display_name = Column(String(256), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    legacy_code = Column(String(64), nullable=True, index=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    display_name = Column(String(256), nullable=False, index=True)
    phone = Column(String(64), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    first_visit_at = Column(Date, nullable=True)
    last_visit_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyDictionaryEntry(Base):
    __tablename__ = "legacy_dictionary_entries"
    __table_args__ = (
        UniqueConstraint("dictionary_name", "code", name="uq_legacy_dictionary_name_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dictionary_name = Column(String(64), nullable=False, index=True)
    code = Column(String(32), nullable=False)
    label = Column(String(255), nullable=False)
    extra = Column(String(255), nullable=True)


class ServiceCatalogItem(Base):
    __tablename__ = "service_catalog_items"

    id = Column(Integer, primary_key=True, index=True)
    legacy_code = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    service_type_code = Column(String(16), nullable=True, index=True)
    grouping_code = Column(String(16), nullable=True, index=True)
    family_code = Column(String(16), nullable=True, index=True)
    esthetic_type_code = Column(String(16), nullable=True, index=True)
    vat_code = Column(String(16), nullable=True, index=True)
    duration_minutes = Column(Integer, nullable=False, default=0)
    default_price = Column(Numeric(10, 2), nullable=False, default=0)
    holiday_price = Column(Numeric(10, 2), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ServicePriceHistory(Base):
    __tablename__ = "service_price_history"
    __table_args__ = (
        Index("ix_service_price_history_service_date", "service_id", "valid_from"),
    )

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    holiday_price = Column(Numeric(10, 2), nullable=False, default=0)
    valid_from = Column(Date, nullable=True)
    source = Column(String(64), nullable=False, default="legacy_import")
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class BundleCatalog(Base):
    __tablename__ = "bundle_catalog"

    id = Column(Integer, primary_key=True, index=True)
    legacy_code = Column(String(16), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    frequency_mode = Column(String(32), nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    valid_from = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BundleCatalogItem(Base):
    __tablename__ = "bundle_catalog_items"
    __table_args__ = (
        UniqueConstraint("bundle_id", "position", name="uq_bundle_catalog_items_position"),
    )

    id = Column(Integer, primary_key=True, index=True)
    bundle_id = Column(Integer, ForeignKey("bundle_catalog.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=True, index=True)
    service_legacy_code = Column(String(16), nullable=False, index=True)
    override_price = Column(Numeric(10, 2), nullable=True)


class LegacyForfaitTransaction(Base):
    __tablename__ = "legacy_forfait_transactions"

    id = Column(Integer, primary_key=True, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    date_token = Column(String(32), nullable=True, index=True)
    bundle_code = Column(String(16), nullable=False, index=True)
    bundle_name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyEdServiceRow(Base):
    __tablename__ = "legacy_edservice_rows"

    id = Column(Integer, primary_key=True, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    service_code = Column(String(16), nullable=False, index=True)
    worker_code = Column(String(16), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False, default=0)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyFicheLine(Base):
    __tablename__ = "legacy_fiche_lines"

    id = Column(Integer, primary_key=True, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    ticket_code = Column(String(32), nullable=True, index=True)
    line_code = Column(String(32), nullable=True)
    date_token = Column(String(32), nullable=True, index=True)
    worker_code = Column(String(16), nullable=True, index=True)
    service_code = Column(String(16), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False, default=0)
    payment_hint = Column(String(32), nullable=True, index=True)
    bundle_code = Column(String(16), nullable=True, index=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyEdition1Daily(Base):
    __tablename__ = "legacy_edition1_daily"

    id = Column(Integer, primary_key=True, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    period_major = Column(String(16), nullable=True)
    period_minor = Column(String(16), nullable=True)
    day_number = Column(String(16), nullable=True)
    day_name = Column(String(64), nullable=True)
    date_token = Column(String(32), nullable=True, index=True)
    salon_code = Column(String(16), nullable=True, index=True)
    value_47 = Column(Numeric(12, 2), nullable=False, default=0)
    value_79 = Column(Numeric(12, 2), nullable=False, default=0)
    value_119 = Column(Numeric(12, 2), nullable=False, default=0)
    value_165 = Column(Numeric(12, 2), nullable=False, default=0)
    value_173 = Column(Numeric(12, 2), nullable=False, default=0)
    value_189 = Column(Numeric(12, 2), nullable=False, default=0)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyStat7Row(Base):
    __tablename__ = "legacy_stat7_rows"

    id = Column(Integer, primary_key=True, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    date_token_compact = Column(String(32), nullable=True, index=True)
    worker_code = Column(String(16), nullable=True, index=True)
    payment_a = Column(String(64), nullable=True)
    payment_b = Column(String(64), nullable=True)
    payment_c = Column(String(64), nullable=True)
    worker_name = Column(String(255), nullable=True)
    value_295 = Column(Numeric(12, 2), nullable=False, default=0)
    value_323 = Column(Numeric(12, 2), nullable=False, default=0)
    value_331 = Column(Numeric(12, 2), nullable=False, default=0)
    value_339 = Column(Numeric(12, 2), nullable=False, default=0)
    value_347 = Column(Numeric(12, 2), nullable=False, default=0)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())
