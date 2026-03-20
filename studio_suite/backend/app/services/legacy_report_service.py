"""
Reporting helpers for imported legacy salon datasets.
"""
from __future__ import annotations

import struct
from datetime import date, datetime
from typing import Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from smb.SMBConnection import SMBConnection

from app.config import settings
from app.models.salon_core import (
    Appointment,
    BundleCatalog,
    LegacyEdition1Daily,
    LegacyEdServiceRow,
    LegacyFicheLine,
    LegacyForfaitTransaction,
    LegacyVisitDocument,
    LegacyWorkerCard,
    LegacyStat7Row,
    ServiceCatalogItem,
    Salon,
    StaffMember,
)
from app.services.legacy_catalog_service import parse_vat_percent_by_service


def _parse_legacy_date(token: Optional[str]) -> Optional[date]:
    if not token:
        return None
    value = token.strip()
    if not value:
        return None
    formats = ("%Y%m%d", "%d%m%Y", "%d/%m/%Y", "%d.%m.%Y")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _in_range(token: Optional[str], from_date: Optional[date], to_date: Optional[date]) -> bool:
    if from_date is None and to_date is None:
        return True
    parsed = _parse_legacy_date(token)
    if parsed is None:
        return False
    if from_date is not None and parsed < from_date:
        return False
    if to_date is not None and parsed > to_date:
        return False
    return True


def get_import_summary(db: Session) -> Dict[str, int]:
    return {
        "salons": db.query(func.count(Salon.id)).scalar() or 0,
        "services": db.query(func.count(ServiceCatalogItem.id)).scalar() or 0,
        "bundles": db.query(func.count(BundleCatalog.id)).scalar() or 0,
        "forfait_transactions": db.query(func.count(LegacyForfaitTransaction.id)).scalar() or 0,
        "fiche_lines": db.query(func.count(LegacyFicheLine.id)).scalar() or 0,
        "edition1_days": db.query(func.count(LegacyEdition1Daily.id)).scalar() or 0,
    }


def get_forfaits_revenue(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    query = db.query(LegacyForfaitTransaction)
    if salon_id is not None:
        query = query.filter(LegacyForfaitTransaction.salon_id == salon_id)
    rows = query.all()
    agg: Dict[str, Dict[str, object]] = {}
    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        code = row.bundle_code or "UNKNOWN"
        if code not in agg:
            agg[code] = {
                "bundle_code": code,
                "bundle_name": row.bundle_name or "",
                "count": 0,
                "revenue": 0.0,
            }
        agg[code]["count"] = int(agg[code]["count"]) + 1
        agg[code]["revenue"] = round(float(agg[code]["revenue"]) + float(row.price), 2)

    return sorted(agg.values(), key=lambda item: float(item["revenue"]), reverse=True)


def get_services_by_worker(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    service_name_by_code = {
        item.legacy_code: item.name for item in db.query(ServiceCatalogItem).all()
    }
    query = db.query(LegacyFicheLine)
    if salon_id is not None:
        query = query.filter(LegacyFicheLine.salon_id == salon_id)
    rows = query.all()
    agg: Dict[tuple[str, str], Dict[str, object]] = {}
    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        worker_code = (row.worker_code or "00").zfill(2)
        service_code = (row.service_code or "0000").zfill(4)
        key = (worker_code, service_code)
        if key not in agg:
            agg[key] = {
                "worker_code": worker_code,
                "worker_name": "",
                "service_code": service_code,
                "service_name": service_name_by_code.get(service_code, ""),
                "qty": 0,
                "revenue": 0.0,
            }
        agg[key]["qty"] = int(agg[key]["qty"]) + 1
        agg[key]["revenue"] = round(float(agg[key]["revenue"]) + float(row.amount), 2)

    staff_name_by_code, worker_card_name_by_code = _build_worker_name_maps(db, salon_id)

    for item in agg.values():
        code = str(item["worker_code"] or "").zfill(2)
        item["worker_name"] = (
            staff_name_by_code.get(code)
            or worker_card_name_by_code.get(code)
            or ""
        )

    return sorted(agg.values(), key=lambda item: float(item["revenue"]), reverse=True)


def _build_worker_name_maps(db: Session, salon_id: Optional[int] = None) -> tuple[Dict[str, str], Dict[str, str]]:
    staff_name_by_code: Dict[str, str] = {}
    staff_query = db.query(StaffMember)
    if salon_id is not None:
        staff_query = staff_query.filter(StaffMember.salon_id == salon_id)
    for staff in staff_query.all():
        legacy_code = (staff.legacy_code or "").strip()
        if legacy_code.isdigit():
            staff_name_by_code[legacy_code.zfill(2)] = staff.display_name

    worker_card_name_by_code: Dict[str, str] = {}
    worker_cards_query = db.query(LegacyWorkerCard).filter(LegacyWorkerCard.is_probable_employee.is_(True))
    if salon_id is not None:
        worker_cards_query = worker_cards_query.filter(LegacyWorkerCard.salon_id == salon_id)
    for card in worker_cards_query.all():
        code = (card.worker_code or "").strip()
        label = (card.full_label or card.second_label or card.first_label or "").strip()
        if code.isdigit() and label:
            worker_card_name_by_code[code.zfill(2)] = label.title()

    return staff_name_by_code, worker_card_name_by_code


def get_monthly_summary(db: Session, salon_id: Optional[int] = None) -> List[Dict[str, object]]:
    query = db.query(LegacyEdition1Daily)
    if salon_id is not None:
        salon = db.query(Salon).filter(Salon.id == salon_id).first()
        if salon and salon.code:
            query = query.filter(LegacyEdition1Daily.salon_code == salon.code)
        else:
            return []
    rows = query.all()
    agg: Dict[str, Dict[str, object]] = {}
    for row in rows:
        parsed = _parse_legacy_date(row.date_token)
        if parsed is None:
            continue
        month = parsed.strftime("%Y-%m")
        if month not in agg:
            agg[month] = {
                "month": month,
                "days_count": 0,
                "gross_total": 0.0,
                "net_total": 0.0,
                "vat_total": 0.0,
                "tickets_count": 0,
            }
        agg[month]["days_count"] = int(agg[month]["days_count"]) + 1
        agg[month]["gross_total"] = round(float(agg[month]["gross_total"]) + float(row.value_47), 2)
        agg[month]["net_total"] = round(float(agg[month]["net_total"]) + float(row.value_79), 2)
        agg[month]["vat_total"] = round(float(agg[month]["vat_total"]) + float(row.value_119), 2)
        agg[month]["tickets_count"] = int(agg[month]["tickets_count"]) + int(float(row.value_165 or 0))

    return sorted(agg.values(), key=lambda item: item["month"])


def get_daily_summary(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    query = db.query(LegacyFicheLine)
    if salon_id is not None:
        query = query.filter(LegacyFicheLine.salon_id == salon_id)
    rows = query.all()
    vat_percent_by_service = parse_vat_percent_by_service(db)
    by_date: Dict[str, Dict[str, object]] = {}

    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        date_token = row.date_token or ""
        if date_token not in by_date:
            parsed = _parse_legacy_date(date_token)
            day_name = parsed.strftime("%A") if parsed else ""
            by_date[date_token] = {
                "date": date_token,
                "day_name": day_name,
                "gross_total": 0.0,
                "net_total": 0.0,
                "vat_total": 0.0,
                "tickets": set(),
            }
        amount = float(row.amount)
        vat_percent = vat_percent_by_service.get((row.service_code or "").zfill(4), 0.0)
        vat_value = amount * (vat_percent / (100.0 + vat_percent)) if vat_percent > 0 else 0.0
        net_value = amount - vat_value

        by_date[date_token]["gross_total"] = round(float(by_date[date_token]["gross_total"]) + amount, 2)
        by_date[date_token]["net_total"] = round(float(by_date[date_token]["net_total"]) + net_value, 2)
        by_date[date_token]["vat_total"] = round(float(by_date[date_token]["vat_total"]) + vat_value, 2)
        if row.ticket_code:
            by_date[date_token]["tickets"].add(row.ticket_code)

    out: List[Dict[str, object]] = []
    for payload in by_date.values():
        out.append(
            {
                "date": payload["date"],
                "day_name": payload["day_name"],
                "gross_total": float(payload["gross_total"]),
                "net_total": float(payload["net_total"]),
                "vat_total": float(payload["vat_total"]),
                "tickets_count": len(payload["tickets"]),
            }
        )

    return sorted(out, key=lambda item: item["date"])


def get_forfait_transactions(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    query = db.query(LegacyForfaitTransaction)
    if salon_id is not None:
        query = query.filter(LegacyForfaitTransaction.salon_id == salon_id)
    rows = query.all()
    out: List[Dict[str, object]] = []
    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        out.append(
            {
                "date_token": row.date_token or "",
                "bundle_code": row.bundle_code,
                "bundle_name": row.bundle_name,
                "price": float(row.price),
            }
        )
    return sorted(out, key=lambda item: (item["date_token"], item["bundle_code"]))


def get_services_aggregate(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    service_name_by_code = {item.legacy_code: item.name for item in db.query(ServiceCatalogItem).all()}
    query = db.query(LegacyFicheLine)
    if salon_id is not None:
        query = query.filter(LegacyFicheLine.salon_id == salon_id)
    rows = query.all()
    agg: Dict[str, Dict[str, object]] = {}
    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        service_code = (row.service_code or "0000").zfill(4)
        if service_code not in agg:
            agg[service_code] = {
                "service_code": service_code,
                "service_name": service_name_by_code.get(service_code, ""),
                "qty": 0,
                "revenue": 0.0,
            }
        agg[service_code]["qty"] = int(agg[service_code]["qty"]) + 1
        agg[service_code]["revenue"] = round(float(agg[service_code]["revenue"]) + float(row.amount), 2)
    return sorted(agg.values(), key=lambda item: float(item["revenue"]), reverse=True)


def get_cashflow_by_payment(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    query = db.query(LegacyFicheLine)
    if salon_id is not None:
        query = query.filter(LegacyFicheLine.salon_id == salon_id)
    rows = query.all()
    agg: Dict[tuple[str, str], Dict[str, object]] = {}
    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        date_token = row.date_token or ""
        payment = row.payment_hint or "UNKNOWN"
        key = (date_token, payment)
        if key not in agg:
            agg[key] = {"date": date_token, "payment_hint": payment, "count": 0, "revenue": 0.0}
        agg[key]["count"] = int(agg[key]["count"]) + 1
        agg[key]["revenue"] = round(float(agg[key]["revenue"]) + float(row.amount), 2)
    return sorted(agg.values(), key=lambda item: (item["date"], item["payment_hint"]))


def get_stat7_worker_summary(db: Session) -> List[Dict[str, object]]:
    rows = db.query(LegacyStat7Row).all()
    agg: Dict[str, Dict[str, object]] = {}
    for row in rows:
        worker_code = (row.worker_code or "00").zfill(2)
        if worker_code not in agg:
            agg[worker_code] = {
                "worker_code": worker_code,
                "worker_name": row.worker_name or "",
                "total": 0.0,
                "payment_a": row.payment_a or "",
                "payment_b": row.payment_b or "",
                "payment_c": row.payment_c or "",
            }
        total_row = float(row.value_295) + float(row.value_323) + float(row.value_331) + float(row.value_339) + float(row.value_347)
        agg[worker_code]["total"] = round(float(agg[worker_code]["total"]) + total_row, 2)
    return sorted(agg.values(), key=lambda item: float(item["total"]), reverse=True)


def get_edservice_aggregate(db: Session) -> List[Dict[str, object]]:
    service_name_by_code = {item.legacy_code: item.name for item in db.query(ServiceCatalogItem).all()}
    rows = db.query(LegacyEdServiceRow).all()
    agg: Dict[str, Dict[str, object]] = {}
    for row in rows:
        code = (row.service_code or "0000").zfill(4)
        if code not in agg:
            agg[code] = {"service_code": code, "service_name": service_name_by_code.get(code, ""), "qty": 0, "revenue": 0.0}
        agg[code]["qty"] = int(agg[code]["qty"]) + 1
        agg[code]["revenue"] = round(float(agg[code]["revenue"]) + float(row.amount), 2)
    return sorted(agg.values(), key=lambda item: float(item["revenue"]), reverse=True)


def get_fiche_documents(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    service_name_by_code = {item.legacy_code: item.name for item in db.query(ServiceCatalogItem).all()}
    query = db.query(LegacyFicheLine)
    if salon_id is not None:
        query = query.filter(LegacyFicheLine.salon_id == salon_id)
    rows = query.all()
    grouped: Dict[tuple[str, str], Dict[str, object]] = {}
    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        date_token = row.date_token or ""
        ticket_code = row.ticket_code or ""
        if not ticket_code:
            continue
        key = (date_token, ticket_code)
        payload = grouped.get(key)
        if payload is None:
            payload = {
                "date_token": date_token,
                "ticket_code": ticket_code,
                "lines_count": 0,
                "total_amount": 0.0,
                "payment_hint": row.payment_hint or "",
                "service_names": [],
            }
            grouped[key] = payload
        payload["lines_count"] = int(payload["lines_count"]) + 1
        payload["total_amount"] = round(float(payload["total_amount"]) + float(row.amount or 0), 2)
        service_code = (row.service_code or "").zfill(4)
        service_name = service_name_by_code.get(service_code) or service_code
        names = payload["service_names"]
        if isinstance(names, list) and service_name not in names:
            names.append(service_name)
        if not payload["payment_hint"] and row.payment_hint:
            payload["payment_hint"] = row.payment_hint

    out: List[Dict[str, object]] = []
    for payload in grouped.values():
        out.append(
            {
                "date_token": str(payload["date_token"]),
                "ticket_code": str(payload["ticket_code"]),
                "lines_count": int(payload["lines_count"]),
                "total_amount": float(payload["total_amount"]),
                "payment_hint": str(payload["payment_hint"] or ""),
                "services": ", ".join(payload["service_names"][:8]) if isinstance(payload["service_names"], list) else "",
            }
        )
    return sorted(out, key=lambda item: (item["date_token"], item["ticket_code"]), reverse=True)


def get_fiche_service_lines(
    db: Session, from_date: Optional[date], to_date: Optional[date], salon_id: Optional[int] = None
) -> List[Dict[str, object]]:
    service_name_by_code = {item.legacy_code: item.name for item in db.query(ServiceCatalogItem).all()}
    staff_name_by_code, worker_card_name_by_code = _build_worker_name_maps(db, salon_id)

    query = db.query(LegacyFicheLine)
    if salon_id is not None:
        query = query.filter(LegacyFicheLine.salon_id == salon_id)
    rows = query.all()

    # Try to resolve time from mapped appointments (if legacy document is linked).
    doc_query = db.query(LegacyVisitDocument)
    if salon_id is not None:
        doc_query = doc_query.filter(LegacyVisitDocument.salon_id == salon_id)
    doc_rows = doc_query.all()
    doc_to_appt: Dict[tuple[int, str, str], int] = {}
    appt_ids: set[int] = set()
    for doc in doc_rows:
        if not _in_range(doc.date_token, from_date, to_date):
            continue
        if doc.mapped_appointment_id is None:
            continue
        key = (int(doc.salon_id or 0), str(doc.date_token or ""), str(doc.ticket_code or ""))
        doc_to_appt[key] = int(doc.mapped_appointment_id)
        appt_ids.add(int(doc.mapped_appointment_id))

    appt_start_by_id: Dict[int, datetime] = {}
    if appt_ids:
        for appt in db.query(Appointment).filter(Appointment.id.in_(appt_ids)).all():
            if appt.start_at:
                appt_start_by_id[int(appt.id)] = appt.start_at

    out: List[Dict[str, object]] = []
    for row in rows:
        if not _in_range(row.date_token, from_date, to_date):
            continue
        worker_code = (row.worker_code or "").zfill(2)
        worker_name = (
            staff_name_by_code.get(worker_code)
            or worker_card_name_by_code.get(worker_code)
            or ""
        )
        lookup_key = (int(row.salon_id or 0), str(row.date_token or ""), str(row.ticket_code or ""))
        appt_id = doc_to_appt.get(lookup_key)
        start_at = appt_start_by_id.get(int(appt_id)) if appt_id is not None else None
        time_label = start_at.strftime("%H:%M") if start_at is not None else ""
        service_code = (row.service_code or "").zfill(4)
        service_name = service_name_by_code.get(service_code) or service_code
        out.append(
            {
                "date_token": row.date_token or "",
                "time_label": time_label,
                "ticket_code": row.ticket_code or "",
                "line_code": row.line_code or "",
                "worker_code": worker_code,
                "worker_name": worker_name,
                "service_code": service_code,
                "service_name": service_name,
                "amount": float(row.amount or 0),
                "payment_hint": row.payment_hint or "",
            }
        )

    return sorted(out, key=lambda item: (item["date_token"], item["ticket_code"], item["line_code"]), reverse=True)


def get_available_fiche_months(db: Session, salon_id: Optional[int] = None) -> List[str]:
    query = db.query(LegacyFicheLine)
    if salon_id is not None:
        query = query.filter(LegacyFicheLine.salon_id == salon_id)
    months: set[str] = set()
    for row in query.with_entities(LegacyFicheLine.date_token).all():
        token = (row[0] or "").strip()
        parsed = _parse_legacy_date(token)
        if parsed is not None:
            months.add(parsed.strftime("%Y-%m"))
    return sorted(months, reverse=True)


def _as_double(chunk: bytes, offset: int) -> float:
    if offset + 8 > len(chunk):
        return 0.0
    value = struct.unpack("<d", chunk[offset : offset + 8])[0]
    if not (0 <= value <= 1_000_000):
        return 0.0
    return round(float(value), 2)


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


def _parse_fiche_rows(content: bytes) -> list[dict[str, object]]:
    chunks, rows = _parse_records(content)
    out: list[dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 9 or not row[8].isdigit():
            continue
        amount = _as_double(chunk, 44)
        if amount <= 0:
            continue
        payment_hint = ""
        for token in row[12:]:
            upper = token.upper()
            if "KARTA" in upper:
                payment_hint = "KARTA"
                break
            if "GOTOW" in upper:
                payment_hint = "GOTOWKA"
                break
            if "VOUCHER" in upper:
                payment_hint = "VOUCHER"
                break
            if "ZAPR" in upper:
                payment_hint = "ZAPROSZENIE"
                break
        out.append(
            {
                "row_index": idx,
                "ticket_code": row[0] if len(row) > 0 else "",
                "line_code": row[1] if len(row) > 1 else "",
                "date_token": row[4] if len(row) > 4 and row[4].isdigit() else "",
                "worker_code": row[5].zfill(2) if len(row) > 5 and row[5].isdigit() else "",
                "service_code": row[8].zfill(4),
                "amount": amount,
                "payment_hint": payment_hint,
                "bundle_code": row[27] if len(row) > 27 else "",
            }
        )
    return out


def _parse_forfait_transactions(content: bytes) -> list[dict[str, object]]:
    chunks, rows = _parse_records(content)
    out: list[dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 5 or not row[1].isdigit():
            continue
        out.append(
            {
                "row_index": idx,
                "bundle_code": row[1].zfill(4),
                "bundle_name": row[3].strip(),
                "date_token": row[4] if row[4].isdigit() else "",
                "price": _as_double(chunk, 56),
            }
        )
    return out


def _connect_legacy_smb() -> SMBConnection:
    conn = SMBConnection(
        settings.LEGACY_SMB_USERNAME or "",
        settings.LEGACY_SMB_PASSWORD or "",
        "studio_suite_legacy_reports",
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


def rebuild_legacy_fiche_reports(db: Session) -> Dict[str, int]:
    """Import legacy report tables from SMB shares without deleting historical months."""

    inserted_fiche_lines = 0
    inserted_forfait_transactions = 0
    conn = _connect_legacy_smb()
    try:
        for salon in db.query(Salon).all():
            share = (salon.code or "").zfill(2)
            if not share:
                continue
            try:
                fiche_content = _read_smb_file(conn, share, "FICHE.FIC")
                fiche_rows = _parse_fiche_rows(fiche_content)
                imported_months = sorted(
                    {
                        str(row.get("date_token", "")).strip()[:6]
                        for row in fiche_rows
                        if str(row.get("date_token", "")).strip()[:6]
                    }
                )
                if imported_months:
                    db.query(LegacyFicheLine).filter(
                        LegacyFicheLine.salon_id == salon.id,
                        or_(*[LegacyFicheLine.date_token.like(f"{ym}%") for ym in imported_months]),
                    ).delete(synchronize_session=False)
                for row in fiche_rows:
                    db.add(
                        LegacyFicheLine(
                            salon_id=salon.id,
                            salon_code=share,
                            row_index=int(row["row_index"]),
                            ticket_code=str(row["ticket_code"] or ""),
                            line_code=str(row["line_code"] or ""),
                            date_token=str(row["date_token"] or ""),
                            worker_code=str(row["worker_code"] or ""),
                            service_code=str(row["service_code"] or ""),
                            amount=float(row["amount"] or 0),
                            payment_hint=str(row["payment_hint"] or ""),
                            bundle_code=str(row["bundle_code"] or ""),
                        )
                    )
                    inserted_fiche_lines += 1
            except Exception:
                pass
            try:
                forfaits_content = _read_smb_file(conn, share, "FORFAITS.FIC")
                forfait_rows = _parse_forfait_transactions(forfaits_content)
                imported_months = sorted(
                    {
                        str(row.get("date_token", "")).strip()[:6]
                        for row in forfait_rows
                        if str(row.get("date_token", "")).strip()[:6]
                    }
                )
                if imported_months:
                    db.query(LegacyForfaitTransaction).filter(
                        LegacyForfaitTransaction.salon_id == salon.id,
                        or_(*[LegacyForfaitTransaction.date_token.like(f"{ym}%") for ym in imported_months]),
                    ).delete(synchronize_session=False)
                for row in forfait_rows:
                    db.add(
                        LegacyForfaitTransaction(
                            salon_id=salon.id,
                            salon_code=share,
                            row_index=int(row["row_index"]),
                            date_token=str(row["date_token"] or ""),
                            bundle_code=str(row["bundle_code"] or ""),
                            bundle_name=str(row["bundle_name"] or ""),
                            price=float(row["price"] or 0),
                        )
                    )
                    inserted_forfait_transactions += 1
            except Exception:
                pass
    finally:
        conn.close()

    db.commit()
    return {
        "fiche_lines": inserted_fiche_lines,
        "forfait_transactions": inserted_forfait_transactions,
    }
