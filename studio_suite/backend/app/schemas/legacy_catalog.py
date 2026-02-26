"""
Schemas for editable legacy catalog (services and bundles) persisted in DB.
"""
from pydantic import BaseModel, Field


class LegacyCatalogServicePriceRow(BaseModel):
    service_id: int
    service_code: str
    service_name: str
    salon_id: int
    price: float
    duration_minutes: int
    is_active: bool


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
    duration_minutes: int = Field(default=0, ge=0)
    default_price: float = Field(ge=0)
    salon_id: int = 1


class UpdateServiceRequest(BaseModel):
    service_name: str | None = Field(default=None, min_length=1, max_length=255)
    duration_minutes: int | None = Field(default=None, ge=0)
    default_price: float | None = Field(default=None, ge=0)
    is_active: bool | None = None
    local_name: str | None = Field(default=None, max_length=255)
