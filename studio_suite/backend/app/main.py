"""
GÄąâ€šÄ‚Ĺ‚wny plik aplikacji FastAPI
"""
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.api.v1 import api_router
from app.database import Base, engine
from app import models  # noqa: F401 - ensure model metadata is registered
from app.services.billing import start_billing_scheduler
from app.services.notifications import start_notification_scheduler
from app.utils.security import get_password_hash

APP_VERSION = "v1.0.0-beta.2026-05-15.T02"

# Utworzenie aplikacji
app = FastAPI(
    title="Studio Suite API",
    description="API dla systemu zarzĂ„â€¦dzania treÄąâ€şciĂ„â€¦ wyÄąâ€şwietlaczy",
    version=APP_VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerÄ‚Ĺ‚w
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.middleware("http")
async def set_security_headers(request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.on_event("startup")
def startup() -> None:
    """Initialize database schema for local/dev environments."""
    if engine.dialect.name == "postgresql":
        # Keep enum in sync on existing deployments without explicit Alembic migrations.
        with engine.begin() as conn:
            enum_exists = conn.execute(
                text("SELECT 1 FROM pg_type WHERE typname = 'userrole'")
            ).scalar()
            if enum_exists:
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'MANAGER'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'MANAGER_MAIN'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'MANAGER_SALON'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'EMPLOYEE'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'RECEPTIONIST'"))
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS tenants ("
                    "id SERIAL PRIMARY KEY, "
                    "code VARCHAR(32) UNIQUE NOT NULL, "
                    "name VARCHAR(128) NOT NULL, "
                    "is_active BOOLEAN NOT NULL DEFAULT TRUE, "
                    "created_at TIMESTAMPTZ DEFAULT now()"
                    ")"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO tenants (id, code, name, is_active) "
                    "VALUES (1, 'DEFAULT', 'Default Tenant', TRUE) "
                    "ON CONFLICT (id) DO NOTHING"
                )
            )
            conn.execute(
                text("UPDATE tenants SET code = :code, name = :name, is_active = TRUE WHERE id = 1"),
                {"code": settings.DEFAULT_TENANT_CODE, "name": settings.DEFAULT_TENANT_NAME},
            )
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_plan VARCHAR(32) NOT NULL DEFAULT 'BASIC'"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(16) NOT NULL DEFAULT 'monthly'"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS monthly_base_price NUMERIC(10,2) NOT NULL DEFAULT 0"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_email VARCHAR(255)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS description TEXT"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS legal_name VARCHAR(255)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tax_id VARCHAR(64)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_address_line1 VARCHAR(255)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_address_line2 VARCHAR(255)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_postal_code VARCHAR(32)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_city VARCHAR(128)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_country VARCHAR(64) NOT NULL DEFAULT 'PL'"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_contact_name VARCHAR(128)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_contact_phone VARCHAR(64)"))
            conn.execute(text("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS billing_due_days INTEGER NOT NULL DEFAULT 14"))
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS tenant_module_licenses ("
                    "id SERIAL PRIMARY KEY, "
                    "tenant_id INTEGER NOT NULL REFERENCES tenants(id), "
                    "module_code VARCHAR(64) NOT NULL, "
                    "is_enabled BOOLEAN NOT NULL DEFAULT TRUE, "
                    "monthly_price NUMERIC(10,2) NOT NULL DEFAULT 0, "
                    "notes VARCHAR(255), "
                    "created_at TIMESTAMPTZ DEFAULT now(), "
                    "updated_at TIMESTAMPTZ DEFAULT now()"
                    ")"
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_module_licenses_tenant_id ON tenant_module_licenses(tenant_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_module_licenses_module_code ON tenant_module_licenses(module_code)"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_module_licenses_tenant_module ON tenant_module_licenses(tenant_id, module_code)"))
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS tenant_billing_invoices ("
                    "id SERIAL PRIMARY KEY, "
                    "tenant_id INTEGER NOT NULL REFERENCES tenants(id), "
                    "period_year INTEGER NOT NULL, "
                    "period_month INTEGER NOT NULL, "
                    "issue_date DATE NOT NULL, "
                    "due_date DATE NOT NULL, "
                    "currency VARCHAR(3) NOT NULL DEFAULT 'PLN', "
                    "base_amount NUMERIC(10,2) NOT NULL DEFAULT 0, "
                    "modules_amount NUMERIC(10,2) NOT NULL DEFAULT 0, "
                    "total_amount NUMERIC(10,2) NOT NULL DEFAULT 0, "
                    "status VARCHAR(24) NOT NULL DEFAULT 'OPEN', "
                    "line_items_json TEXT, "
                    "notes VARCHAR(255), "
                    "sent_at TIMESTAMPTZ NULL, "
                    "paid_at TIMESTAMPTZ NULL, "
                    "created_at TIMESTAMPTZ DEFAULT now(), "
                    "updated_at TIMESTAMPTZ DEFAULT now()"
                    ")"
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_billing_invoices_tenant_period "
                    "ON tenant_billing_invoices(tenant_id, period_year, period_month)"
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_billing_invoices_due_date ON tenant_billing_invoices(due_date)"))
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS tenant_billing_reminder_logs ("
                    "id SERIAL PRIMARY KEY, "
                    "tenant_id INTEGER NOT NULL REFERENCES tenants(id), "
                    "invoice_id INTEGER NOT NULL REFERENCES tenant_billing_invoices(id), "
                    "reminder_kind VARCHAR(64) NOT NULL, "
                    "channel VARCHAR(16) NOT NULL DEFAULT 'EMAIL', "
                    "recipient VARCHAR(255), "
                    "status VARCHAR(24) NOT NULL DEFAULT 'SENT', "
                    "error_message VARCHAR(255), "
                    "sent_at TIMESTAMPTZ DEFAULT now()"
                    ")"
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenant_billing_reminder_logs_invoice_kind "
                    "ON tenant_billing_reminder_logs(invoice_id, reminder_kind)"
                )
            )
            conn.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('tenants','id'), "
                    "(SELECT COALESCE(MAX(id), 1) FROM tenants), true)"
                )
            )
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN NOT NULL DEFAULT FALSE"))
            conn.execute(text("UPDATE users SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_tenant_id') THEN "
                    "ALTER TABLE users ADD CONSTRAINT fk_users_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE user_sessions us SET tenant_id = u.tenant_id FROM users u WHERE us.user_id = u.id AND us.tenant_id IS NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_user_sessions_tenant_id') THEN "
                    "ALTER TABLE user_sessions ADD CONSTRAINT fk_user_sessions_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE salons ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE salons SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE salons ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE salons ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_salons_tenant_id') THEN "
                    "ALTER TABLE salons ADD CONSTRAINT fk_salons_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE staff_members ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE staff_members SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE staff_members ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE staff_members ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_staff_members_tenant_id') THEN "
                    "ALTER TABLE staff_members ADD CONSTRAINT fk_staff_members_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE customers SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE customers ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE customers ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_customers_tenant_id') THEN "
                    "ALTER TABLE customers ADD CONSTRAINT fk_customers_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE appointments SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE appointments ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE appointments ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_appointments_tenant_id') THEN "
                    "ALTER TABLE appointments ADD CONSTRAINT fk_appointments_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE stock_locations ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE stock_locations SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE stock_locations ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE stock_locations ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_stock_locations_tenant_id') THEN "
                    "ALTER TABLE stock_locations ADD CONSTRAINT fk_stock_locations_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE inventory_issues ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE inventory_issues SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE inventory_issues ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE inventory_issues ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_inventory_issues_tenant_id') THEN "
                    "ALTER TABLE inventory_issues ADD CONSTRAINT fk_inventory_issues_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(text("UPDATE sales SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE sales ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE sales ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sales_tenant_id') THEN "
                    "ALTER TABLE sales ADD CONSTRAINT fk_sales_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(
                text(
                    "UPDATE payments p "
                    "SET tenant_id = a.tenant_id "
                    "FROM appointments a "
                    "WHERE p.appointment_id = a.id AND p.tenant_id IS NULL"
                )
            )
            conn.execute(text("UPDATE payments SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE payments ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE payments ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_payments_tenant_id') THEN "
                    "ALTER TABLE payments ADD CONSTRAINT fk_payments_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payments_tenant_id ON payments(tenant_id)"))
            conn.execute(text("ALTER TABLE promotions ADD COLUMN IF NOT EXISTS tenant_id INTEGER"))
            conn.execute(
                text(
                    "UPDATE promotions pr "
                    "SET tenant_id = s.tenant_id "
                    "FROM salons s "
                    "WHERE pr.salon_id = s.id AND pr.tenant_id IS NULL"
                )
            )
            conn.execute(text("UPDATE promotions SET tenant_id = 1 WHERE tenant_id IS NULL"))
            conn.execute(text("ALTER TABLE promotions ALTER COLUMN tenant_id SET DEFAULT 1"))
            conn.execute(text("ALTER TABLE promotions ALTER COLUMN tenant_id SET NOT NULL"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_promotions_tenant_id') THEN "
                    "ALTER TABLE promotions ADD CONSTRAINT fk_promotions_tenant_id "
                    "FOREIGN KEY (tenant_id) REFERENCES tenants(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_promotions_tenant_id ON promotions(tenant_id)"))
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ADD COLUMN IF NOT EXISTS stock_mx03 NUMERIC(12,2)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ADD COLUMN IF NOT EXISTS stock_mx04 NUMERIC(12,2)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ADD COLUMN IF NOT EXISTS stock_mx07 NUMERIC(12,2)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ADD COLUMN IF NOT EXISTS name_pl VARCHAR(255)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ADD COLUMN IF NOT EXISTS fiscal_code VARCHAR(32)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ADD COLUMN IF NOT EXISTS sale_price_gross NUMERIC(10,2)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ADD COLUMN IF NOT EXISTS s_u BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS quantity NUMERIC(12,2)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS catalog_net_price NUMERIC(10,2)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS unit_count NUMERIC(12,2)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS warehouse VARCHAR(64)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS purchase_price NUMERIC(10,2)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS weight NUMERIC(12,4)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS package_weight NUMERIC(12,4)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS min_unit NUMERIC(12,4)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS note VARCHAR(255)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS salon_sale_price NUMERIC(10,2)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS purchase_price_c NUMERIC(10,2)"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items ADD COLUMN IF NOT EXISTS is_locked BOOLEAN NOT NULL DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items DROP COLUMN IF EXISTS upsize_ts"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items DROP COLUMN IF EXISTS catalog_price"))
            conn.execute(text("ALTER TABLE legacy_product_catalog_items DROP COLUMN IF EXISTS ean"))
            conn.execute(text("ALTER TABLE legacy_fiche_lines ADD COLUMN IF NOT EXISTS salon_id INTEGER"))
            conn.execute(text("ALTER TABLE legacy_fiche_lines ADD COLUMN IF NOT EXISTS salon_code VARCHAR(16)"))
            conn.execute(text("ALTER TABLE legacy_forfait_transactions ADD COLUMN IF NOT EXISTS salon_id INTEGER"))
            conn.execute(text("ALTER TABLE legacy_forfait_transactions ADD COLUMN IF NOT EXISTS salon_code VARCHAR(16)"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_legacy_fiche_lines_salon_id') THEN "
                    "ALTER TABLE legacy_fiche_lines ADD CONSTRAINT fk_legacy_fiche_lines_salon_id "
                    "FOREIGN KEY (salon_id) REFERENCES salons(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_legacy_forfait_transactions_salon_id') THEN "
                    "ALTER TABLE legacy_forfait_transactions ADD CONSTRAINT fk_legacy_forfait_transactions_salon_id "
                    "FOREIGN KEY (salon_id) REFERENCES salons(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ALTER COLUMN legacy_code TYPE VARCHAR(32)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE service_catalog_items "
                    "ADD COLUMN IF NOT EXISTS bookable BOOLEAN NOT NULL DEFAULT TRUE"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE salon_service_formula_items "
                    "ALTER COLUMN product_legacy_code TYPE VARCHAR(32)"
                )
            )
            # Additive only migration path for new operational modules.
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64)"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE staff_members ADD COLUMN IF NOT EXISTS user_id INTEGER"))
            conn.execute(text("ALTER TABLE staff_members ADD COLUMN IF NOT EXISTS can_be_booked BOOLEAN NOT NULL DEFAULT TRUE"))
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_staff_members_user_id') THEN "
                    "ALTER TABLE staff_members ADD CONSTRAINT fk_staff_members_user_id "
                    "FOREIGN KEY (user_id) REFERENCES users(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE inventory_issues "
                    "ADD COLUMN IF NOT EXISTS performed_line_id INTEGER"
                )
            )
            conn.execute(
                text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_inventory_issues_performed_line_id') THEN "
                    "ALTER TABLE inventory_issues ADD CONSTRAINT fk_inventory_issues_performed_line_id "
                    "FOREIGN KEY (performed_line_id) REFERENCES appointment_performed_lines(id); "
                    "END IF; "
                    "END $$;"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_inventory_issues_performed_line "
                    "ON inventory_issues(performed_line_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS staff_bundle_offers ("
                    "id SERIAL PRIMARY KEY, "
                    "tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenants(id), "
                    "salon_id INTEGER NOT NULL REFERENCES salons(id), "
                    "staff_id INTEGER NOT NULL REFERENCES staff_members(id), "
                    "bundle_id INTEGER NOT NULL REFERENCES bundle_catalog(id), "
                    "priority INTEGER NOT NULL DEFAULT 100, "
                    "is_active BOOLEAN NOT NULL DEFAULT TRUE, "
                    "valid_from TIMESTAMP NULL, "
                    "valid_to TIMESTAMP NULL, "
                    "created_at TIMESTAMPTZ DEFAULT now(), "
                    "updated_at TIMESTAMPTZ DEFAULT now()"
                    ")"
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_staff_bundle_offer_staff_bundle "
                    "ON staff_bundle_offers(staff_id, bundle_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_staff_bundle_offers_salon_staff "
                    "ON staff_bundle_offers(salon_id, staff_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS public_booking_otp_challenges ("
                    "id SERIAL PRIMARY KEY, "
                    "tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenants(id), "
                    "salon_id INTEGER NOT NULL REFERENCES salons(id), "
                    "phone VARCHAR(64) NOT NULL, "
                    "otp_hash VARCHAR(128) NOT NULL, "
                    "expires_at TIMESTAMP NOT NULL, "
                    "verified_at TIMESTAMP NULL, "
                    "attempts_count INTEGER NOT NULL DEFAULT 0, "
                    "last_attempt_at TIMESTAMP NULL, "
                    "request_ip VARCHAR(64) NULL, "
                    "payload_json TEXT NOT NULL, "
                    "created_at TIMESTAMPTZ DEFAULT now()"
                    ")"
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_public_booking_otp_phone_created ON public_booking_otp_challenges(phone, created_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_public_booking_otp_expires ON public_booking_otp_challenges(expires_at)"))
            superadmin_username = settings.SUPERADMIN_USERNAME.strip().lower()
            existing_superadmin = conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": superadmin_username},
            ).first()
            if existing_superadmin is None:
                conn.execute(
                    text(
                        "INSERT INTO users (tenant_id, username, password_hash, role, is_superadmin, totp_secret, totp_enabled) "
                        "VALUES (1, :username, :password_hash, 'ADMIN', TRUE, :totp_secret, :totp_enabled)"
                    ),
                    {
                        "username": superadmin_username,
                        "password_hash": get_password_hash(settings.SUPERADMIN_PASSWORD),
                        "totp_secret": settings.SUPERADMIN_TOTP_SECRET,
                        "totp_enabled": bool(settings.SUPERADMIN_TOTP_SECRET),
                    },
                )
            else:
                conn.execute(
                    text(
                        "UPDATE users SET tenant_id = 1, role = 'ADMIN', is_superadmin = TRUE "
                        "WHERE username = :username"
                    ),
                    {"username": superadmin_username},
                )
    if engine.dialect.name != "postgresql":
        Base.metadata.create_all(bind=engine)
    start_notification_scheduler()
    start_billing_scheduler()


@app.get("/")
async def root():
    """Endpoint gÄąâ€šÄ‚Ĺ‚wny"""
    return {
        "message": "Studio Suite API",
        "version": APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": APP_VERSION}
