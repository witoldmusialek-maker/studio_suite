from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.salon_core import Salon, SmsGatewayDevice, SmsGatewayPairingCode

router = APIRouter(prefix="/auth", tags=["public-auth"])


class SmsGatewayRegisterRequest(BaseModel):
    pair_code: str = Field(min_length=4, max_length=32)
    device_name: str = Field(min_length=1, max_length=128)
    device_uuid: str = Field(min_length=6, max_length=128)
    endpoint_url: str = Field(min_length=12, max_length=512)
    app_version: str | None = Field(default=None, max_length=32)


class SmsGatewayRegisterResponse(BaseModel):
    device_id: int
    salon_id: int
    salon_name: str | None = None
    auth_token: str


def _normalize_pair_code(value: str) -> str:
    return "".join(ch for ch in (value or "").strip().upper() if ch.isalnum())


def _validate_endpoint_url(endpoint_url: str) -> str:
    cleaned = (endpoint_url or "").strip()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_url is required")
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_url must start with http:// or https://")
    if not cleaned.endswith("/send"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_url must end with /send")
    return cleaned


@router.post("/sms-gateway/register", response_model=SmsGatewayRegisterResponse)
async def register_sms_gateway_device(
    payload: SmsGatewayRegisterRequest,
    db: Session = Depends(get_db),
):
    pair_code = _normalize_pair_code(payload.pair_code)
    if len(pair_code) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pairing code")

    pairing = (
        db.query(SmsGatewayPairingCode)
        .filter(
            SmsGatewayPairingCode.pair_code == pair_code,
            SmsGatewayPairingCode.is_used.is_(False),
            SmsGatewayPairingCode.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not pairing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pairing code invalid or expired")

    endpoint_url = _validate_endpoint_url(payload.endpoint_url)
    device_uuid = (payload.device_uuid or "").strip()
    if not device_uuid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="device_uuid is required")

    auth_token = secrets.token_hex(32)
    now = datetime.utcnow()

    row = (
        db.query(SmsGatewayDevice)
        .filter(
            SmsGatewayDevice.tenant_id == pairing.tenant_id,
            SmsGatewayDevice.salon_id == pairing.salon_id,
            SmsGatewayDevice.device_uuid == device_uuid,
        )
        .first()
    )
    if row:
        row.device_name = payload.device_name.strip()[:128]
        row.endpoint_url = endpoint_url
        row.auth_token = auth_token
        row.app_version = (payload.app_version or "").strip()[:32] or None
        row.is_active = True
        row.last_seen_at = now
    else:
        row = SmsGatewayDevice(
            tenant_id=pairing.tenant_id,
            salon_id=pairing.salon_id,
            device_uuid=device_uuid,
            device_name=payload.device_name.strip()[:128],
            endpoint_url=endpoint_url,
            auth_token=auth_token,
            app_version=(payload.app_version or "").strip()[:32] or None,
            is_active=True,
            last_seen_at=now,
            created_by_user_id=pairing.created_by_user_id,
        )
        db.add(row)

    pairing.is_used = True
    pairing.used_at = now
    db.commit()
    db.refresh(row)

    salon = db.query(Salon).filter(Salon.id == row.salon_id).first()
    return SmsGatewayRegisterResponse(
        device_id=row.id,
        salon_id=row.salon_id,
        salon_name=salon.name if salon else None,
        auth_token=auth_token,
    )
