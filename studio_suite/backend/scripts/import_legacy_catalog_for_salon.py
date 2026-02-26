#!/usr/bin/env python3
"""
Import services and bundles from legacy FIC files into a selected salon scope.
This script is safe for multi-salon setup:
- service catalog is global,
- prices, availability and bundles are salon-specific.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import Base, SessionLocal, engine
from app.models import salon_core  # noqa: F401
from app.models.salon_core import (
    BundleCatalog,
    BundleCatalogItem,
    LegacyProductCatalogItem,
    Salon,
    SalonServiceCatalogItem,
    ServiceCatalogItem,
    ServicePriceHistory,
)


def parse_records(path: Path) -> Tuple[int, List[bytes], List[List[str]]]:
    data = path.read_bytes()
    rec_len = int(data[7:11].decode("ascii"))
    offset = rec_len
    total = max(0, (len(data) - offset) // rec_len)
    chunks: List[bytes] = []
    rows: List[List[str]] = []
    for i in range(total):
        chunk = data[offset + i * rec_len : offset + (i + 1) * rec_len]
        chunks.append(chunk)
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        rows.append(parts)
    return rec_len, chunks, rows


def as_double(chunk: bytes, offset: int) -> float:
    if offset + 8 > len(chunk):
        return 0.0
    value = struct.unpack("<d", chunk[offset : offset + 8])[0]
    if not (0 <= value <= 1_000_000):
        return 0.0
    return round(value, 2)


def parse_service_catalog(service_fic: Path) -> Dict[str, Dict[str, object]]:
    _, chunks, rows = parse_records(service_fic)
    out: Dict[str, Dict[str, object]] = {}
    for chunk, row in zip(chunks, rows):
        if len(row) < 4 or not row[0].isdigit():
            continue
        code = row[0].zfill(4)
        duration_raw = row[9] if len(row) > 9 else "60"
        duration_minutes = int(duration_raw) if duration_raw.isdigit() else 60
        out[code] = {
            "name": row[3].strip(),
            "service_type_code": row[1].strip() if len(row) > 1 else "",
            "grouping_code": row[2].strip() if len(row) > 2 else "",
            "family_code": row[7].strip() if len(row) > 7 else "",
            "vat_code": row[8].strip() if len(row) > 8 else "",
            "duration_minutes": duration_minutes,
            "price_regular": as_double(chunk, 46),
            "price_holiday": as_double(chunk, 54),
        }
    return out


def parse_bundle_lines(forfait_fic: Path) -> Dict[str, Dict[str, object]]:
    _, chunks, rows = parse_records(forfait_fic)
    bundles: Dict[str, Dict[str, object]] = {}
    for chunk, row in zip(chunks, rows):
        if len(row) < 3 or not row[0].isdigit():
            continue
        code = row[0].zfill(4)
        name = row[1].strip()
        service_codes = [p for p in row[3:] if p.isdigit() and len(p) == 4]
        item_prices: List[float] = []
        for idx in range(len(service_codes)):
            item_prices.append(as_double(chunk, 89 + idx * 8))
        bundles[code] = {
            "name": name,
            "service_codes": service_codes,
            "item_prices": item_prices,
        }
    return bundles


def parse_products_catalog(products_fic: Path) -> Dict[str, Dict[str, str]]:
    _, _, rows = parse_records(products_fic)
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        if len(row) < 3 or not row[0].isdigit():
            continue
        code = row[0].zfill(4)
        out[code] = {
            "name": row[2].strip(),
            "type_code": row[1].strip() if len(row) > 1 else "",
            "family_code": row[3].strip() if len(row) > 3 else "",
            "brand_1": row[6].strip() if len(row) > 6 else "",
            "brand_2": row[8].strip() if len(row) > 8 else "",
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Import legacy services/bundles into selected salon scope.")
    parser.add_argument("--input-dir", required=True, help="Directory with SERVICE.FIC and FORFAIT.FIC")
    parser.add_argument("--salon-code", required=True, help="Salon code, e.g. 12")
    parser.add_argument("--salon-name", required=True, help="Salon name")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")
    for required in ("SERVICE.FIC", "FORFAIT.FIC", "PRODUITS.FIC"):
        if not (input_dir / required).exists():
            raise SystemExit(f"Missing required file: {required}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        salon = db.query(Salon).filter(Salon.code == args.salon_code).first()
        if salon is None:
            salon = Salon(code=args.salon_code, name=args.salon_name, is_active=True)
            db.add(salon)
            db.flush()
        else:
            salon.name = args.salon_name
            salon.is_active = True

        service_meta_by_code = parse_service_catalog(input_dir / "SERVICE.FIC")
        products_meta_by_code = parse_products_catalog(input_dir / "PRODUITS.FIC")
        imported_codes = set(service_meta_by_code.keys())

        created_products = 0
        updated_products = 0
        existing_products = {
            row.legacy_code: row for row in db.query(LegacyProductCatalogItem).all()
        }
        for product_code, product_meta in sorted(products_meta_by_code.items()):
            row = existing_products.get(product_code)
            if row is None:
                row = LegacyProductCatalogItem(
                    legacy_code=product_code,
                    name=product_meta["name"] or product_code,
                    type_code=product_meta["type_code"] or None,
                    family_code=product_meta["family_code"] or None,
                    brand_1=product_meta["brand_1"] or None,
                    brand_2=product_meta["brand_2"] or None,
                    is_active=True,
                )
                db.add(row)
                created_products += 1
            else:
                row.name = product_meta["name"] or row.name
                row.type_code = product_meta["type_code"] or None
                row.family_code = product_meta["family_code"] or None
                row.brand_1 = product_meta["brand_1"] or None
                row.brand_2 = product_meta["brand_2"] or None
                row.is_active = True
                updated_products += 1

        existing_services = db.query(ServiceCatalogItem).all()
        service_by_code = {row.legacy_code: row for row in existing_services}

        # Reset salon links/prices before full refresh.
        db.query(SalonServiceCatalogItem).filter(SalonServiceCatalogItem.salon_id == salon.id).update(
            {SalonServiceCatalogItem.is_active: False, SalonServiceCatalogItem.local_name: None}
        )
        db.query(ServicePriceHistory).filter(ServicePriceHistory.salon_id == salon.id).delete()

        service_id_by_code: Dict[str, int] = {}
        created_services = 0
        linked_services = 0
        for code, meta in sorted(service_meta_by_code.items()):
            existing = service_by_code.get(code)
            if existing is None:
                existing = ServiceCatalogItem(
                    legacy_code=code,
                    name=str(meta["name"]),
                    service_type_code=str(meta["service_type_code"]),
                    grouping_code=str(meta["grouping_code"]),
                    family_code=str(meta["family_code"]),
                    vat_code=str(meta["vat_code"]),
                    duration_minutes=int(meta["duration_minutes"]),
                    default_price=float(meta["price_regular"]),
                    holiday_price=float(meta["price_holiday"]),
                    is_active=True,
                )
                db.add(existing)
                db.flush()
                service_by_code[code] = existing
                created_services += 1

            service_id_by_code[code] = existing.id
            link = (
                db.query(SalonServiceCatalogItem)
                .filter(
                    SalonServiceCatalogItem.salon_id == salon.id,
                    SalonServiceCatalogItem.service_id == existing.id,
                )
                .first()
            )
            if link is None:
                link = SalonServiceCatalogItem(
                    salon_id=salon.id,
                    service_id=existing.id,
                    is_active=True,
                )
                db.add(link)
            link.is_active = True
            link.local_name = str(meta["name"]) if str(meta["name"]) != existing.name else None
            linked_services += 1

            db.add(
                ServicePriceHistory(
                    service_id=existing.id,
                    salon_id=salon.id,
                    price=float(meta["price_regular"]),
                    holiday_price=float(meta["price_holiday"]),
                    source="legacy_import_service_fic",
                )
            )

        # Hard refresh bundles for this salon only.
        existing_bundle_ids = [
            row[0]
            for row in db.query(BundleCatalog.id).filter(BundleCatalog.salon_id == salon.id).all()
        ]
        if existing_bundle_ids:
            db.query(BundleCatalogItem).filter(BundleCatalogItem.bundle_id.in_(existing_bundle_ids)).delete(
                synchronize_session=False
            )
            db.query(BundleCatalog).filter(BundleCatalog.id.in_(existing_bundle_ids)).delete(
                synchronize_session=False
            )

        bundles = parse_bundle_lines(input_dir / "FORFAIT.FIC")
        created_bundles = 0
        created_bundle_items = 0
        for bundle_code, bundle_data in sorted(bundles.items()):
            service_codes = [code for code in bundle_data["service_codes"] if code in service_id_by_code]
            item_prices = bundle_data.get("item_prices", [])

            computed_price = 0.0
            for idx, service_code in enumerate(service_codes):
                override = float(item_prices[idx]) if idx < len(item_prices) else 0.0
                if override > 0:
                    computed_price += override
                else:
                    computed_price += float(service_meta_by_code[service_code]["price_regular"])

            bundle = BundleCatalog(
                legacy_code=bundle_code,
                salon_id=salon.id,
                name=str(bundle_data["name"]),
                frequency_mode="week_and_holiday",
                price=round(computed_price, 2),
            )
            db.add(bundle)
            db.flush()
            created_bundles += 1

            for idx, service_code in enumerate(service_codes):
                override = float(item_prices[idx]) if idx < len(item_prices) else 0.0
                db.add(
                    BundleCatalogItem(
                        bundle_id=bundle.id,
                        position=idx + 1,
                        service_id=service_id_by_code.get(service_code),
                        service_legacy_code=service_code,
                        override_price=override if override > 0 else None,
                    )
                )
                created_bundle_items += 1

        # Deactivate links missing in import payload.
        for link in db.query(SalonServiceCatalogItem).filter(SalonServiceCatalogItem.salon_id == salon.id).all():
            service = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == link.service_id).first()
            if service and service.legacy_code not in imported_codes:
                link.is_active = False
                link.local_name = None

        db.commit()
        print(
            f"salon={salon.code} created_services={created_services} linked_services={linked_services} "
            f"bundles={created_bundles} bundle_items={created_bundle_items} "
            f"products_created={created_products} products_updated={updated_products}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
