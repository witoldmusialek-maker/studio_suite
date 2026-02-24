"""
Endpointy API dla dzwonkĂłw szkolnych
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, time

from app.database import get_db
from app.models.bell_schedule import BellSchedule
from app.models.bell_history import BellHistory
from app.models.bell_runtime import BellCalendarOverride
from app.models.bell_profile import BellProfile, BellProfileOverride, BellScheduleProfile, BellProfilePlaceholder
from app.models.bell_music import BellMusicSchedule, BellMusicTrack
from app.models.bell_sound import BellSound
from app.models.bell_model_config import BellModelConfig
from app.models.user import User
from app.api.deps import get_current_user, get_current_admin
from app.schemas.bell import (
    BellScheduleCreate,
    BellScheduleUpdate,
    BellScheduleResponse,
    BellHistoryResponse,
    BellPlayCommand,
    BellMarkPlayedRequest,
    BellRuntimePauseRequest,
    BellRuntimeControlResponse,
    BellCalendarOverrideCreate,
    BellCalendarOverrideResponse,
    BellProfileCreate,
    BellProfileUpdate,
    BellProfileResponse,
    BellProfileOverrideCreate,
    BellProfileOverrideResponse,
    BellScheduleProfilesUpdate,
    BellSoundResponse,
    BellSoundRenameRequest,
    BellProfilePlaceholderUpsert,
    BellProfilePlaceholderResponse,
    BellMusicScheduleCreate,
    BellMusicScheduleUpdate,
    BellMusicScheduleResponse,
    BellMusicTrackCreate,
    BellMusicTrackResponse,
    BellModelConfigUpsert,
    BellModelConfigResponse,
)
from app.services.bell_service import (
    get_displays_for_bell,
    log_bell_play,
    get_or_create_runtime_control,
    get_active_bell_profile,
    get_bells_to_play,
    is_bell_playback_blocked,
)
from app.services.bell_music_service import get_active_music_schedule, get_active_music_tracks
from app.services.display_runtime_state import is_display_playing_video
from app.utils.time_utils import local_now
from app.config import settings
import os
import shutil
import re

router = APIRouter(prefix="/bells", tags=["bells"])

_SOUND_REF_PREFIX = "sound:"
_PLACEHOLDER_REF_PREFIX = "placeholder:"


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
    return cleaned or "sound.wav"


def _build_track_ref(sound_id: Optional[int], placeholder_key: Optional[str], file_path: Optional[str]) -> str:
    if sound_id is not None:
        return f"{_SOUND_REF_PREFIX}{int(sound_id)}"
    if placeholder_key:
        return f"{_PLACEHOLDER_REF_PREFIX}{placeholder_key.strip().upper()}"
    return (file_path or "").strip()


def _parse_track_ref(file_path: str) -> tuple[Optional[int], Optional[str]]:
    if file_path.startswith(_SOUND_REF_PREFIX):
        raw = file_path[len(_SOUND_REF_PREFIX):]
        try:
            return int(raw), None
        except ValueError:
            return None, None
    if file_path.startswith(_PLACEHOLDER_REF_PREFIX):
        key = file_path[len(_PLACEHOLDER_REF_PREFIX):].strip().upper()
        return None, key or None
    return None, None


def _resolve_placeholder_sound_id(
    db: Session,
    profile_id: Optional[int],
    placeholder_key: Optional[str],
) -> Optional[int]:
    if not profile_id or not placeholder_key:
        return None
    mapping = db.query(BellProfilePlaceholder).filter(
        BellProfilePlaceholder.profile_id == profile_id,
        BellProfilePlaceholder.placeholder_key == placeholder_key,
    ).first()
    return mapping.sound_id if mapping else None


def _serialize_track_for_profile(
    db: Session,
    track: BellMusicTrack,
    profile_id: Optional[int],
) -> dict:
    sound_id, placeholder_key = _parse_track_ref(track.file_path or "")
    resolved_sound_id = sound_id
    if placeholder_key:
        resolved_sound_id = _resolve_placeholder_sound_id(db, profile_id, placeholder_key)

    resolved_sound = None
    if resolved_sound_id:
        resolved_sound = db.query(BellSound).filter(BellSound.id == resolved_sound_id).first()

    return {
        "id": track.id,
        "schedule_id": track.schedule_id,
        "file_path": track.file_path,
        "title": track.title,
        "sort_order": track.sort_order,
        "active": track.active,
        "sound_id": sound_id,
        "placeholder_key": placeholder_key,
        "resolved_sound_id": resolved_sound_id,
        "resolved_file_path": resolved_sound.file_path if resolved_sound else None,
        "resolved_name": resolved_sound.name if resolved_sound else None,
        "created_at": track.created_at,
    }


@router.get("/runtime/model-config", response_model=BellModelConfigResponse)
async def get_bell_model_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(BellModelConfig).order_by(BellModelConfig.id.asc()).first()
    if not row:
        return BellModelConfigResponse()
    return row


@router.put("/runtime/model-config", response_model=BellModelConfigResponse)
async def upsert_bell_model_config(
    payload: BellModelConfigUpsert,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellModelConfig).order_by(BellModelConfig.id.asc()).first()
    if not row:
        row = BellModelConfig(model_json=payload.model_json, revision=1)
        db.add(row)
    else:
        row.model_json = payload.model_json
        row.revision = (row.revision or 0) + 1
    db.commit()
    db.refresh(row)
    return row


@router.post("/upload-sound", response_model=BellSoundResponse, status_code=status.HTTP_201_CREATED)
async def upload_bell_sound(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    allowed_types = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/x-wav"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio content type: {file.content_type}"
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sound file too large (max 5 MB)"
        )

    sounds_dir = os.path.join(settings.CONTENT_DIR, "sounds")
    os.makedirs(sounds_dir, exist_ok=True)

    filename = _safe_filename(file.filename or "sound.wav")
    base_name, ext = os.path.splitext(filename)
    file_path = os.path.join(sounds_dir, filename)
    counter = 1
    while os.path.exists(file_path):
        filename = f"{base_name}_{counter}{ext}"
        file_path = os.path.join(sounds_dir, filename)
        counter += 1

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    sound_name = name.strip() if name and name.strip() else base_name
    base_sound_name = sound_name
    counter = 1
    while db.query(BellSound).filter(BellSound.name == sound_name).first():
        sound_name = f"{base_sound_name} ({counter})"
        counter += 1

    db_sound = BellSound(
        name=sound_name,
        file_path=file_path,
        mime_type=file.content_type,
        size_bytes=len(content),
        active=True,
    )
    db.add(db_sound)
    db.commit()
    db.refresh(db_sound)
    return db_sound


@router.get("/sounds", response_model=List[BellSoundResponse])
async def get_sound_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(BellSound).order_by(BellSound.name.asc()).all()


@router.put("/sounds/{sound_id}", response_model=BellSoundResponse)
async def rename_sound(
    sound_id: int,
    payload: BellSoundRenameRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    sound = db.query(BellSound).filter(BellSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound not found")

    new_name = payload.name.strip()
    if not new_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be empty")

    duplicate = db.query(BellSound).filter(BellSound.name == new_name, BellSound.id != sound_id).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sound name already exists")

    sound.name = new_name
    db.commit()
    db.refresh(sound)
    return sound


@router.delete("/sounds/{sound_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sound(
    sound_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    sound = db.query(BellSound).filter(BellSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound not found")

    in_use = db.query(BellMusicTrack).filter(BellMusicTrack.file_path == f"{_SOUND_REF_PREFIX}{sound_id}").first()
    if in_use:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sound is used in a playlist")

    placeholder_use = db.query(BellProfilePlaceholder).filter(BellProfilePlaceholder.sound_id == sound_id).first()
    if placeholder_use:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sound is used by a profile placeholder")

    if sound.file_path and os.path.exists(sound.file_path):
        os.remove(sound.file_path)

    db.delete(sound)
    db.commit()
    return None


@router.get("/sounds/{sound_id}/file")
async def get_sound_file(
    sound_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sound = db.query(BellSound).filter(BellSound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound not found")

    file_path = os.path.normpath(sound.file_path or "")
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound file is empty")
    if not os.path.isabs(file_path):
        if not os.path.exists(file_path):
            file_path = os.path.normpath(os.path.join(settings.CONTENT_DIR, file_path))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound file not found")

    filename = os.path.basename(file_path)
    return FileResponse(path=file_path, filename=filename)


@router.post("/", response_model=BellScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_bell_schedule(
    bell_data: BellScheduleCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Utworzenie harmonogramu dzwonka (tylko admin)"""
    db_bell = BellSchedule(**bell_data.dict())
    db.add(db_bell)
    db.commit()
    db.refresh(db_bell)
    return db_bell


@router.get("/", response_model=List[BellScheduleResponse])
async def get_bell_schedules(
    skip: int = 0,
    limit: int = 100,
    active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie listy harmonogramĂłw dzwonkĂłw (admin i operator)"""
    query = db.query(BellSchedule)
    
    if active is not None:
        query = query.filter(BellSchedule.active == active)
    
    bells = query.order_by(BellSchedule.bell_time).offset(skip).limit(limit).all()
    return bells


@router.get("/{bell_id}", response_model=BellScheduleResponse)
async def get_bell_schedule(
    bell_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie szczegĂłĹ‚Ăłw harmonogramu dzwonka"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    return bell


@router.put("/{bell_id}", response_model=BellScheduleResponse)
async def update_bell_schedule(
    bell_id: int,
    bell_data: BellScheduleUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aktualizacja harmonogramu dzwonka (tylko admin)"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    
    update_data = bell_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bell, field, value)
    
    db.commit()
    db.refresh(bell)
    return bell


@router.delete("/{bell_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bell_schedule(
    bell_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """UsuniÄ™cie harmonogramu dzwonka (tylko admin)"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    
    # UsuniÄ™cie pliku dĹşwiÄ™kowego jeĹ›li istnieje
    if bell.sound_file_path and os.path.exists(bell.sound_file_path):
        os.remove(bell.sound_file_path)
    
    db.delete(bell)
    db.commit()
    return None


@router.get("/{bell_id}/history", response_model=List[BellHistoryResponse])
async def get_bell_history(
    bell_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pobranie historii odtworzeĹ„ dzwonka"""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )
    
    history = db.query(BellHistory).filter(
        BellHistory.bell_schedule_id == bell_id
    ).order_by(BellHistory.played_at.desc()).limit(limit).all()
    
    return history


@router.get("/display/{display_id}/play-command", response_model=Optional[BellPlayCommand])
async def get_bell_play_command(
    display_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobranie komendy odtwarzania dzwonka dla wyĹ›wietlacza (publiczny endpoint dla klienta)
    Sprawdza czy jest dzwonek do odtworzenia w tym momencie
    """
    if not settings.BELL_CLIENT_PLAYBACK_ENABLED:
        return None
    if is_display_playing_video(display_id):
        # When panel is playing video, keep video audio authoritative.
        return None

    from app.services.bell_service import get_bells_to_play
    
    bells = get_bells_to_play(db)
    
    for bell in bells:
        displays = get_displays_for_bell(db, bell)
        display_ids = [d.id for d in displays]
        
        if display_id in display_ids:
            # Sprawdzenie czy klient nie odebral juz komendy w ciagu ostatniej minuty.
            # Statusy serwerowe (played_server/failed_server) nie blokuja klienta w trybie hybrydowym.
            recent_play = db.query(BellHistory).filter(
                BellHistory.bell_schedule_id == bell.id,
                BellHistory.played_at >= datetime.utcnow() - timedelta(minutes=1),
                BellHistory.status.in_(["pending_client", "played", "success", "failed"]),
            ).first()
            
            if not recent_play and bell.sound_file_path:
                log_bell_play(db, bell.id, status="pending_client")
                return BellPlayCommand(
                    bell_schedule_id=bell.id,
                    sound_file_path=bell.sound_file_path,
                    volume=bell.volume
                )
    
    return None


@router.get("/runtime/status")
async def get_bells_runtime_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Runtime status i konfiguracja trybu odtwarzania dzwonkow."""
    control = get_or_create_runtime_control(db)
    return {
        "server_playback_enabled": settings.BELL_SERVER_PLAYBACK_ENABLED,
        "client_playback_enabled": settings.BELL_CLIENT_PLAYBACK_ENABLED,
        "server_player_cmd_configured": bool((settings.BELL_SERVER_PLAYER_CMD or "").strip()),
        "server_player_timeout_sec": settings.BELL_SERVER_PLAYER_TIMEOUT_SEC,
        "bells_enabled": control.bells_enabled,
        "pause_until": control.pause_until,
        "pause_reason": control.pause_reason,
    }


@router.get("/runtime/active-profile", response_model=Optional[BellProfileResponse])
async def get_runtime_active_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_active_bell_profile(db)



@router.get("/runtime/preview")
async def preview_bells_runtime(
    at: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Podglad logiki dzwonkow: co zostanie odtworzone dla zadanej godziny HH:MM[:SS].
    Ulatwia testy bez czekania na rzeczywisty czas.
    """
    now = local_now()
    preview_time = now.time()

    if at:
        try:
            parsed = datetime.strptime(at, "%H:%M:%S")
        except ValueError:
            try:
                parsed = datetime.strptime(at, "%H:%M")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid time format. Use HH:MM or HH:MM:SS",
                )
        preview_time = time(hour=parsed.hour, minute=parsed.minute, second=parsed.second)

    bells = get_bells_to_play(db, current_time=preview_time)
    active_profile = get_active_bell_profile(db, now)
    return {
        "timestamp": now.isoformat(),
        "preview_time": preview_time.strftime("%H:%M:%S"),
        "runtime_blocked": is_bell_playback_blocked(db, now),
        "active_profile": active_profile.name if active_profile else None,
        "bells": [
            {
                "id": bell.id,
                "name": bell.name,
                "bell_time": bell.bell_time.strftime("%H:%M:%S"),
                "sound_file_path": bell.sound_file_path,
                "display_ids": bell.display_ids or [],
            }
            for bell in bells
        ],
    }


@router.post("/mark-played", status_code=status.HTTP_200_OK)
async def mark_bell_played(
    payload: BellMarkPlayedRequest,
    db: Session = Depends(get_db)
):
    """Oznaczenie odtworzenia dzwonka przez klienta wyswietlacza."""
    bell_schedule_id = payload.bell_schedule_id or payload.bell_id
    if not bell_schedule_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bell_schedule_id (or bell_id) is required"
        )

    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_schedule_id).first()
    if not bell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bell schedule not found"
        )

    history = log_bell_play(
        db=db,
        bell_schedule_id=bell_schedule_id,
        status=payload.status,
        error_message=payload.error_message,
    )

    return {
        "message": "Bell playback logged",
        "bell_schedule_id": bell_schedule_id,
        "history_id": history.id,
    }


@router.post("/runtime/pause", response_model=BellRuntimeControlResponse)
async def pause_bells_runtime(
    payload: BellRuntimePauseRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Pause all bells globally for defined time window."""
    control = get_or_create_runtime_control(db)
    minutes = max(1, min(24 * 60, int(payload.minutes)))
    control.pause_until = datetime.utcnow() + timedelta(minutes=minutes)
    control.pause_reason = payload.reason or "Manual pause"
    db.commit()
    db.refresh(control)
    return control


@router.post("/runtime/resume", response_model=BellRuntimeControlResponse)
async def resume_bells_runtime(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Resume bell playback after manual pause."""
    control = get_or_create_runtime_control(db)
    control.pause_until = None
    control.pause_reason = None
    control.bells_enabled = True
    db.commit()
    db.refresh(control)
    return control


@router.post("/runtime/enabled/{enabled}", response_model=BellRuntimeControlResponse)
async def set_bells_enabled(
    enabled: bool,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Hard on/off switch for all bells."""
    control = get_or_create_runtime_control(db)
    control.bells_enabled = enabled
    if enabled:
        control.pause_until = None
        control.pause_reason = None
    db.commit()
    db.refresh(control)
    return control


@router.get("/runtime/calendar-overrides", response_model=List[BellCalendarOverrideResponse])
async def get_bell_calendar_overrides(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(BellCalendarOverride).order_by(BellCalendarOverride.day.asc()).all()


@router.post("/runtime/calendar-overrides", response_model=BellCalendarOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_or_replace_calendar_override(
    payload: BellCalendarOverrideCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(BellCalendarOverride).filter(BellCalendarOverride.day == payload.day).first()
    if existing:
        existing.bells_enabled = payload.bells_enabled
        existing.reason = payload.reason
        db.commit()
        db.refresh(existing)
        return existing

    row = BellCalendarOverride(
        day=payload.day,
        bells_enabled=payload.bells_enabled,
        reason=payload.reason,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/runtime/calendar-overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_override(
    override_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellCalendarOverride).filter(BellCalendarOverride.id == override_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override not found")
    db.delete(row)
    db.commit()
    return None


@router.get("/runtime/profiles", response_model=List[BellProfileResponse])
async def get_bell_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(BellProfile).order_by(BellProfile.name.asc()).all()


@router.post("/runtime/profiles", response_model=BellProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_bell_profile(
    payload: BellProfileCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if payload.is_default:
        db.query(BellProfile).update({"is_default": False})

    row = BellProfile(
        name=payload.name,
        month=payload.month,
        is_default=payload.is_default,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/runtime/profiles/{profile_id}", response_model=BellProfileResponse)
async def update_bell_profile(
    profile_id: int,
    payload: BellProfileUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellProfile).filter(BellProfile.id == profile_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default"):
        db.query(BellProfile).update({"is_default": False})

    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/runtime/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bell_profile(
    profile_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellProfile).filter(BellProfile.id == profile_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    db.query(BellScheduleProfile).filter(BellScheduleProfile.profile_id == profile_id).delete()
    db.query(BellProfileOverride).filter(BellProfileOverride.profile_id == profile_id).delete()
    db.query(BellProfilePlaceholder).filter(BellProfilePlaceholder.profile_id == profile_id).delete()
    db.delete(row)
    db.commit()
    return None


@router.get("/runtime/profiles/{profile_id}/placeholders", response_model=List[BellProfilePlaceholderResponse])
async def get_profile_placeholders(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(BellProfile).filter(BellProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return (
        db.query(BellProfilePlaceholder)
        .filter(BellProfilePlaceholder.profile_id == profile_id)
        .order_by(BellProfilePlaceholder.placeholder_key.asc())
        .all()
    )


@router.put("/runtime/profiles/{profile_id}/placeholders/{placeholder_key}", response_model=BellProfilePlaceholderResponse)
async def upsert_profile_placeholder(
    profile_id: int,
    placeholder_key: str,
    payload: BellProfilePlaceholderUpsert,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    normalized_key = placeholder_key.strip().upper()
    profile = db.query(BellProfile).filter(BellProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    sound = db.query(BellSound).filter(BellSound.id == payload.sound_id).first()
    if not sound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound not found")

    row = db.query(BellProfilePlaceholder).filter(
        BellProfilePlaceholder.profile_id == profile_id,
        BellProfilePlaceholder.placeholder_key == normalized_key,
    ).first()
    if row:
        row.sound_id = payload.sound_id
        db.commit()
        db.refresh(row)
        return row

    row = BellProfilePlaceholder(
        profile_id=profile_id,
        placeholder_key=normalized_key,
        sound_id=payload.sound_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/runtime/profiles/{profile_id}/placeholders/{placeholder_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_placeholder(
    profile_id: int,
    placeholder_key: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    normalized_key = placeholder_key.strip().upper()
    row = db.query(BellProfilePlaceholder).filter(
        BellProfilePlaceholder.profile_id == profile_id,
        BellProfilePlaceholder.placeholder_key == normalized_key,
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placeholder mapping not found")
    db.delete(row)
    db.commit()
    return None


@router.get("/runtime/profile-overrides", response_model=List[BellProfileOverrideResponse])
async def get_bell_profile_overrides(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(BellProfileOverride).order_by(BellProfileOverride.day.asc()).all()


@router.post("/runtime/profile-overrides", response_model=BellProfileOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_or_replace_bell_profile_override(
    payload: BellProfileOverrideCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    profile = db.query(BellProfile).filter(BellProfile.id == payload.profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile not found")

    row = db.query(BellProfileOverride).filter(BellProfileOverride.day == payload.day).first()
    if row:
        row.profile_id = payload.profile_id
        row.reason = payload.reason
        db.commit()
        db.refresh(row)
        return row

    row = BellProfileOverride(day=payload.day, profile_id=payload.profile_id, reason=payload.reason)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/runtime/profile-overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bell_profile_override(
    override_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellProfileOverride).filter(BellProfileOverride.id == override_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile override not found")
    db.delete(row)
    db.commit()
    return None


@router.get("/display/{display_id}/music-playlist")
async def get_music_playlist_for_display(
    display_id: int,
    db: Session = Depends(get_db),
):
    """Public endpoint for audio clients: active break playlist for display."""
    if is_display_playing_video(display_id):
        return {"active": False}
    schedule = get_active_music_schedule(db, display_id=display_id)
    if not schedule:
        return {"active": False}

    active_profile = get_active_bell_profile(db)
    active_profile_id = active_profile.id if active_profile else None
    tracks = get_active_music_tracks(db, schedule.id)
    serialized = [_serialize_track_for_profile(db, track, active_profile_id) for track in tracks]
    playable = [row for row in serialized if row["resolved_file_path"]]
    return {
        "active": True,
        "schedule": {
            "id": schedule.id,
            "name": schedule.name,
            "start_time": schedule.start_time.strftime("%H:%M:%S"),
            "end_time": schedule.end_time.strftime("%H:%M:%S"),
            "volume": schedule.volume,
            "priority": schedule.priority,
        },
        "tracks": [
            {
                "id": row["id"],
                "title": row["resolved_name"] or row["title"],
                "file_path": row["resolved_file_path"],
                "file_url": f"{settings.API_V1_PREFIX}/bells/music-tracks/{row['id']}/file",
                "sort_order": row["sort_order"],
                "placeholder_key": row["placeholder_key"],
                "sound_id": row["resolved_sound_id"],
            }
            for row in playable
        ],
    }


@router.get("/runtime/music-preview")
async def preview_music_runtime(
    at: Optional[str] = None,
    display_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = local_now()
    preview_dt = now
    if at:
        try:
            parsed = datetime.strptime(at, "%H:%M:%S")
        except ValueError:
            try:
                parsed = datetime.strptime(at, "%H:%M")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid time format. Use HH:MM or HH:MM:SS",
                )
        preview_dt = now.replace(hour=parsed.hour, minute=parsed.minute, second=parsed.second, microsecond=0)

    schedule = get_active_music_schedule(db, display_id=display_id, now=preview_dt)
    active_profile = get_active_bell_profile(db, preview_dt)
    active_profile_id = active_profile.id if active_profile else None
    tracks = get_active_music_tracks(db, schedule.id) if schedule else []
    serialized = [_serialize_track_for_profile(db, track, active_profile_id) for track in tracks]
    return {
        "timestamp": now.isoformat(),
        "preview_time": preview_dt.strftime("%H:%M:%S"),
        "display_id": display_id,
        "active": bool(schedule),
        "schedule": {
            "id": schedule.id,
            "name": schedule.name,
            "start_time": schedule.start_time.strftime("%H:%M:%S"),
            "end_time": schedule.end_time.strftime("%H:%M:%S"),
            "volume": schedule.volume,
            "priority": schedule.priority,
        } if schedule else None,
        "tracks_count": len(serialized),
        "playable_tracks_count": len([row for row in serialized if row["resolved_file_path"]]),
    }


@router.get("/runtime/music-schedules", response_model=List[BellMusicScheduleResponse])
async def get_music_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(BellMusicSchedule)
        .order_by(BellMusicSchedule.priority.desc(), BellMusicSchedule.start_time.asc())
        .all()
    )


@router.post("/runtime/music-schedules", response_model=BellMusicScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_music_schedule(
    payload: BellMusicScheduleCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = BellMusicSchedule(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/runtime/music-schedules/{schedule_id}", response_model=BellMusicScheduleResponse)
async def update_music_schedule(
    schedule_id: int,
    payload: BellMusicScheduleUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellMusicSchedule).filter(BellMusicSchedule.id == schedule_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Music schedule not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/runtime/music-schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_music_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellMusicSchedule).filter(BellMusicSchedule.id == schedule_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Music schedule not found")
    db.query(BellMusicTrack).filter(BellMusicTrack.schedule_id == schedule_id).delete()
    db.delete(row)
    db.commit()
    return None


@router.get("/runtime/music-schedules/{schedule_id}/tracks", response_model=List[BellMusicTrackResponse])
async def get_music_tracks(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = db.query(BellMusicSchedule).filter(BellMusicSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Music schedule not found")
    active_profile = get_active_bell_profile(db)
    active_profile_id = active_profile.id if active_profile else None
    tracks = get_active_music_tracks(db, schedule_id)
    return [_serialize_track_for_profile(db, track, active_profile_id) for track in tracks]


@router.post("/runtime/music-schedules/{schedule_id}/tracks", response_model=BellMusicTrackResponse, status_code=status.HTTP_201_CREATED)
async def add_music_track(
    schedule_id: int,
    payload: BellMusicTrackCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    schedule = db.query(BellMusicSchedule).filter(BellMusicSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Music schedule not found")

    if payload.sound_id is None and not payload.placeholder_key and not payload.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide one of: sound_id, placeholder_key or file_path",
        )

    if payload.sound_id is not None:
        sound = db.query(BellSound).filter(BellSound.id == payload.sound_id).first()
        if not sound:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound not found")

    file_path = _build_track_ref(payload.sound_id, payload.placeholder_key, payload.file_path)
    if not file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid track source")

    row = BellMusicTrack(
        schedule_id=schedule_id,
        file_path=file_path,
        title=payload.title,
        sort_order=payload.sort_order,
        active=payload.active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    active_profile = get_active_bell_profile(db)
    active_profile_id = active_profile.id if active_profile else None
    return _serialize_track_for_profile(db, row, active_profile_id)


@router.delete("/runtime/music-tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_music_track(
    track_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(BellMusicTrack).filter(BellMusicTrack.id == track_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Music track not found")
    db.delete(row)
    db.commit()
    return None


@router.get("/music-tracks/{track_id}/file")
async def get_music_track_file(
    track_id: int,
    db: Session = Depends(get_db),
):
    row = db.query(BellMusicTrack).filter(BellMusicTrack.id == track_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Music track not found")

    active_profile = get_active_bell_profile(db)
    active_profile_id = active_profile.id if active_profile else None
    serialized = _serialize_track_for_profile(db, row, active_profile_id)

    resolved_path = serialized.get("resolved_file_path")
    if not resolved_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track source is unresolved for current profile")

    file_path = os.path.normpath(str(resolved_path))
    if not os.path.isabs(file_path):
        if not os.path.exists(file_path):
            file_path = os.path.normpath(os.path.join(settings.CONTENT_DIR, file_path))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track file not found")

    filename = os.path.basename(file_path)
    return FileResponse(path=file_path, filename=filename)


@router.get("/{bell_id}/sound-file")
async def get_bell_sound_file(
    bell_id: int,
    db: Session = Depends(get_db),
):
    """Public endpoint for audio clients to download bell sound."""
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bell schedule not found")
    if not bell.sound_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sound file configured")

    file_path = os.path.normpath(bell.sound_file_path)
    if not os.path.isabs(file_path):
        if not os.path.exists(file_path):
            file_path = os.path.normpath(os.path.join(settings.CONTENT_DIR, file_path))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sound file not found")

    filename = os.path.basename(file_path)
    return FileResponse(path=file_path, filename=filename)


@router.get("/{bell_id}/profiles", response_model=List[int])
async def get_bell_schedule_profiles(
    bell_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bell schedule not found")
    links = db.query(BellScheduleProfile).filter(BellScheduleProfile.bell_schedule_id == bell_id).all()
    return [link.profile_id for link in links]


@router.put("/{bell_id}/profiles", response_model=List[int])
async def set_bell_schedule_profiles(
    bell_id: int,
    payload: BellScheduleProfilesUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    bell = db.query(BellSchedule).filter(BellSchedule.id == bell_id).first()
    if not bell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bell schedule not found")

    profile_ids = sorted(set(payload.profile_ids))
    if profile_ids:
        existing_count = db.query(BellProfile).filter(BellProfile.id.in_(profile_ids)).count()
        if existing_count != len(profile_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more profiles do not exist")

    db.query(BellScheduleProfile).filter(BellScheduleProfile.bell_schedule_id == bell_id).delete()
    for profile_id in profile_ids:
        db.add(BellScheduleProfile(bell_schedule_id=bell_id, profile_id=profile_id))
    db.commit()
    return profile_ids


