"""
Business logic for editable legacy catalog persisted in database.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.salon_core import (
    BundleCatalog,
    BundleCatalogItem,
    LegacyDictionaryEntry,
    Salon,
    SalonServiceCatalogItem,
    ServiceCatalogItem,
    ServicePriceHistory,
)


def _round_price(value: float) -> float:
    return round(float(value), 2)


def _ensure_salon(db: Session, salon_id: int) -> Salon:
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise ValueError("salon_not_found")
    return salon


def _ensure_salon_service_link(db: Session, salon_id: int, service_id: int) -> SalonServiceCatalogItem:
    link = (
        db.query(SalonServiceCatalogItem)
        .filter(
            SalonServiceCatalogItem.salon_id == salon_id,
            SalonServiceCatalogItem.service_id == service_id,
        )
        .first()
    )
    if link:
        return link
    link = SalonServiceCatalogItem(salon_id=salon_id, service_id=service_id, is_active=True)
    db.add(link)
    db.flush()
    return link


def _seed_missing_links_for_salon(db: Session, salon_id: int) -> None:
    existing_count = (
        db.query(func.count(SalonServiceCatalogItem.id))
        .filter(SalonServiceCatalogItem.salon_id == salon_id)
        .scalar()
        or 0
    )
    if existing_count > 0:
        return

    service_ids = [
        row[0]
        for row in db.query(ServicePriceHistory.service_id)
        .filter(ServicePriceHistory.salon_id == salon_id)
        .distinct()
        .all()
    ]
    if not service_ids:
        service_ids = [row[0] for row in db.query(ServiceCatalogItem.id).all()]

    for service_id in service_ids:
        db.add(SalonServiceCatalogItem(salon_id=salon_id, service_id=service_id, is_active=True))
    db.flush()


def _latest_prices_by_service_id(db: Session, salon_id: int = 1) -> dict[int, float]:
    latest_price_subquery = (
        db.query(
            ServicePriceHistory.service_id.label("service_id"),
            ServicePriceHistory.salon_id.label("salon_id"),
            func.max(ServicePriceHistory.id).label("max_id"),
        )
        .group_by(ServicePriceHistory.service_id, ServicePriceHistory.salon_id)
        .subquery()
    )
    latest_prices = (
        db.query(ServicePriceHistory)
        .join(latest_price_subquery, ServicePriceHistory.id == latest_price_subquery.c.max_id)
        .all()
    )
    return {
        row.service_id: _round_price(row.price)
        for row in latest_prices
        if (row.salon_id or salon_id) == salon_id
    }


def _recalculate_bundle_price(db: Session, bundle_id: int, salon_id: int = 1) -> float:
    bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id).first()
    if not bundle:
        raise ValueError("bundle_not_found")
    items = (
        db.query(BundleCatalogItem)
        .filter(BundleCatalogItem.bundle_id == bundle_id)
        .order_by(BundleCatalogItem.position.asc())
        .all()
    )
    service_defaults = _latest_prices_by_service_id(db, salon_id=salon_id)
    service_rows = db.query(ServiceCatalogItem).all()
    fallback_price = {row.id: _round_price(row.default_price) for row in service_rows}

    total = 0.0
    for item in items:
        if item.override_price is not None:
            total += _round_price(item.override_price)
        elif item.service_id:
            total += service_defaults.get(item.service_id, fallback_price.get(item.service_id, 0.0))

    bundle.price = _round_price(total)
    db.flush()
    return _round_price(bundle.price)


def get_legacy_catalog(db: Session, salon_id: int = 1) -> dict:
    _ensure_salon(db, salon_id)
    _seed_missing_links_for_salon(db, salon_id)
    price_by_service_id = _latest_prices_by_service_id(db, salon_id=salon_id)

    links = (
        db.query(SalonServiceCatalogItem)
        .filter(SalonServiceCatalogItem.salon_id == salon_id, SalonServiceCatalogItem.is_active == True)  # noqa: E712
        .all()
    )
    service_ids = [link.service_id for link in links]
    services = (
        db.query(ServiceCatalogItem)
        .filter(ServiceCatalogItem.id.in_(service_ids) if service_ids else False)
        .order_by(ServiceCatalogItem.legacy_code.asc())
        .all()
    )
    link_by_service_id = {link.service_id: link for link in links}

    service_prices = []
    for service in services:
        link = link_by_service_id.get(service.id)
        current_price = price_by_service_id.get(service.id, _round_price(service.default_price))
        service_prices.append(
            {
                "service_id": service.id,
                "service_code": service.legacy_code,
                "service_name": (link.local_name if link and link.local_name else service.name),
                "salon_id": salon_id,
                "price": _round_price(current_price),
                "duration_minutes": int(service.duration_minutes or 0),
                "is_active": bool(service.is_active and (link.is_active if link else True)),
            }
        )

    bundles = (
        db.query(BundleCatalog)
        .filter(BundleCatalog.salon_id == salon_id)
        .order_by(BundleCatalog.legacy_code.asc())
        .all()
    )
    bundle_ids = [bundle.id for bundle in bundles]
    bundle_items = (
        db.query(BundleCatalogItem)
        .filter(BundleCatalogItem.bundle_id.in_(bundle_ids) if bundle_ids else False)
        .order_by(BundleCatalogItem.bundle_id.asc(), BundleCatalogItem.position.asc())
        .all()
    )
    service_by_id = {service.id: service for service in services}
    items_by_bundle: dict[int, list[dict]] = {}
    for item in bundle_items:
        service = service_by_id.get(item.service_id) if item.service_id else None
        service_name = ""
        if service:
            link = link_by_service_id.get(service.id)
            service_name = link.local_name if link and link.local_name else service.name
        items_by_bundle.setdefault(item.bundle_id, []).append(
            {
                "position": item.position,
                "service_id": item.service_id,
                "service_code": item.service_legacy_code,
                "service_name": service_name,
                "override_price": float(item.override_price) if item.override_price is not None else None,
            }
        )

    bundles_payload = [
        {
            "bundle_id": bundle.id,
            "salon_id": bundle.salon_id,
            "bundle_code": bundle.legacy_code,
            "bundle_name": bundle.name,
            "price": _round_price(bundle.price),
            "items": items_by_bundle.get(bundle.id, []),
        }
        for bundle in bundles
    ]

    return {"service_prices": service_prices, "bundles": bundles_payload}


def update_service_price(db: Session, service_id: int, salon_id: int, price: float) -> dict:
    _ensure_salon(db, salon_id)
    service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == service_id).first()
    if not service:
        raise ValueError("service_not_found")
    _ensure_salon_service_link(db, salon_id=salon_id, service_id=service.id)

    db.add(
        ServicePriceHistory(
            service_id=service_id,
            salon_id=salon_id,
            price=price,
            holiday_price=float(service.holiday_price),
            source="manual_update",
        )
    )
    affected_bundle_ids = [
        row[0]
        for row in db.query(BundleCatalogItem.bundle_id)
        .join(BundleCatalog, BundleCatalog.id == BundleCatalogItem.bundle_id)
        .filter(BundleCatalogItem.service_id == service_id, BundleCatalog.salon_id == salon_id)
        .all()
    ]
    for bundle_id in set(affected_bundle_ids):
        _recalculate_bundle_price(db, bundle_id=bundle_id, salon_id=salon_id)
    db.commit()
    db.refresh(service)
    return {"service_id": service.id, "price": _round_price(price)}


def update_bundle_price(db: Session, bundle_id: int, price: float) -> dict:
    bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id).first()
    if not bundle:
        raise ValueError("bundle_not_found")
    bundle.price = price
    db.commit()
    db.refresh(bundle)
    return {"bundle_id": bundle.id, "price": float(bundle.price)}


def update_bundle_item_price(db: Session, bundle_id: int, position: int, override_price: float | None) -> dict:
    item = (
        db.query(BundleCatalogItem)
        .filter(BundleCatalogItem.bundle_id == bundle_id, BundleCatalogItem.position == position)
        .first()
    )
    if not item:
        raise ValueError("bundle_item_not_found")
    item.override_price = override_price
    bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id).first()
    if not bundle:
        raise ValueError("bundle_not_found")
    _recalculate_bundle_price(db, bundle_id=bundle_id, salon_id=bundle.salon_id or 1)
    db.commit()
    db.refresh(item)
    return {
        "bundle_id": bundle_id,
        "position": position,
        "override_price": _round_price(item.override_price) if item.override_price is not None else None,
    }


def create_bundle(db: Session, bundle_code: str, bundle_name: str, salon_id: int = 1) -> dict:
    _ensure_salon(db, salon_id)
    existing = (
        db.query(BundleCatalog)
        .filter(BundleCatalog.legacy_code == bundle_code, BundleCatalog.salon_id == salon_id)
        .first()
    )
    if existing:
        raise ValueError("bundle_code_exists")
    bundle = BundleCatalog(
        legacy_code=bundle_code,
        salon_id=salon_id,
        name=bundle_name,
        frequency_mode="week_and_holiday",
        price=0,
    )
    db.add(bundle)
    db.commit()
    db.refresh(bundle)
    return {"bundle_id": bundle.id, "bundle_code": bundle.legacy_code}


def delete_bundle(db: Session, bundle_id: int) -> None:
    bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id).first()
    if not bundle:
        raise ValueError("bundle_not_found")
    db.query(BundleCatalogItem).filter(BundleCatalogItem.bundle_id == bundle_id).delete()
    db.delete(bundle)
    db.commit()


def add_bundle_item(db: Session, bundle_id: int, service_id: int, override_price: float | None) -> dict:
    bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id).first()
    if not bundle:
        raise ValueError("bundle_not_found")
    service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == service_id).first()
    if not service:
        raise ValueError("service_not_found")
    link = (
        db.query(SalonServiceCatalogItem)
        .filter(
            SalonServiceCatalogItem.salon_id == (bundle.salon_id or 1),
            SalonServiceCatalogItem.service_id == service_id,
            SalonServiceCatalogItem.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not link:
        raise ValueError("service_not_available_in_salon")

    max_position = (
        db.query(func.max(BundleCatalogItem.position))
        .filter(BundleCatalogItem.bundle_id == bundle_id)
        .scalar()
        or 0
    )
    item = BundleCatalogItem(
        bundle_id=bundle_id,
        position=int(max_position) + 1,
        service_id=service_id,
        service_legacy_code=service.legacy_code,
        override_price=override_price,
    )
    db.add(item)
    _recalculate_bundle_price(db, bundle_id=bundle_id, salon_id=bundle.salon_id or 1)
    db.commit()
    db.refresh(item)
    return {"bundle_id": bundle_id, "position": item.position}


def delete_bundle_item(db: Session, bundle_id: int, position: int) -> None:
    item = (
        db.query(BundleCatalogItem)
        .filter(BundleCatalogItem.bundle_id == bundle_id, BundleCatalogItem.position == position)
        .first()
    )
    if not item:
        raise ValueError("bundle_item_not_found")
    db.delete(item)
    db.flush()

    items = (
        db.query(BundleCatalogItem)
        .filter(BundleCatalogItem.bundle_id == bundle_id)
        .order_by(BundleCatalogItem.position.asc())
        .all()
    )
    for index, row in enumerate(items, start=1):
        row.position = index

    bundle = db.query(BundleCatalog).filter(BundleCatalog.id == bundle_id).first()
    if not bundle:
        raise ValueError("bundle_not_found")
    _recalculate_bundle_price(db, bundle_id=bundle_id, salon_id=bundle.salon_id or 1)
    db.commit()


def create_service(
    db: Session,
    service_code: str,
    service_name: str,
    duration_minutes: int,
    default_price: float,
    salon_id: int = 1,
) -> dict:
    _ensure_salon(db, salon_id)
    code = service_code.strip().upper()
    name = service_name.strip()
    if not code or not name:
        raise ValueError("invalid_payload")

    existing = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.legacy_code == code).first()
    if existing:
        link = _ensure_salon_service_link(db, salon_id=salon_id, service_id=existing.id)
        link.is_active = True
        link.local_name = name if name != existing.name else None
        db.add(
            ServicePriceHistory(
                service_id=existing.id,
                salon_id=salon_id,
                price=default_price,
                holiday_price=default_price,
                source="manual_create_attach",
            )
        )
        db.commit()
        db.refresh(existing)
        return {
            "service_id": existing.id,
            "service_code": existing.legacy_code,
            "service_name": link.local_name or existing.name,
            "duration_minutes": int(existing.duration_minutes or 0),
            "default_price": _round_price(default_price),
            "is_active": bool(link.is_active and existing.is_active),
        }

    service = ServiceCatalogItem(
        legacy_code=code,
        name=name,
        duration_minutes=int(duration_minutes),
        default_price=default_price,
        holiday_price=default_price,
        is_active=True,
    )
    db.add(service)
    db.flush()
    db.add(SalonServiceCatalogItem(salon_id=salon_id, service_id=service.id, is_active=True, local_name=None))
    db.add(
        ServicePriceHistory(
            service_id=service.id,
            salon_id=salon_id,
            price=default_price,
            holiday_price=default_price,
            source="manual_create",
        )
    )

    db.commit()
    db.refresh(service)
    return {
        "service_id": service.id,
        "service_code": service.legacy_code,
        "service_name": service.name,
        "duration_minutes": int(service.duration_minutes or 0),
        "default_price": _round_price(service.default_price),
        "is_active": bool(service.is_active),
    }


def update_service(
    db: Session,
    service_id: int,
    service_name: str | None,
    duration_minutes: int | None,
    default_price: float | None,
    is_active: bool | None,
    local_name: str | None,
    salon_id: int = 1,
) -> dict:
    _ensure_salon(db, salon_id)
    service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == service_id).first()
    if not service:
        raise ValueError("service_not_found")
    link = _ensure_salon_service_link(db, salon_id=salon_id, service_id=service.id)

    if service_name is not None:
        clean_name = service_name.strip()
        if not clean_name:
            raise ValueError("invalid_payload")
        service.name = clean_name

    if local_name is not None:
        cleaned_local = local_name.strip()
        link.local_name = cleaned_local or None

    if duration_minutes is not None:
        service.duration_minutes = int(duration_minutes)

    price_changed = False
    resolved_price = service.default_price
    if default_price is not None:
        rounded_price = _round_price(default_price)
        resolved_price = rounded_price
        db.add(
            ServicePriceHistory(
                service_id=service.id,
                salon_id=salon_id,
                price=rounded_price,
                holiday_price=rounded_price,
                source="manual_update",
            )
        )
        price_changed = True

    if is_active is not None:
        link.is_active = bool(is_active)

    if price_changed:
        affected_bundle_ids = [
            row[0]
            for row in db.query(BundleCatalogItem.bundle_id)
            .join(BundleCatalog, BundleCatalog.id == BundleCatalogItem.bundle_id)
            .filter(BundleCatalogItem.service_id == service.id, BundleCatalog.salon_id == salon_id)
            .all()
        ]
        for bundle_id in set(affected_bundle_ids):
            _recalculate_bundle_price(db, bundle_id=bundle_id, salon_id=salon_id)

    db.commit()
    db.refresh(service)
    return {
        "service_id": service.id,
        "service_code": service.legacy_code,
        "service_name": link.local_name or service.name,
        "duration_minutes": int(service.duration_minutes or 0),
        "default_price": _round_price(resolved_price),
        "is_active": bool(service.is_active and link.is_active),
    }


def delete_service(db: Session, service_id: int, salon_id: int) -> None:
    _ensure_salon(db, salon_id)
    service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == service_id).first()
    if not service:
        raise ValueError("service_not_found")

    in_bundle = (
        db.query(BundleCatalogItem.id)
        .join(BundleCatalog, BundleCatalog.id == BundleCatalogItem.bundle_id)
        .filter(BundleCatalogItem.service_id == service.id, BundleCatalog.salon_id == salon_id)
        .first()
    )
    if in_bundle:
        raise ValueError("service_in_bundle")

    link = (
        db.query(SalonServiceCatalogItem)
        .filter(SalonServiceCatalogItem.salon_id == salon_id, SalonServiceCatalogItem.service_id == service.id)
        .first()
    )
    if not link:
        raise ValueError("service_not_found")
    link.is_active = False
    link.local_name = None
    db.commit()


def parse_vat_percent_by_service(db: Session) -> dict[str, float]:
    vat_entries = (
        db.query(LegacyDictionaryEntry)
        .filter(LegacyDictionaryEntry.dictionary_name == "vat_codes")
        .all()
    )
    vat_percent_by_code: dict[str, float] = {}
    for entry in vat_entries:
        token = (entry.label or "").replace(",", ".").strip()
        try:
            vat_percent_by_code[entry.code] = float(token)
        except ValueError:
            vat_percent_by_code[entry.code] = 0.0

    service_rows = db.query(ServiceCatalogItem).all()
    service_vat_percent: dict[str, float] = {}
    for service in service_rows:
        service_vat_percent[service.legacy_code] = vat_percent_by_code.get(service.vat_code or "", 0.0)
    return service_vat_percent
