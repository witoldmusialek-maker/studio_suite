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
    LargeBinary,
    Time,
    UniqueConstraint,
    Index,
)
from sqlalchemy.sql import func

from app.database import Base


class Salon(Base):
    __tablename__ = "salons"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
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
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    # UserRole (admin/manager/employee/receptionist) stays in users for authz.
    # Salon-operational roles (hairdresser/assistant/receptionist/...) are mapped via StaffRole.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("staff_roles.id"), nullable=True, index=True)
    legacy_code = Column(String(16), nullable=True, index=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    display_name = Column(String(256), nullable=False)
    public_bio = Column(Text, nullable=True)
    public_photo_url = Column(String(1024), nullable=True)
    public_photo_data = Column(LargeBinary, nullable=True)
    public_photo_content_type = Column(String(64), nullable=True)
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


class StaffMonthlySchedule(Base):
    __tablename__ = "staff_monthly_schedules"
    __table_args__ = (
        UniqueConstraint("staff_id", "salon_id", "work_date", "time_from", "time_to", name="uq_staff_monthly_schedule_slot"),
        Index("ix_staff_monthly_schedules_staff_date", "staff_id", "work_date"),
        Index("ix_staff_monthly_schedules_salon_date", "salon_id", "work_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
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
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    legacy_code = Column(String(64), nullable=True, index=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    display_name = Column(String(256), nullable=False, index=True)
    phone = Column(String(64), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    first_visit_at = Column(Date, nullable=True)
    last_visit_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClientCard(Base):
    __tablename__ = "client_cards"
    __table_args__ = (
        UniqueConstraint("client_id", name="uq_client_cards_client"),
    )

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    discount_pct = Column(Numeric(6, 2), nullable=False, default=0)
    expiry = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (
        Index("ix_invitations_client_expiry", "client_id", "expiry"),
    )

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=False, index=True)
    expiry = Column(Date, nullable=True, index=True)
    used_on_payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_appointment_type", "appointment_id", "notification_type"),
        Index("ix_notifications_status_created", "status", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    phone = Column(String(64), nullable=False, index=True)
    notification_type = Column(String(32), nullable=False, default="confirmation")
    status = Column(String(16), nullable=False, default="pending", index=True)
    message = Column(String(512), nullable=False)
    provider_message_id = Column(String(64), nullable=True, index=True)
    error_message = Column(String(255), nullable=True)
    sent_at = Column(DateTime(timezone=False), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SmsGatewayPairingCode(Base):
    __tablename__ = "sms_gateway_pairing_codes"
    __table_args__ = (
        Index("ix_sms_gateway_pairing_codes_code", "pair_code", unique=True),
        Index("ix_sms_gateway_pairing_codes_salon_expiry", "salon_id", "expires_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    pair_code = Column(String(32), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=False), nullable=False, index=True)
    is_used = Column(Boolean, nullable=False, default=False, index=True)
    used_at = Column(DateTime(timezone=False), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SmsGatewayDevice(Base):
    __tablename__ = "sms_gateway_devices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "salon_id", "device_uuid", name="uq_sms_gateway_device_tenant_salon_uuid"),
        Index("ix_sms_gateway_devices_salon_active", "salon_id", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    device_uuid = Column(String(128), nullable=False, index=True)
    device_name = Column(String(128), nullable=False)
    endpoint_url = Column(String(512), nullable=False)
    auth_token = Column(String(128), nullable=False)
    app_version = Column(String(32), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_seen_at = Column(DateTime(timezone=False), nullable=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    start_at = Column(DateTime(timezone=False), nullable=False, index=True)
    end_at = Column(DateTime(timezone=False), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="planned")
    allow_overlap = Column(Boolean, nullable=False, default=False)
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
    service_name_snapshot = Column(String(255), nullable=True)
    list_price_snapshot = Column(Numeric(10, 2), nullable=True)
    discount_allocated_snapshot = Column(Numeric(10, 2), nullable=True)
    sold_as_bundle = Column(Boolean, nullable=False, default=False)
    bundle_id_snapshot = Column(Integer, ForeignKey("bundle_catalog.id"), nullable=True, index=True)
    price_snapshot = Column(Numeric(10, 2), nullable=False, default=0)
    performed_at = Column(DateTime(timezone=False), nullable=False, index=True)
    color_product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PerformedLineResource(Base):
    __tablename__ = "performedline_resources"
    __table_args__ = (
        UniqueConstraint("performedline_id", "recipeitem_id", name="uq_performedline_resources_line_recipe"),
        Index("ix_performedline_resources_line", "performedline_id"),
        Index("ix_performedline_resources_product", "product_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    performedline_id = Column(Integer, ForeignKey("appointment_performed_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    recipeitem_id = Column(Integer, ForeignKey("service_recipe_items.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    product_family_snapshot = Column(String(100), nullable=True)
    product_name_snapshot = Column(String(255), nullable=True)
    quantity_used = Column(Numeric(10, 3), nullable=False, default=0)
    quantity_unit = Column(String(20), nullable=True)
    unit_cost_snapshot = Column(Numeric(10, 2), nullable=True)
    total_cost_snapshot = Column(Numeric(10, 2), nullable=True)
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
    bookable = Column(Boolean, nullable=False, default=True)
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


class ProductFamilyDictionary(Base):
    __tablename__ = "product_family_dictionaries"
    __table_args__ = (
        UniqueConstraint("code", name="uq_product_family_dictionaries_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProductFamilyLegacyRule(Base):
    __tablename__ = "product_family_legacy_rules"
    __table_args__ = (
        Index("ix_product_family_legacy_rules_family_sort", "family_id", "sort_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("product_family_dictionaries.id", ondelete="CASCADE"), nullable=False, index=True)
    match_token = Column(String(128), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False, default=100)
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
    variant_code = Column(String(32), nullable=True, index=True)
    position = Column(Integer, nullable=False, default=1)
    product_family = Column(String(100), nullable=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
    product_label_snapshot = Column(String(255), nullable=True)
    is_optional = Column(Boolean, nullable=False, default=False)
    is_required = Column(Boolean, nullable=False, default=True)
    quantity_mode = Column(String(16), nullable=False, default="EXACT")
    planned_quantity = Column(Numeric(10, 3), nullable=False, default=0)
    planned_min = Column(Numeric(10, 3), nullable=True)
    planned_default = Column(Numeric(10, 3), nullable=True)
    planned_max = Column(Numeric(10, 3), nullable=True)
    unit = Column(String(20), nullable=False, default="PCS")
    recipe_unit_label = Column(String(20), nullable=True)
    package_unit_count = Column(Numeric(10, 3), nullable=True)
    package_unit_label = Column(String(20), nullable=True)
    package_size_value = Column(Numeric(10, 3), nullable=True)
    package_size_unit = Column(String(20), nullable=True)
    inventory_mode = Column(String(24), nullable=False, default="PER_SERVICE")
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


class StaffBundleOffer(Base):
    __tablename__ = "staff_bundle_offers"
    __table_args__ = (
        UniqueConstraint("staff_id", "bundle_id", name="uq_staff_bundle_offer_staff_bundle"),
        Index("ix_staff_bundle_offers_salon_staff", "salon_id", "staff_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    bundle_id = Column(Integer, ForeignKey("bundle_catalog.id"), nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    valid_from = Column(DateTime(timezone=False), nullable=True, index=True)
    valid_to = Column(DateTime(timezone=False), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PublicBookingOtpChallenge(Base):
    __tablename__ = "public_booking_otp_challenges"
    __table_args__ = (
        Index("ix_public_booking_otp_phone_created", "phone", "created_at"),
        Index("ix_public_booking_otp_expires", "expires_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    phone = Column(String(64), nullable=False, index=True)
    otp_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime(timezone=False), nullable=False, index=True)
    verified_at = Column(DateTime(timezone=False), nullable=True, index=True)
    attempts_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=False), nullable=True)
    request_ip = Column(String(64), nullable=True)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StockLocation(Base):
    __tablename__ = "stock_locations"
    __table_args__ = (
        UniqueConstraint("salon_id", "code", name="uq_stock_locations_salon_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
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


class SalonProductTargetStock(Base):
    __tablename__ = "salon_product_target_stocks"
    __table_args__ = (
        UniqueConstraint("salon_id", "product_id", name="uq_salon_product_target_stock"),
        Index("ix_salon_product_target_stocks_salon_product", "salon_id", "product_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    target_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ReplenishmentSuggestion(Base):
    __tablename__ = "replenishment_suggestions"
    __table_args__ = (
        Index("ix_replenishment_suggestions_salon_status", "salon_id", "status"),
        Index("ix_replenishment_suggestions_product_status", "product_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    target_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    actual_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    suggested_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    status = Column(String(16), nullable=False, default="OPEN", index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True, index=True)
    note = Column(String(255), nullable=True)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_salon_created", "salon_id", "created_at"),
        Index("ix_purchase_orders_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(16), nullable=False, default="DRAFT", index=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    ordered_at = Column(DateTime(timezone=True), nullable=True)


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_purchase_order_lines_po", "purchase_order_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    target_quantity = Column(Numeric(14, 4), nullable=True)
    actual_quantity = Column(Numeric(14, 4), nullable=True)
    ordered_quantity = Column(Numeric(14, 4), nullable=False, default=0)
    unit = Column(String(8), nullable=False, default="PCS")
    unit_cost = Column(Numeric(12, 4), nullable=True)
    total_cost = Column(Numeric(14, 4), nullable=True)


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        Index("ix_goods_receipts_salon_received", "salon_id", "received_at"),
        Index("ix_goods_receipts_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True, index=True)
    received_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(16), nullable=False, default="DRAFT", index=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"
    __table_args__ = (
        Index("ix_goods_receipt_lines_receipt", "goods_receipt_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    goods_receipt_id = Column(Integer, ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=False, index=True)
    quantity = Column(Numeric(14, 4), nullable=False, default=0)
    unit = Column(String(8), nullable=False, default="PCS")
    unit_cost = Column(Numeric(12, 4), nullable=True)
    total_cost = Column(Numeric(14, 4), nullable=True)


class InventoryIssue(Base):
    __tablename__ = "inventory_issues"
    __table_args__ = (
        Index("ix_inventory_issues_salon_time", "salon_id", "issue_time"),
        Index("ix_inventory_issues_appointment_service_step", "appointment_service_step_id"),
        Index("ix_inventory_issues_performed_line", "performed_line_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
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
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
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
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True, index=True)
    line_kind = Column(String(24), nullable=False, default="product")
    legacy_worker_code_snapshot = Column(String(16), nullable=True)
    legacy_service_code_snapshot = Column(String(32), nullable=True)
    label_snapshot = Column(String(255), nullable=True)
    bundle_id = Column(Integer, ForeignKey("bundle_catalog.id"), nullable=True, index=True)
    bundle_code_snapshot = Column(String(16), nullable=True)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0)
    quantity = Column(Numeric(14, 4), nullable=False, default=1)
    unit = Column(String(8), nullable=False, default="PCS")
    unit_price_gross = Column(Numeric(12, 2), nullable=False, default=0)
    total_price_gross = Column(Numeric(12, 2), nullable=False, default=0)
    fiscal_code = Column(String(32), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_salon_time", "salon_id", "paid_at"),
        Index("ix_payments_method", "method"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True, index=True)
    client_card_id = Column(Integer, ForeignKey("client_cards.id"), nullable=True, index=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=True, index=True)
    method = Column(String(16), nullable=False, default="cash", index=True)
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    service_gross = Column(Numeric(12, 2), nullable=False, default=0)
    retail_gross = Column(Numeric(12, 2), nullable=False, default=0)
    discount_total = Column(Numeric(12, 2), nullable=False, default=0)
    discount_reason_snapshot = Column(String(64), nullable=True)
    promotion_name_snapshot = Column(String(255), nullable=True)
    paid_at = Column(DateTime(timezone=False), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"
    __table_args__ = (
        Index("ix_payment_allocations_payment_method", "payment_id", "method"),
    )

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String(16), nullable=False, default="cash", index=True)
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    voucher_reference = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PaymentLine(Base):
    __tablename__ = "payment_lines"
    __table_args__ = (
        Index("ix_payment_lines_payment_kind", "payment_id", "item_kind"),
    )

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False, index=True)
    item_kind = Column(String(16), nullable=False, default="service")
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
    invitation_id = Column(Integer, ForeignKey("invitations.id"), nullable=True, index=True)
    label = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    total_gross = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())




class CashierCashSession(Base):
    __tablename__ = "cashier_cash_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "salon_id", "business_date", name="uq_cashier_cash_sessions_tenant_salon_date"),
        Index("ix_cashier_cash_sessions_salon_date", "salon_id", "business_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    business_date = Column(Date, nullable=False, index=True)
    opening_cash = Column(Numeric(12, 2), nullable=False, default=0)
    closing_cash = Column(Numeric(12, 2), nullable=True)
    status = Column(String(16), nullable=False, default="OPEN")
    opened_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    closed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CashierExpense(Base):
    __tablename__ = "cashier_expenses"
    __table_args__ = (
        Index("ix_cashier_expenses_salon_date", "salon_id", "expense_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    expense_date = Column(Date, nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expense_type = Column(String(32), nullable=False, default="misc")
    family = Column(String(128), nullable=True)
    label = Column(String(255), nullable=False)
    amount_gross = Column(Numeric(12, 2), nullable=False, default=0)
    vat_amount = Column(Numeric(12, 2), nullable=False, default=0)
    amount_net = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CashierCorrectionAudit(Base):
    __tablename__ = "cashier_correction_audits"
    __table_args__ = (
        Index("ix_cashier_correction_audits_sale", "sale_id", "created_at"),
        Index("ix_cashier_correction_audits_salon", "tenant_id", "salon_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(24), nullable=False, default="VOID", index=True)
    reason = Column(String(512), nullable=False)
    previous_status = Column(String(16), nullable=False)
    new_status = Column(String(16), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class StaffPresenceEntry(Base):
    __tablename__ = "staff_presence_entries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "salon_id", "staff_id", "presence_date", name="uq_staff_presence_tenant_salon_staff_date"),
        Index("ix_staff_presence_salon_date", "salon_id", "presence_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff_members.id"), nullable=False, index=True)
    presence_date = Column(Date, nullable=False, index=True)
    status = Column(String(24), nullable=False, default="PRESENT")
    time_from = Column(Time, nullable=True)
    time_to = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Promotion(Base):
    __tablename__ = "promotions"
    __table_args__ = (
        Index("ix_promotions_validity", "valid_from", "valid_to"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    name = Column(String(255), nullable=False, index=True)
    promotion_type = Column(String(32), nullable=False, default="fixed_discount")
    value = Column(Numeric(12, 2), nullable=False, default=0)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("service_catalog_items.id"), nullable=True, index=True)
    bundle_id = Column(Integer, ForeignKey("bundle_catalog.id"), nullable=True, index=True)
    customer_tier = Column(String(32), nullable=True, index=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LegacyForfaitTransaction(Base):
    __tablename__ = "legacy_forfait_transactions"

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=True, index=True)
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
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_code = Column(String(16), nullable=True, index=True)
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


class LegacyStockReportBatch(Base):
    __tablename__ = "legacy_stock_report_batches"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    source_archive_path = Column(String(512), nullable=False)
    source_archive_name = Column(String(255), nullable=False, index=True)
    source_archive_sha256 = Column(String(64), nullable=True, index=True)
    source_archive_size_bytes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class LegacyStockReportFile(Base):
    __tablename__ = "legacy_stock_report_files"
    __table_args__ = (
        UniqueConstraint("batch_id", "file_name", name="uq_legacy_stock_report_files_batch_file"),
        Index("ix_legacy_stock_report_files_salon_type", "salon_id", "report_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("legacy_stock_report_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    salon_label = Column(String(128), nullable=True, index=True)
    file_name = Column(String(255), nullable=False, index=True)
    file_ext = Column(String(16), nullable=False, index=True)
    report_type = Column(String(64), nullable=False, index=True)
    report_year = Column(Integer, nullable=True, index=True)
    report_month = Column(Integer, nullable=True, index=True)
    report_generated_at = Column(DateTime(timezone=False), nullable=True, index=True)
    row_count = Column(Integer, nullable=False, default=0)
    parse_status = Column(String(32), nullable=False, default="pending", index=True)
    parse_error = Column(Text, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class LegacyStockReportRow(Base):
    __tablename__ = "legacy_stock_report_rows"
    __table_args__ = (
        UniqueConstraint("report_file_id", "row_index", name="uq_legacy_stock_report_rows_file_row"),
        Index("ix_legacy_stock_report_rows_product_code", "product_code"),
        Index("ix_legacy_stock_report_rows_mapped_product", "mapped_product_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    report_file_id = Column(Integer, ForeignKey("legacy_stock_report_files.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    product_code = Column(String(64), nullable=True, index=True)
    product_name_pl = Column(String(255), nullable=True)
    product_name = Column(String(255), nullable=True)
    family_code = Column(String(128), nullable=True, index=True)
    package_label = Column(String(64), nullable=True)
    catalog_price = Column(Numeric(12, 4), nullable=True)
    sale_price_gross = Column(Numeric(12, 4), nullable=True)
    unit_count = Column(Numeric(14, 4), nullable=True)
    counted_units_pcs = Column(Numeric(14, 4), nullable=True)
    counted_units_dose = Column(Numeric(14, 4), nullable=True)
    counted_weight_gross = Column(Numeric(14, 4), nullable=True)
    counted_packages = Column(Numeric(14, 4), nullable=True)
    balance_open = Column(Numeric(14, 4), nullable=True)
    balance_pz = Column(Numeric(14, 4), nullable=True)
    balance_wz_rw = Column(Numeric(14, 4), nullable=True)
    balance_adjustment = Column(Numeric(14, 4), nullable=True)
    balance_close = Column(Numeric(14, 4), nullable=True)
    raw_payload = Column(Text, nullable=True)
    mapped_product_id = Column(Integer, ForeignKey("legacy_product_catalog_items.id"), nullable=True, index=True)
    mapping_confidence = Column(Numeric(5, 4), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
