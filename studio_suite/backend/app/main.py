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

APP_VERSION = "v1.0.0-beta.2026-02-27.25"

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
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'EMPLOYEE'"))
                conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'RECEPTIONIST'"))
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
            conn.execute(
                text(
                    "ALTER TABLE legacy_product_catalog_items "
                    "ALTER COLUMN legacy_code TYPE VARCHAR(32)"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE salon_service_formula_items "
                    "ALTER COLUMN product_legacy_code TYPE VARCHAR(32)"
                )
            )
            # Additive only migration path for new operational modules.
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
    Base.metadata.create_all(bind=engine)


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
