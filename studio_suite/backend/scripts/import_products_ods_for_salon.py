#!/usr/bin/env python3
"""
Import product catalog from ODS into global + salon-scoped product tables.
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import Base, SessionLocal, engine
from app.models import salon_core  # noqa: F401
from app.models.salon_core import LegacyProductCatalogItem, Salon, SalonProductCatalogItem

NS = {
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}


def parse_ods_rows(path: Path) -> List[List[str]]:
    with zipfile.ZipFile(path, "r") as zf:
        root = ET.fromstring(zf.read("content.xml"))
    table = root.find(".//table:table", NS)
    if table is None:
        return []
    rows: List[List[str]] = []
    for row in table.findall("table:table-row", NS):
        values: List[str] = []
        for cell in row.findall("table:table-cell", NS):
            repeated = int(
                cell.attrib.get("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated", "1")
            )
            text = "".join((p.text or "") for p in cell.findall(".//text:p", NS)).strip()
            values.extend([text] * repeated)
        if any(values):
            rows.append(values)
    return rows


def parse_package_size_g(token: str) -> float | None:
    raw = (token or "").lower().replace(",", ".").strip()
    if not raw:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", raw)
    if not m:
        return None
    value = float(m.group(1))
    if value <= 0:
        return None
    return round(value, 2)


def pick_name(pl_name: str, short_name: str) -> str:
    candidate = (pl_name or "").strip()
    if candidate:
        return candidate
    return (short_name or "").strip()


def normalize_default_doses(package_size_g: float | None) -> tuple[float, float, float]:
    if package_size_g is None:
        return 4.0, 2.0, 1.25
    if package_size_g >= 200:
        return 8.0, 4.0, 2.5
    if package_size_g >= 100:
        return 4.0, 2.0, 1.25
    if package_size_g >= 75:
        return 3.0, 1.5, 1.0
    return 2.0, 1.0, 0.75


def main() -> None:
    parser = argparse.ArgumentParser(description="Import ODS product base for selected salon.")
    parser.add_argument("--input-file", required=True, help="Path to .ods file")
    parser.add_argument("--salon-code", required=True, help="Salon code, e.g. 12")
    parser.add_argument("--salon-name", required=True, help="Salon name")
    parser.add_argument("--deactivate-missing", action="store_true")
    args = parser.parse_args()

    ods_file = Path(args.input_file)
    if not ods_file.exists():
        raise SystemExit(f"Input file not found: {ods_file}")

    rows = parse_ods_rows(ods_file)
    if not rows:
        raise SystemExit("No rows found in ODS")

    header = rows[0]
    idx: Dict[str, int] = {}
    for i, col in enumerate(header):
        if col and col not in idx:
            idx[col] = i

    required = ["ID_P", "NAZWAPL", "NAZWA1"]
    missing = [name for name in required if name not in idx]
    if missing:
        raise SystemExit(f"Missing required columns: {', '.join(missing)}")

    def col(row: List[str], name: str) -> str:
        i = idx.get(name)
        if i is None or i >= len(row):
            return ""
        return row[i].strip()

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

        processed_codes: set[str] = set()
        created_products = 0
        updated_products = 0
        linked_products = 0

        for row in rows[1:]:
            code_raw = col(row, "ID_P")
            code = code_raw.zfill(4) if code_raw.isdigit() else code_raw
            name = pick_name(col(row, "NAZWAPL"), col(row, "NAZWA1"))
            if not code or not name:
                continue
            processed_codes.add(code)

            package_size_g = parse_package_size_g(col(row, "POJ"))
            brand = col(row, "GRUPA") or None
            type_code = col(row, "CECHA_RODZINA") or None
            family_code = col(row, "rodzina2") or None

            product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.legacy_code == code).first()
            if product is None:
                product = LegacyProductCatalogItem(
                    legacy_code=code,
                    name=name,
                    type_code=type_code,
                    family_code=family_code,
                    brand_1=brand,
                    brand_2=None,
                    is_active=True,
                )
                db.add(product)
                db.flush()
                created_products += 1
            else:
                product.name = name
                product.type_code = type_code
                product.family_code = family_code
                product.brand_1 = brand
                product.is_active = True
                updated_products += 1

            link = (
                db.query(SalonProductCatalogItem)
                .filter(
                    SalonProductCatalogItem.salon_id == salon.id,
                    SalonProductCatalogItem.product_id == product.id,
                )
                .first()
            )
            doses_short, doses_medium, doses_long = normalize_default_doses(package_size_g)
            if link is None:
                link = SalonProductCatalogItem(
                    salon_id=salon.id,
                    product_id=product.id,
                    local_name=name if name != product.name else None,
                    package_size_g=package_size_g if package_size_g is not None else 100,
                    doses_short=doses_short,
                    doses_medium=doses_medium,
                    doses_long=doses_long,
                    is_active=True,
                )
                db.add(link)
            else:
                link.local_name = name if name != product.name else None
                if package_size_g is not None:
                    link.package_size_g = package_size_g
                if float(link.doses_short) <= 0:
                    link.doses_short = doses_short
                if float(link.doses_medium) <= 0:
                    link.doses_medium = doses_medium
                if float(link.doses_long) <= 0:
                    link.doses_long = doses_long
                link.is_active = True
            linked_products += 1

        if args.deactivate_missing:
            links = db.query(SalonProductCatalogItem).filter(SalonProductCatalogItem.salon_id == salon.id).all()
            for link in links:
                product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.id == link.product_id).first()
                if product and product.legacy_code not in processed_codes:
                    link.is_active = False

        db.commit()
        print(
            f"salon={salon.code} processed={len(processed_codes)} "
            f"products_created={created_products} products_updated={updated_products} linked_products={linked_products}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

