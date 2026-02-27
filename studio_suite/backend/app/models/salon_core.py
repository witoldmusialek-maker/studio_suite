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
    Text,
    Time,
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
    # UserRole (admin/manager/employee/receptionist) stays in users for authz.
    # Salon-operational roles (hairdresser/assistant/receptionist/...) are mapped via StaffRole.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("staff_roles.id"), nullable=True, index=True)
    legacy_code = Column(String(16), nullable=True, index=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    display_name = Column(String(256), nullable=False)
    can_be_booked = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StaffSalonMembership(Base):
    __tablename__ = "staff_salon_memberships"
    __table_args__ = (
        UniqueConstraint("staff_id", "salon_id", name="uq_staff_salon_membership_staff_salon"),
    )

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StaffWeeklySchedule(Base):
    __tablename__ = "staff_weekly_schedules"
    __table_args__ = (
        UniqueConstraint("staff_id", "salon_id", "weekday", "time_from", "time_to", name="uq_staff_weekly_schedule_slot"),
        Index("ix_staff_weekly_schedules_staff_weekday", "staff_id", "weekday"),
    )

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    weekday = Column(Integer, nullable=False, index=True)
    time_from = Column(Time, nullable=False)
    time_to = Column(Time, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StaffTimeOff(Base):
    __tablename__ = "staff_time_off"
    __table_args__ = (
        Index("ix_staff_time_off_staff_period", "staff_id", "start_datetime", "end_datetime"),
    )

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    start_datetime = Column(DateTime(timezone=False), nullable=False, index=True)
    end_datetime = Column(DateTime(timezone=False), nullable=False, index=True)
    reason = Column(String(255), nullable=True)
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


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    start_at = Column(DateTime(timezone=False), nullable=False, index=True)
    end_at = Column(DateTime(timezone=False), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="planned")
    bundle_id = Column(Integer, ForeignKey("bundle_catalog.id"), nullable=True, index=True)
    total_price_snapshot = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppointmentResource(Base):
    __tablename__ = "appointment_resources"
    __table_args__ = (
        UniqueConstraint("appointment_id", "staff_id", name="uq_appointment_resources_appointment_staff"),
    )

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppointmentService(Base):
    __tablename__ = "appointment_services"
    __table_args__ = (
        UniqueConstraint("appointment_id", "service_id", name="uq_appointment_services_appointment_service"),
    )

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppointmentServiceStep(Base):
    __tablename__ = "appointment_service_steps"
    __table_args__ = (
        Index("ix_appointment_service_steps_staff_status", "staff_id", "status"),
        Index("ix_appointment_service_steps_appointment_time", "appointment_id", "planned_start"),
    )

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    appointment_service_id = Column(Integer, ForeignKey("appointment_services.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=False, index=True)
    step_code = Column(String(32), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True, index=True)
    planned_start = Column(DateTime(timezone=False), nullable=True, index=True)
    start_time = Column(DateTime(timezone=False), nullable=True, index=True)
    end_time = Column(DateTime(timezone=False), nullable=True, index=True)
    status = Column(String(16), nullable=False, default="planned")
    uses_materials = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppointmentPerformedLine(Base):
    __tablename__ = "appointment_performed_lines"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=False, index=True)
    worker_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    worker_role_id = Column(Integer, ForeignKey("staff_roles.id"), nullable=False, index=True)
    price_snapshot = Column(Numeric(10, 2), nullable=False, default=0)
    performed_at = Column(DateTime(timezone=False), nullable=False, index=True)
    color_product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
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
    legacy_code = Column(String(32), unique=True, nullable=False, index=True)
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


class SalonServiceCatalogItem(Base):
    __tablename__ = "salon_service_catalog_items"
    __table_args__ = (
        UniqueConstraint("salon_id", "service_id", name="uq_salon_service_catalog_items_salon_service"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=False, index=True)
    local_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyProductCatalogItem(Base):
    __tablename__ = "legacy_product_catalog_items"

    id = Column(Integer, primary_key=True, index=True)
    legacy_code = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_pl = Column(String(255), nullable=True, index=True)
    fiscal_code = Column(String(32), nullable=True, index=True)
    quantity = Column(Numeric(12, 2), nullable=True)
    catalog_net_price = Column(Numeric(10, 2), nullable=True)
    unit_count = Column(Numeric(12, 2), nullable=True)
    warehouse = Column(String(64), nullable=True)
    type_code = Column(String(16), nullable=True, index=True)
    purchase_price = Column(Numeric(10, 2), nullable=True)
    family_code = Column(String(16), nullable=True, index=True)
    brand_1 = Column(String(128), nullable=True)
    brand_2 = Column(String(128), nullable=True)
    weight = Column(Numeric(12, 4), nullable=True)
    package_weight = Column(Numeric(12, 4), nullable=True)
    min_unit = Column(Numeric(12, 4), nullable=True)
    note = Column(String(255), nullable=True)
    salon_sale_price = Column(Numeric(10, 2), nullable=True)
    purchase_price_c = Column(Numeric(10, 2), nullable=True)
    is_locked = Column(Boolean, nullable=False, default=False)
    sale_price_gross = Column(Numeric(10, 2), nullable=True)
    s_u = Column(Boolean, nullable=False, default=False)
    stock_mx03 = Column(Numeric(12, 2), nullable=True, default=0)
    stock_mx04 = Column(Numeric(12, 2), nullable=True, default=0)
    stock_mx07 = Column(Numeric(12, 2), nullable=True, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SalonServiceFormulaItem(Base):
    __tablename__ = "salon_service_formula_items"
    __table_args__ = (
        UniqueConstraint("salon_id", "service_id", "position", name="uq_salon_service_formula_position"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    product_legacy_code = Column(String(32), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SalonProductCatalogItem(Base):
    __tablename__ = "salon_product_catalog_items"
    __table_args__ = (
        UniqueConstraint("salon_id", "product_id", name="uq_salon_product_catalog_items_salon_product"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    local_name = Column(String(255), nullable=True)
    package_size_g = Column(Numeric(10, 2), nullable=True, default=100)
    doses_short = Column(Numeric(10, 2), nullable=False, default=4)
    doses_medium = Column(Numeric(10, 2), nullable=False, default=2)
    doses_long = Column(Numeric(10, 2), nullable=False, default=1.25)
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


class ServiceRecipeItem(Base):
    __tablename__ = "service_recipe_items"
    __table_args__ = (
        Index("ix_service_recipe_items_service_id", "service_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id", ondelete="CASCADE"), nullable=False, index=True)
    product_family = Column(String(100), nullable=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
    planned_quantity = Column(Numeric(10, 3), nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="PCS")
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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


class StockLocation(Base):
    __tablename__ = "stock_locations"
    __table_args__ = (
        UniqueConstraint("salon_id", "code", name="uq_stock_locations_salon_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    code = Column(String(32), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    location_type = Column(String(16), nullable=False, default="MIXED", index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StockLevel(Base):
    __tablename__ = "stock_levels"
    __table_args__ = (
        UniqueConstraint("stock_location_id", "product_id", name="uq_stock_levels_location_product"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_location_id = Column(Integer, ForeignKey("stock_locations.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    quantity = Column(Numeric(14, 4), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InventoryIssue(Base):
    __tablename__ = "inventory_issues"
    __table_args__ = (
        Index("ix_inventory_issues_salon_time", "salon_id", "issue_time"),
        Index("ix_inventory_issues_appointment_service_step", "appointment_service_step_id"),
        Index("ix_inventory_issues_performed_line", "performed_line_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    stock_location_id = Column(Integer, ForeignKey("stock_locations.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=True, index=True)
    performed_line_id = Column(Integer, ForeignKey("appointment_performed_lines.id"), nullable=True, index=True)
    appointment_service_step_id = Column(Integer, ForeignKey("appointment_service_steps.id"), nullable=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True, index=True)
    issue_time = Column(DateTime(timezone=False), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="planned")
    remarks = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryIssueLine(Base):
    __tablename__ = "inventory_issue_lines"
    __table_args__ = (
        Index("ix_inventory_issue_lines_issue_product", "inventory_issue_id", "product_id"),
        Index("ix_inventory_issue_lines_service", "service_id"),
        Index("ix_inventory_issue_lines_performed_line", "performed_line_id"),
        Index("ix_inventory_issue_lines_recipe_item", "recipe_item_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    inventory_issue_id = Column(Integer, ForeignKey("inventory_issues.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=True, index=True)
    recipe_item_id = Column(Integer, ForeignKey("service_recipe_items.id"), nullable=True, index=True)
    # Optional direct pointer to AppointmentPerformedLine.id.
    # Multiple inventory lines may point to one performed line (multi-step material usage).
    performed_line_id = Column(Integer, ForeignKey("appointment_performed_lines.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
    quantity_planned = Column(Numeric(14, 4), nullable=True)
    quantity_actual = Column(Numeric(14, 4), nullable=True)
    unit = Column(String(8), nullable=False, default="PCS")
    unit_cost = Column(Numeric(12, 4), nullable=False, default=0)
    total_cost = Column(Numeric(12, 4), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_salon_time", "salon_id", "sale_time"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    cashier_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sale_time = Column(DateTime(timezone=False), nullable=False, index=True)
    total_gross = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(16), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SaleLine(Base):
    __tablename__ = "sale_lines"
    __table_args__ = (
        Index("ix_sale_lines_sale_product", "sale_id", "product_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    quantity = Column(Numeric(14, 4), nullable=False, default=1)
    unit = Column(String(8), nullable=False, default="PCS")
    unit_price_gross = Column(Numeric(12, 2), nullable=False, default=0)
    total_price_gross = Column(Numeric(12, 2), nullable=False, default=0)
    fiscal_code = Column(String(32), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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


class LegacyImportBatch(Base):
    __tablename__ = "legacy_import_batches"
    __table_args__ = (
        Index("ix_legacy_import_batches_source_salon_code", "source_salon_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_salon_code = Column(String(16), nullable=False)
    source_path = Column(String(512), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class LegacySourceFile(Base):
    __tablename__ = "legacy_source_files"
    __table_args__ = (
        UniqueConstraint("batch_id", "file_name", name="uq_legacy_source_files_batch_file"),
        Index("ix_legacy_source_files_salon_file", "salon_code", "file_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("legacy_import_batches.id"), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=False, index=True)
    file_name = Column(String(64), nullable=False, index=True)
    record_length = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=False, default=0)
    parsed_row_count = Column(Integer, nullable=False, default=0)
    file_size_bytes = Column(Integer, nullable=True)
    sha256 = Column(String(64), nullable=True, index=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyRawRecord(Base):
    __tablename__ = "legacy_raw_records"
    __table_args__ = (
        UniqueConstraint("source_file_id", "row_index", name="uq_legacy_raw_records_source_row"),
        Index("ix_legacy_raw_records_source_token_count", "source_file_id", "token_count"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_file_id = Column(Integer, ForeignKey("legacy_source_files.id"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    token_count = Column(Integer, nullable=False, default=0)
    tokens_payload = Column(Text, nullable=False)
    parse_status = Column(String(32), nullable=False, default="raw")
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyClientCard(Base):
    __tablename__ = "legacy_client_cards"
    __table_args__ = (
        UniqueConstraint("salon_code", "source_row_index", name="uq_legacy_client_cards_salon_row"),
        Index("ix_legacy_client_cards_name", "normalized_name"),
        Index("ix_legacy_client_cards_customer", "mapped_customer_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("legacy_import_batches.id"), nullable=False, index=True)
    source_file_id = Column(Integer, ForeignKey("legacy_source_files.id"), nullable=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=False, index=True)
    source_row_index = Column(Integer, nullable=False)
    label_1 = Column(String(255), nullable=True)
    label_2 = Column(String(255), nullable=True)
    gender = Column(String(8), nullable=True)
    date_token = Column(String(32), nullable=True, index=True)
    service_code_count = Column(Integer, nullable=False, default=0)
    service_codes_sample = Column(String(512), nullable=True)
    normalized_name = Column(String(255), nullable=True, index=True)
    dedupe_key = Column(String(255), nullable=True, index=True)
    mapped_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyHistoryCard(Base):
    __tablename__ = "legacy_history_cards"
    __table_args__ = (
        UniqueConstraint("salon_code", "source_row_index", name="uq_legacy_history_cards_salon_row"),
        Index("ix_legacy_history_cards_name", "normalized_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("legacy_import_batches.id"), nullable=False, index=True)
    source_file_id = Column(Integer, ForeignKey("legacy_source_files.id"), nullable=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=False, index=True)
    source_row_index = Column(Integer, nullable=False)
    surname = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    birth_or_ref = Column(String(64), nullable=True)
    text_events_count = Column(Integer, nullable=False, default=0)
    text_events_sample = Column(Text, nullable=True)
    normalized_name = Column(String(255), nullable=True, index=True)
    mapped_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyWorkerCard(Base):
    __tablename__ = "legacy_worker_cards"
    __table_args__ = (
        UniqueConstraint("salon_code", "source_row_index", name="uq_legacy_worker_cards_salon_row"),
        Index("ix_legacy_worker_cards_salon_worker_code", "salon_code", "worker_code"),
        Index("ix_legacy_worker_cards_staff", "mapped_staff_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("legacy_import_batches.id"), nullable=False, index=True)
    source_file_id = Column(Integer, ForeignKey("legacy_source_files.id"), nullable=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=False, index=True)
    source_row_index = Column(Integer, nullable=False)
    worker_code = Column(String(16), nullable=True)
    first_label = Column(String(255), nullable=True)
    second_label = Column(String(255), nullable=True)
    full_label = Column(String(255), nullable=True)
    category_token = Column(String(64), nullable=True)
    is_probable_employee = Column(Boolean, nullable=False, default=False)
    mapped_staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True, index=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyVisitDocument(Base):
    __tablename__ = "legacy_visit_documents"
    __table_args__ = (
        UniqueConstraint("salon_code", "ticket_code", "date_token", name="uq_legacy_visit_documents_ticket_date"),
        Index("ix_legacy_visit_documents_customer", "mapped_customer_id"),
        Index("ix_legacy_visit_documents_appointment", "mapped_appointment_id"),
        Index("ix_legacy_visit_documents_channel_date", "channel_code", "date_token"),
    )

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("legacy_import_batches.id"), nullable=False, index=True)
    source_file_id = Column(Integer, ForeignKey("legacy_source_files.id"), nullable=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=False, index=True)
    ticket_code = Column(String(32), nullable=False, index=True)
    date_token = Column(String(32), nullable=True, index=True)
    visit_date = Column(Date, nullable=True, index=True)
    channel_code = Column(String(16), nullable=True, index=True)
    mapped_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    mapped_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payment_hint = Column(String(32), nullable=True, index=True)
    source_client_row_index = Column(Integer, nullable=True)
    source_history_row_index = Column(Integer, nullable=True)
    match_rule = Column(String(64), nullable=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyVisitDocumentLine(Base):
    __tablename__ = "legacy_visit_document_lines"
    __table_args__ = (
        UniqueConstraint("document_id", "line_code", "service_code", name="uq_legacy_visit_document_lines_doc_line_service"),
        Index("ix_legacy_visit_document_lines_service", "service_code"),
        Index("ix_legacy_visit_document_lines_worker", "worker_code"),
        Index("ix_legacy_visit_document_lines_mapped_service", "mapped_service_id"),
        Index("ix_legacy_visit_document_lines_mapped_staff", "mapped_staff_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("legacy_visit_documents.id"), nullable=False, index=True)
    source_file_id = Column(Integer, ForeignKey("legacy_source_files.id"), nullable=True, index=True)
    source_row_index = Column(Integer, nullable=False, index=True)
    line_code = Column(String(32), nullable=True)
    service_code = Column(String(16), nullable=False)
    worker_code = Column(String(16), nullable=True)
    qty_token = Column(String(32), nullable=True)
    state_flag = Column(String(16), nullable=True)
    kind_flag = Column(String(16), nullable=True)
    group_code = Column(String(16), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False, default=0)
    price_token_raw = Column(String(64), nullable=True)
    mapped_service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=True, index=True)
    mapped_staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True, index=True)
    mapped_performed_line_id = Column(Integer, ForeignKey("appointment_performed_lines.id"), nullable=True, index=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyCustomerMatch(Base):
    __tablename__ = "legacy_customer_matches"
    __table_args__ = (
        Index("ix_legacy_customer_matches_confidence", "confidence"),
        Index("ix_legacy_customer_matches_target", "customer_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=False, index=True)
    client_card_id = Column(Integer, ForeignKey("legacy_client_cards.id"), nullable=True, index=True)
    history_card_id = Column(Integer, ForeignKey("legacy_history_cards.id"), nullable=True, index=True)
    visit_document_id = Column(Integer, ForeignKey("legacy_visit_documents.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    match_rule = Column(String(64), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False, default=0)
    is_accepted = Column(Boolean, nullable=False, default=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
