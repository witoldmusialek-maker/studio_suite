from datetime import datetime

from pydantic import BaseModel, Field


class PublicSalonRead(BaseModel):
    id: int
    name: str


class PublicServiceRead(BaseModel):
    id: int
    code: str
    name: str
    duration_minutes: int
    price: float


class PublicBundleRead(BaseModel):
    id: int
    code: str
    name: str
    price: float
    duration_minutes: int


class PublicStaffRead(BaseModel):
    id: int
    display_name: str
    public_bio: str | None = None
    public_photo_url: str | None = None


class PublicTimeSlot(BaseModel):
    staff_id: int
    staff_name: str
    start_at: datetime
    end_at: datetime
    duration_minutes: int


class PublicBootstrapResponse(BaseModel):
    salons: list[PublicSalonRead]
    services: list[PublicServiceRead]
    bundles: list[PublicBundleRead]
    staff: list[PublicStaffRead]


class PublicCalendarResponse(BaseModel):
    salon_id: int
    duration_minutes: int
    slots: list[PublicTimeSlot]


class PublicAppointmentCreate(BaseModel):
    salon_id: int
    service_id: int | None = None
    bundle_id: int | None = None
    staff_id: int
    slot: datetime
    client_phone: str = Field(min_length=3, max_length=64)
    client_name: str | None = Field(default=None, max_length=256)
    otp_challenge_id: int | None = None
    otp_code: str | None = Field(default=None, min_length=4, max_length=10)


class PublicAppointmentRead(BaseModel):
    appointment_id: int
    status: str
    salon_id: int
    service_id: int | None = None
    bundle_id: int | None = None
    staff_id: int
    start_at: datetime
    end_at: datetime
    client_phone: str


class PublicOtpRequest(BaseModel):
    salon_id: int
    service_id: int | None = None
    bundle_id: int | None = None
    staff_id: int
    slot: datetime
    client_phone: str = Field(min_length=3, max_length=64)
    client_name: str | None = Field(default=None, max_length=256)


class PublicOtpResponse(BaseModel):
    otp_challenge_id: int
    expires_in_seconds: int
    masked_phone: str
