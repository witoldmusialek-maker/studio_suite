"""
Schemas for booking module (clients, appointments, execution lines).
"""
from datetime import date, datetime, time

from pydantic import BaseModel, Field


class BookingSalon(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool


class BookingStaffRole(BaseModel):
    id: int
    code: str
    name: str


class BookingStaffResource(BaseModel):
    id: int
    salon_id: int
    name: str
    role_ids: list[int]


class BookingClient(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str | None = None


class BookingService(BaseModel):
    id: int
    code: str
    name: str
    duration_minutes: int


class BookingPriceListItem(BaseModel):
    id: int
    salon_id: int
    service_id: int
    price: float


class BookingBundleItem(BaseModel):
    service_id: int
    override_price: float | None = None


class BookingBundle(BaseModel):
    id: int
    salon_id: int
    code: str
    name: str
    price: float
    items: list[BookingBundleItem]


class BookingColorProduct(BaseModel):
    id: int
    code: str
    name: str
    brand: str


class BookingAppointment(BaseModel):
    id: int
    salon_id: int
    client_id: int
    start_at: str
    end_at: str
    status: str
    allow_overlap: bool = False
    resources: list[int]
    services: list[int]
    bundle_id: int | None = None
    total_price_snapshot: float


class BookingPerformedServiceLine(BaseModel):
    id: int
    appointment_id: int
    service_id: int
    service_name_snapshot: str | None = None
    worker_id: int
    worker_role_id: int
    list_price_snapshot: float | None = None
    discount_allocated_snapshot: float | None = None
    sold_as_bundle: bool = False
    bundle_id_snapshot: int | None = None
    price_snapshot: float
    performed_at: str
    color_product_id: int | None = None


class BookingPerformedLineResourceRead(BaseModel):
    performed_line_id: int
    service_id: int
    service_name: str | None = None
    worker_id: int
    worker_name: str | None = None
    worker_role_id: int
    worker_role_name: str | None = None
    product_id: int
    product_family: str | None = None
    product_name: str | None = None
    quantity_used: float
    quantity_unit: str | None = None
    unit_cost_snapshot: float | None = None
    total_cost_snapshot: float | None = None


class BookingSmsNotifyRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=64)


class BookingSmsNotifyResponse(BaseModel):
    notification_id: int
    appointment_id: int
    phone: str
    status: str
    notification_type: str
    error_message: str | None = None


class BookingSmsBatchResponse(BaseModel):
    sent: int
    failed: int


class BookingBootstrapResponse(BaseModel):
    salons: list[BookingSalon]
    staffRoles: list[BookingStaffRole]
    resources: list[BookingStaffResource]
    clients: list[BookingClient]
    services: list[BookingService]
    priceListItems: list[BookingPriceListItem]
    bundles: list[BookingBundle]
    colorProducts: list[BookingColorProduct]
    appointments: list[BookingAppointment]
    performedServiceLines: list[BookingPerformedServiceLine]


class BookingClientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=256)
    phone: str = Field(min_length=1, max_length=64)
    email: str | None = Field(default=None, max_length=255)


class BookingClientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=256)
    phone: str | None = Field(default=None, min_length=1, max_length=64)
    email: str | None = Field(default=None, max_length=255)


class BookingAppointmentCreate(BaseModel):
    salon_id: int
    client_id: int
    start_at: datetime
    end_at: datetime
    resources: list[int] = Field(default_factory=list)
    services: list[int] = Field(default_factory=list)
    allow_overlap: bool = False
    bundle_id: int | None = None
    total_price_snapshot: float = Field(ge=0, default=0)


class BookingExecutionResourceCreate(BaseModel):
    recipe_item_id: int
    product_id: int
    quantity_used: float = Field(gt=0)
    quantity_unit: str | None = Field(default=None, max_length=20)


class BookingExecutionLineCreate(BaseModel):
    service_id: int
    worker_id: int
    worker_role_id: int
    price_snapshot: float = Field(ge=0)
    color_product_id: int | None = None
    resources: list[BookingExecutionResourceCreate] = Field(default_factory=list)


class BookingAppointmentComplete(BaseModel):
    performed_at: datetime
    lines: list[BookingExecutionLineCreate] = Field(min_length=1)


class BookingSalonStaffMember(BaseModel):
    id: int
    user_id: int | None = None
    role_id: int | None = None
    role_code: str | None = None
    salon_id: int | None = None
    display_name: str
    first_name: str | None = None
    last_name: str | None = None
    can_be_booked: bool
    is_active: bool


class BookingStaffLocationRead(BaseModel):
    salon_id: int
    salon_name: str | None = None
    is_primary: bool
    is_active: bool


class BookingStaffLocationWrite(BaseModel):
    salon_id: int
    is_primary: bool = False


class BookingStaffBundleOfferRead(BaseModel):
    staff_id: int
    bundle_id: int
    bundle_code: str
    bundle_name: str
    priority: int = 100
    is_active: bool = True


class BookingStaffBundleOfferWriteItem(BaseModel):
    bundle_id: int
    priority: int = 100
    is_active: bool = True


class BookingStaffBundleOfferWrite(BaseModel):
    offers: list[BookingStaffBundleOfferWriteItem] = Field(default_factory=list)


class BookingStatsResponse(BaseModel):
    salons: int
    clients: int
    appointments: int
    planned_appointments: int
    completed_appointments: int
    available_staff: int
    appointments_in_progress: int = 0
    revenue_today: float = 0


class BookingStaffWeeklyScheduleCreate(BaseModel):
    salon_id: int
    weekday: int = Field(ge=0, le=6)
    time_from: time
    time_to: time
    is_active: bool = True


class BookingStaffWeeklyScheduleUpdate(BaseModel):
    salon_id: int | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    time_from: time | None = None
    time_to: time | None = None
    is_active: bool | None = None


class BookingStaffWeeklyScheduleRead(BaseModel):
    id: int
    staff_id: int
    salon_id: int
    weekday: int
    time_from: time
    time_to: time
    is_active: bool


class BookingStaffMonthlyScheduleRead(BaseModel):
    id: int
    staff_id: int
    salon_id: int
    work_date: date
    time_from: time
    time_to: time
    is_active: bool


class BookingStaffMonthlyScheduleWriteItem(BaseModel):
    salon_id: int
    work_date: date
    time_from: time
    time_to: time
    is_active: bool = True


class BookingStaffMonthlyScheduleReplace(BaseModel):
    date_from: date
    date_to: date
    entries: list[BookingStaffMonthlyScheduleWriteItem] = Field(default_factory=list)


class BookingStaffTimeOffCreate(BaseModel):
    salon_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: str | None = Field(default=None, max_length=255)


class BookingStaffTimeOffUpdate(BaseModel):
    salon_id: int | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    reason: str | None = Field(default=None, max_length=255)


class BookingStaffTimeOffRead(BaseModel):
    id: int
    staff_id: int
    salon_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: str | None = None


class BookingAvailabilitySlot(BaseModel):
    start_at: datetime
    end_at: datetime


class BookingAvailabilityStaffSlots(BaseModel):
    staff_id: int
    staff_name: str
    slots: list[BookingAvailabilitySlot]


class BookingAvailabilityResponse(BaseModel):
    salon_id: int
    date: date
    total_duration_minutes: int
    service_ids: list[int]
    preferred_staff_id: int | None = None
    results: list[BookingAvailabilityStaffSlots]
