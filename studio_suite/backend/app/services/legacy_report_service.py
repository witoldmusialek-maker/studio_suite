"""
Reporting helpers for imported legacy salon datasets.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.salon_core import (
    BundleCatalog,
    LegacyEdition1Daily,
    LegacyEdServiceRow,
    LegacyFicheLine,
    LegacyForfaitTransaction,
    LegacyStat7Row,
    ServiceCatalogItem,
    Salon,
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
    db: Session, from_date: Optional[date], to_date: Optional[date]
) -> List[Dict[str, object]]:
    rows = db.query(LegacyForfaitTransaction).all()
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
    db: Session, from_date: Optional[date], to_date: Optional[date]
) -> List[Dict[str, object]]:
    service_name_by_code = {
        item.legacy_code: item.name for item in db.query(ServiceCatalogItem).all()
    }
    rows = db.query(LegacyFicheLine).all()
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

    staff_name_by_code: Dict[str, str] = {}
    from app.models.salon_core import StaffMember  # local import to avoid circular hinting

    for staff in db.query(StaffMember).all():
        if staff.legacy_code:
            staff_name_by_code[staff.legacy_code.zfill(2)] = staff.display_name

    for item in agg.values():
        item["worker_name"] = staff_name_by_code.get(item["worker_code"], "")

    return sorted(agg.values(), key=lambda item: float(item["revenue"]), reverse=True)


def get_monthly_summary(db: Session) -> List[Dict[str, object]]:
    rows = db.query(LegacyEdition1Daily).all()
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
    db: Session, from_date: Optional[date], to_date: Optional[date]
) -> List[Dict[str, object]]:
    rows = db.query(LegacyFicheLine).all()
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
    db: Session, from_date: Optional[date], to_date: Optional[date]
) -> List[Dict[str, object]]:
    rows = db.query(LegacyForfaitTransaction).all()
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
    db: Session, from_date: Optional[date], to_date: Optional[date]
) -> List[Dict[str, object]]:
    service_name_by_code = {item.legacy_code: item.name for item in db.query(ServiceCatalogItem).all()}
    rows = db.query(LegacyFicheLine).all()
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
    db: Session, from_date: Optional[date], to_date: Optional[date]
) -> List[Dict[str, object]]:
    rows = db.query(LegacyFicheLine).all()
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
