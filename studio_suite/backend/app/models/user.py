"""
Model użytkownika
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, ForeignKey, Index, Boolean, Numeric, Text
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """Role użytkowników"""
    ADMIN = "admin"
    MANAGER = "manager"
    MANAGER_MAIN = "manager_main"
    MANAGER_SALON = "manager_salon"
    EMPLOYEE = "employee"
    RECEPTIONIST = "receptionist"
    OPERATOR_DISPLAYS = "operator_displays"
    OPERATOR_BELLS = "operator_bells"
    OPERATOR = "operator"  # legacy alias; traktowany jak operator wyświetlaczy


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    billing_plan = Column(String(32), nullable=False, default="BASIC", server_default="BASIC")
    billing_cycle = Column(String(16), nullable=False, default="monthly", server_default="monthly")
    monthly_base_price = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    billing_email = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    legal_name = Column(String(255), nullable=True)
    tax_id = Column(String(64), nullable=True)
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_postal_code = Column(String(32), nullable=True)
    billing_city = Column(String(128), nullable=True)
    billing_country = Column(String(64), nullable=False, default="PL", server_default="PL")
    billing_contact_name = Column(String(128), nullable=True)
    billing_contact_phone = Column(String(64), nullable=True)
    billing_due_days = Column(Integer, nullable=False, default=14, server_default="14")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TenantModuleLicense(Base):
    __tablename__ = "tenant_module_licenses"
    __table_args__ = (
        Index("ix_tenant_module_licenses_tenant_module", "tenant_id", "module_code", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    module_code = Column(String(64), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    monthly_price = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base):
    """Model użytkownika"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, default=1, server_default="1")
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_superadmin = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_last_seen", "last_seen"),
        Index("ix_user_sessions_user_last_seen", "user_id", "last_seen"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=True, index=True)
    session_key = Column(String(64), nullable=False, unique=True, index=True)
    user_role = Column(String(32), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    last_seen = Column(DateTime(timezone=False), nullable=False, server_default=func.now())


class TenantBillingInvoice(Base):
    __tablename__ = "tenant_billing_invoices"
    __table_args__ = (
        Index("ix_tenant_billing_invoices_tenant_period", "tenant_id", "period_year", "period_month", unique=True),
        Index("ix_tenant_billing_invoices_due_date", "due_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    currency = Column(String(3), nullable=False, default="PLN", server_default="PLN")
    base_amount = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    modules_amount = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    total_amount = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    status = Column(String(24), nullable=False, default="OPEN", server_default="OPEN")
    line_items_json = Column(Text, nullable=True)
    notes = Column(String(255), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantBillingReminderLog(Base):
    __tablename__ = "tenant_billing_reminder_logs"
    __table_args__ = (
        Index("ix_tenant_billing_reminder_logs_invoice_kind", "invoice_id", "reminder_kind", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("tenant_billing_invoices.id"), nullable=False, index=True)
    reminder_kind = Column(String(64), nullable=False)
    channel = Column(String(16), nullable=False, default="EMAIL", server_default="EMAIL")
    recipient = Column(String(255), nullable=True)
    status = Column(String(24), nullable=False, default="SENT", server_default="SENT")
    error_message = Column(String(255), nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
