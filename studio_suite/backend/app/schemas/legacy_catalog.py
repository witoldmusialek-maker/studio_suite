"""
Schemas for editable legacy catalog (services and bundles) persisted in DB.
"""
from pydantic import BaseModel, Field


class LegacyCatalogServicePriceRow(BaseModel):
    service_id: int
    service_code: str
    service_name: str
    service_segment: str
    salon_id: int
    price: float
    duration_minutes: int
    bookable: bool = True
    is_active: bool
    is_formula: bool
    formula_products: list["LegacyCatalogFormulaProductRow"] = []


class LegacyCatalogFormulaProductRow(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    brand: str | None = None


class LegacyCatalogBundleItemRow(BaseModel):
    position: int
    service_id: int | None
    service_code: str
    service_name: str
    override_price: float | None


class LegacyCatalogBundleRow(BaseModel):
    bundle_id: int
    salon_id: int | None
    bundle_code: str
    bundle_name: str
    price: float
    items: list[LegacyCatalogBundleItemRow]


class LegacyCatalogResponse(BaseModel):
    service_prices: list[LegacyCatalogServicePriceRow]
    bundles: list[LegacyCatalogBundleRow]


class UpdateServicePriceRequest(BaseModel):
    price: float = Field(ge=0)


class UpdateBundlePriceRequest(BaseModel):
    price: float = Field(ge=0)


class UpdateBundleItemPriceRequest(BaseModel):
    override_price: float | None = Field(default=None, ge=0)


class CreateBundleRequest(BaseModel):
    bundle_code: str = Field(min_length=1, max_length=16)
    bundle_name: str = Field(min_length=1, max_length=255)
    salon_id: int = 1


class AddBundleItemRequest(BaseModel):
    service_id: int
    override_price: float | None = Field(default=None, ge=0)


class CreateServiceRequest(BaseModel):
    service_code: str = Field(min_length=1, max_length=16)
    service_name: str = Field(min_length=1, max_length=255)
    service_segment: str = Field(min_length=1, max_length=16)
    duration_minutes: int = Field(default=0, ge=0)
    default_price: float = Field(ge=0)
    bookable: bool = True
    salon_id: int = 1


class UpdateServiceRequest(BaseModel):
    service_name: str | None = Field(default=None, min_length=1, max_length=255)
    service_segment: str | None = Field(default=None, min_length=1, max_length=16)
    duration_minutes: int | None = Field(default=None, ge=0)
    default_price: float | None = Field(default=None, ge=0)
    bookable: bool | None = None
    is_active: bool | None = None
    local_name: str | None = Field(default=None, max_length=255)


class LegacyProductCatalogRow(BaseModel):
    salon_product_id: int
    product_id: int
    product_code: str
    product_name: str
    product_name_pl: str | None = None
    fiscal_code: str | None = None
    brand: str | None = None
    package_size_g: float | None = None
    sale_price_gross: float | None = None
    s_u: bool = False
    doses_short: float
    doses_medium: float
    doses_long: float
    stock_mx03: float | None = None
    stock_mx04: float | None = None
    stock_mx07: float | None = None
    is_active: bool


class UpdateServiceFormulaRequest(BaseModel):
    is_formula: bool
    product_ids: list[int] = []


class LegacyCatalogSyncDiff(BaseModel):
    services_missing_in_db: int
    services_name_diff: int
    services_duration_diff: int
    services_price_diff: int
    bundles_missing_in_db: int
    bundles_name_diff: int
    bundles_price_diff: int
    bundles_items_diff: int
    total: int


class LegacyCatalogSyncReport(BaseModel):
    salon_id: int
    salon_code: str
    salon_name: str
    diff: LegacyCatalogSyncDiff


class LegacyCatalogSyncApplyResult(BaseModel):
    report: LegacyCatalogSyncReport
    created_services: int
    updated_service_names: int
    updated_service_durations: int
    updated_service_prices: int
    created_bundles: int
    updated_bundle_names: int
    rebuilt_bundle_items: int
