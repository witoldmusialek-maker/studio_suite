from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Any

from smb.SMBConnection import SMBConnection
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.salon_core import (
    BundleCatalog,
    BundleCatalogItem,
    Salon,
    SalonServiceCatalogItem,
    ServiceCatalogItem,
    ServicePriceHistory,
)


def _as_double(chunk: bytes, offset: int) -> float:
    if offset + 8 > len(chunk):
        return 0.0
    value = struct.unpack("<d", chunk[offset : offset + 8])[0]
    if not (0 <= value <= 1_000_000):
        return 0.0
    return round(value, 2)


def _parse_records(content: bytes) -> tuple[list[bytes], list[list[str]]]:
    rec_len = int(content[7:11].decode("ascii"))
    offset = rec_len
    total = max(0, (len(content) - offset) // rec_len)
    chunks: list[bytes] = []
    rows: list[list[str]] = []
    for i in range(total):
        chunk = content[offset + i * rec_len : offset + (i + 1) * rec_len]
        chunks.append(chunk)
        parts = [part.decode("latin-1", "replace").strip() for part in chunk.split(b"\x00") if part.strip()]
        rows.append(parts)
    return chunks, rows


def _parse_service_fic(content: bytes) -> dict[str, dict[str, Any]]:
    chunks, rows = _parse_records(content)
    out: dict[str, dict[str, Any]] = {}
    for chunk, row in zip(chunks, rows):
        if len(row) < 4 or not row[0].isdigit():
            continue
        code = row[0].zfill(4)
        duration_raw = row[9] if len(row) > 9 else "60"
        duration = int(duration_raw) if duration_raw.isdigit() else 60
        out[code] = {
            "name": row[3].strip(),
            "duration_minutes": duration,
            "price": _as_double(chunk, 46),
        }
    return out


def _parse_forfait_fic(content: bytes) -> dict[str, dict[str, Any]]:
    chunks, rows = _parse_records(content)
    bundles: dict[str, dict[str, Any]] = {}
    for chunk, row in zip(chunks, rows):
        if len(row) < 3 or not row[0].isdigit():
            continue
        code = row[0].zfill(4)
        name = row[1].strip()
        service_codes = [part for part in row[3:] if part.isdigit() and len(part) == 4]
        item_prices: list[float] = []
        for idx in range(len(service_codes)):
            item_prices.append(_as_double(chunk, 89 + idx * 8))
        bundles[code] = {
            "name": name,
            "service_codes": service_codes,
            "item_prices": item_prices,
            "total_price": round(sum(item_prices), 2),
        }
    return bundles


def _latest_prices_by_service_id(db: Session, salon_id: int) -> dict[int, float]:
    latest_price_subquery = (
        db.query(
            ServicePriceHistory.service_id.label("service_id"),
            ServicePriceHistory.salon_id.label("salon_id"),
            func.max(ServicePriceHistory.id).label("max_id"),
        )
        .filter(ServicePriceHistory.salon_id == salon_id)
        .group_by(ServicePriceHistory.service_id, ServicePriceHistory.salon_id)
        .subquery()
    )
    rows = (
        db.query(ServicePriceHistory)
        .join(latest_price_subquery, ServicePriceHistory.id == latest_price_subquery.c.max_id)
        .all()
    )
    return {row.service_id: round(float(row.price), 2) for row in rows if row.price is not None}


def _infer_service_segment(service_code: str) -> str:
    if not service_code.isdigit():
        return "PANI"
    numeric = int(service_code)
    if 101 <= numeric <= 199:
        return "PAN"
    if 200 <= numeric <= 299:
        return "SPRZEDAZ"
    if 300 <= numeric <= 399:
        return "ESTETYKA"
    return "PANI"


def _normalize(value: str | None) -> str:
    return " ".join((value or "").strip().split()).upper()


def _connect_legacy_smb() -> SMBConnection:
    conn = SMBConnection(
        settings.LEGACY_SMB_USERNAME or "",
        settings.LEGACY_SMB_PASSWORD or "",
        "studio_suite_sync",
        settings.LEGACY_SMB_HOST,
        domain=settings.LEGACY_SMB_DOMAIN or "",
        use_ntlm_v2=settings.LEGACY_SMB_USE_NTLM_V2,
        is_direct_tcp=(settings.LEGACY_SMB_PORT == 445),
    )
    if not conn.connect(settings.LEGACY_SMB_HOST, settings.LEGACY_SMB_PORT, timeout=20):
        raise RuntimeError("legacy_smb_connect_failed")
    return conn


def _read_smb_file(conn: SMBConnection, share: str, filename: str) -> bytes:
    from io import BytesIO

    stream = BytesIO()
    conn.retrieveFile(share, filename, stream)
    return stream.getvalue()


@dataclass
class LegacySnapshot:
    services: dict[str, dict[str, Any]]
    bundles: dict[str, dict[str, Any]]


def _load_legacy_snapshot(salon_code: str) -> LegacySnapshot:
    share = salon_code.zfill(2)
    conn = _connect_legacy_smb()
    try:
        service_content = _read_smb_file(conn, share, "SERVICE.FIC")
        forfait_content = _read_smb_file(conn, share, "FORFAIT.FIC")
    finally:
        conn.close()
    return LegacySnapshot(
        services=_parse_service_fic(service_content),
        bundles=_parse_forfait_fic(forfait_content),
    )


def _db_service_view(db: Session, salon_id: int) -> tuple[dict[str, dict[str, Any]], dict[str, ServiceCatalogItem]]:
    links = (
        db.query(SalonServiceCatalogItem)
        .filter(SalonServiceCatalogItem.salon_id == salon_id)
        .all()
    )
    service_ids = [row.service_id for row in links]
    services = (
        db.query(ServiceCatalogItem)
        .filter(ServiceCatalogItem.id.in_(service_ids) if service_ids else False)
        .all()
    )
    by_id = {row.id: row for row in services}
    prices = _latest_prices_by_service_id(db, salon_id=salon_id)
    out: dict[str, dict[str, Any]] = {}
    by_code_entity: dict[str, ServiceCatalogItem] = {}
    for link in links:
        service = by_id.get(link.service_id)
        if not service:
            continue
        code = (service.legacy_code or "").zfill(4)
        out[code] = {
            "name": link.local_name or service.name,
            "duration_minutes": int(service.duration_minutes or 0),
            "price": round(float(prices.get(service.id, service.default_price or 0)), 2),
        }
        by_code_entity[code] = service
    return out, by_code_entity


def _db_bundle_view(db: Session, salon_id: int) -> tuple[dict[str, dict[str, Any]], dict[str, BundleCatalog]]:
    bundles = db.query(BundleCatalog).filter(BundleCatalog.salon_id == salon_id).all()
    bundle_ids = [row.id for row in bundles]
    items = (
        db.query(BundleCatalogItem)
        .filter(BundleCatalogItem.bundle_id.in_(bundle_ids) if bundle_ids else False)
        .order_by(BundleCatalogItem.position.asc())
        .all()
    )
    grouped: dict[int, list[BundleCatalogItem]] = {}
    for item in items:
        grouped.setdefault(item.bundle_id, []).append(item)

    out: dict[str, dict[str, Any]] = {}
    by_code_entity: dict[str, BundleCatalog] = {}
    for bundle in bundles:
        code = (bundle.legacy_code or "").zfill(4)
        rows = grouped.get(bundle.id, [])
        out[code] = {
            "name": bundle.name,
            "total_price": round(float(bundle.price or 0), 2),
            "service_codes": [((row.service_legacy_code or "").zfill(4)) for row in rows if row.service_legacy_code],
        }
        by_code_entity[code] = bundle
    return out, by_code_entity


def build_sync_report(db: Session, salon_id: int) -> dict[str, Any]:
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise ValueError("salon_not_found")

    legacy = _load_legacy_snapshot(salon.code or "")
    db_services, _ = _db_service_view(db, salon_id)
    db_bundles, _ = _db_bundle_view(db, salon_id)

    legacy_service_codes = set(legacy.services.keys())
    db_service_codes = set(db_services.keys())
    service_common = sorted(legacy_service_codes & db_service_codes)

    services_missing_in_db = len(legacy_service_codes - db_service_codes)
    services_name_diff = sum(1 for code in service_common if _normalize(legacy.services[code]["name"]) != _normalize(db_services[code]["name"]))
    services_duration_diff = sum(1 for code in service_common if int(legacy.services[code]["duration_minutes"]) != int(db_services[code]["duration_minutes"]))
    services_price_diff = sum(1 for code in service_common if abs(float(legacy.services[code]["price"]) - float(db_services[code]["price"])) > 0.01)

    legacy_bundle_codes = set(legacy.bundles.keys())
    db_bundle_codes = set(db_bundles.keys())
    bundle_common = sorted(legacy_bundle_codes & db_bundle_codes)

    bundles_missing_in_db = len(legacy_bundle_codes - db_bundle_codes)
    bundles_name_diff = sum(1 for code in bundle_common if _normalize(legacy.bundles[code]["name"]) != _normalize(db_bundles[code]["name"]))
    bundles_price_diff = sum(1 for code in bundle_common if abs(float(legacy.bundles[code]["total_price"]) - float(db_bundles[code]["total_price"])) > 0.01)
    bundles_items_diff = sum(1 for code in bundle_common if list(legacy.bundles[code]["service_codes"]) != list(db_bundles[code]["service_codes"]))

    diff = {
        "services_missing_in_db": services_missing_in_db,
        "services_name_diff": services_name_diff,
        "services_duration_diff": services_duration_diff,
        "services_price_diff": services_price_diff,
        "bundles_missing_in_db": bundles_missing_in_db,
        "bundles_name_diff": bundles_name_diff,
        "bundles_price_diff": bundles_price_diff,
        "bundles_items_diff": bundles_items_diff,
    }
    diff["total"] = int(sum(diff.values()))
    return {
        "salon_id": salon.id,
        "salon_code": salon.code,
        "salon_name": salon.name,
        "diff": diff,
        "_legacy_snapshot": legacy,
    }


def apply_sync_from_legacy(db: Session, salon_id: int) -> dict[str, Any]:
    report = build_sync_report(db, salon_id)
    legacy: LegacySnapshot = report.pop("_legacy_snapshot")
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise ValueError("salon_not_found")

    db_services, by_code_service = _db_service_view(db, salon_id)
    created_services = 0
    updated_service_names = 0
    updated_service_durations = 0
    updated_service_prices = 0

    for service_code in sorted(legacy.services.keys()):
        legacy_row = legacy.services[service_code]
        service = by_code_service.get(service_code)
        if service is None:
            service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.legacy_code == service_code).first()
            if service is None:
                service = ServiceCatalogItem(
                    legacy_code=service_code,
                    name=legacy_row["name"],
                    service_type_code=_infer_service_segment(service_code),
                    duration_minutes=int(legacy_row["duration_minutes"]),
                    default_price=float(legacy_row["price"]),
                    holiday_price=float(legacy_row["price"]),
                    is_active=True,
                    bookable=True,
                )
                db.add(service)
                db.flush()
                created_services += 1
            link = (
                db.query(SalonServiceCatalogItem)
                .filter(
                    SalonServiceCatalogItem.salon_id == salon_id,
                    SalonServiceCatalogItem.service_id == service.id,
                )
                .first()
            )
            if link is None:
                link = SalonServiceCatalogItem(salon_id=salon_id, service_id=service.id, is_active=True)
                db.add(link)
            by_code_service[service_code] = service
            db_services[service_code] = {
                "name": link.local_name or service.name,
                "duration_minutes": int(service.duration_minutes or 0),
                "price": round(float(service.default_price or 0), 2),
            }

        link = (
            db.query(SalonServiceCatalogItem)
            .filter(
                SalonServiceCatalogItem.salon_id == salon_id,
                SalonServiceCatalogItem.service_id == service.id,
            )
            .first()
        )
        if link and _normalize(link.local_name or service.name) != _normalize(legacy_row["name"]):
            link.local_name = legacy_row["name"]
            updated_service_names += 1

        if int(service.duration_minutes or 0) != int(legacy_row["duration_minutes"]):
            service.duration_minutes = int(legacy_row["duration_minutes"])
            updated_service_durations += 1

        latest_price = _latest_prices_by_service_id(db, salon_id).get(service.id, round(float(service.default_price or 0), 2))
        if abs(float(latest_price) - float(legacy_row["price"])) > 0.01:
            db.add(
                ServicePriceHistory(
                    service_id=service.id,
                    salon_id=salon_id,
                    price=float(legacy_row["price"]),
                    holiday_price=float(legacy_row["price"]),
                    source="legacy_sync",
                )
            )
            updated_service_prices += 1

    db.flush()

    db_bundles, by_code_bundle = _db_bundle_view(db, salon_id)
    created_bundles = 0
    updated_bundle_names = 0
    rebuilt_bundle_items = 0

    service_id_by_code: dict[str, int] = {}
    for service in db.query(ServiceCatalogItem).all():
        service_id_by_code[(service.legacy_code or "").zfill(4)] = service.id

    for bundle_code in sorted(legacy.bundles.keys()):
        legacy_bundle = legacy.bundles[bundle_code]
        bundle = by_code_bundle.get(bundle_code)
        if bundle is None:
            bundle = BundleCatalog(
                legacy_code=bundle_code,
                salon_id=salon_id,
                name=legacy_bundle["name"],
                frequency_mode="week_and_holiday",
                price=float(legacy_bundle["total_price"]),
            )
            db.add(bundle)
            db.flush()
            by_code_bundle[bundle_code] = bundle
            created_bundles += 1
        elif _normalize(bundle.name) != _normalize(legacy_bundle["name"]):
            bundle.name = legacy_bundle["name"]
            updated_bundle_names += 1

        current_items = (
            db.query(BundleCatalogItem)
            .filter(BundleCatalogItem.bundle_id == bundle.id)
            .order_by(BundleCatalogItem.position.asc())
            .all()
        )
        current_codes = [((row.service_legacy_code or "").zfill(4)) for row in current_items if row.service_legacy_code]
        legacy_codes = list(legacy_bundle["service_codes"])
        if current_codes != legacy_codes or len(current_items) != len(legacy_codes):
            db.query(BundleCatalogItem).filter(BundleCatalogItem.bundle_id == bundle.id).delete(synchronize_session=False)
            for idx, service_code in enumerate(legacy_codes, start=1):
                service_id = service_id_by_code.get(service_code)
                override_price = None
                if idx - 1 < len(legacy_bundle["item_prices"]):
                    raw = float(legacy_bundle["item_prices"][idx - 1])
                    if raw > 0:
                        override_price = raw
                db.add(
                    BundleCatalogItem(
                        bundle_id=bundle.id,
                        position=idx,
                        service_id=service_id,
                        service_legacy_code=service_code,
                        override_price=override_price,
                    )
                )
            rebuilt_bundle_items += 1

    db.commit()
    report = build_sync_report(db, salon_id)
    report.pop("_legacy_snapshot", None)
    return {
        "report": report,
        "created_services": created_services,
        "updated_service_names": updated_service_names,
        "updated_service_durations": updated_service_durations,
        "updated_service_prices": updated_service_prices,
        "created_bundles": created_bundles,
        "updated_bundle_names": updated_bundle_names,
        "rebuilt_bundle_items": rebuilt_bundle_items,
    }
