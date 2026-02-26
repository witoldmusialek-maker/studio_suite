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

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base, SessionLocal, engine
from app.models import salon_core  # noqa: F401
from app.models.salon_core import (
    LegacyProductCatalogItem,
    Salon,
    SalonProductCatalogItem,
    SalonServiceFormulaItem,
)

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


def parse_price_value(token: str) -> float | None:
    raw = (token or "").strip().replace(",", ".")
    if not raw:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not m:
        return None
    try:
        value = float(m.group(0))
    except ValueError:
        return None
    if value < 0:
        return None
    return round(value, 2)


def parse_stock_value(token: str) -> float | None:
    raw = (token or "").strip().replace(",", ".")
    if not raw:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not m:
        return None
    try:
        return round(float(m.group(0)), 2)
    except ValueError:
        return None


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


def trunc(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    clean = value.strip()
    if not clean:
        return None
    return clean[:max_len]


def main() -> None:
    parser = argparse.ArgumentParser(description="Import ODS product base for selected salon.")
    parser.add_argument("--input-file", required=True, help="Path to .ods file")
    parser.add_argument("--salon-code", required=True, help="Salon code, e.g. 12")
    parser.add_argument("--salon-name", required=True, help="Salon name")
    parser.add_argument("--deactivate-missing", action="store_true")
    parser.add_argument("--replace-all", action="store_true", help="Delete existing product base and replace in full")
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

    required = ["ID_P", "NAZWAPL", "NAZWA1", "FISK", "POJ", "CENASPBRT"]
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

        if args.replace_all:
            db.query(SalonServiceFormulaItem).delete()
            db.query(SalonProductCatalogItem).delete()
            db.query(LegacyProductCatalogItem).delete()
            db.flush()

        processed_codes: set[str] = set()
        processed_links: set[tuple[int, int]] = set()
        created_products = 0
        updated_products = 0
        linked_products = 0
        link_by_product_id = {
            row.product_id: row
            for row in db.query(SalonProductCatalogItem).filter(SalonProductCatalogItem.salon_id == salon.id).all()
        }

        for row in rows[1:]:
            code_raw = col(row, "ID_P")
            code = code_raw.zfill(4) if code_raw.isdigit() else code_raw
            name = col(row, "NAZWA1")
            name_pl = col(row, "NAZWAPL")
            if not code or not name:
                continue
            processed_codes.add(code)

            package_size_g = parse_package_size_g(col(row, "POJ"))
            fiscal_code = trunc(col(row, "FISK"), 32)
            catalog_price = parse_price_value(col(row, "cena_sp_f") or col(row, "F"))
            sale_price_gross = parse_price_value(col(row, "CENASPBRT"))
            stock_mx03 = parse_stock_value(col(row, "MX03"))
            stock_mx04 = parse_stock_value(col(row, "MX04"))
            stock_mx07 = parse_stock_value(col(row, "MX07"))
            brand = trunc(col(row, "GRUPA"), 128)
            type_code = trunc(col(row, "CECHA_RODZINA"), 16)
            family_code = trunc(col(row, "rodzina2"), 16)
            s_u_token = (col(row, "S_U") or "").strip()
            s_u = s_u_token in {"1", "true", "TRUE", "t", "T", "yes", "YES"}

            product = db.query(LegacyProductCatalogItem).filter(LegacyProductCatalogItem.legacy_code == code).first()
            if product is None:
                product = LegacyProductCatalogItem(
                    legacy_code=code,
                    name=name,
                    name_pl=name_pl or None,
                    fiscal_code=fiscal_code,
                    type_code=type_code,
                    family_code=family_code,
                    brand_1=brand,
                    brand_2=None,
                    catalog_price=catalog_price,
                    sale_price_gross=sale_price_gross,
                    s_u=s_u,
                    stock_mx03=stock_mx03,
                    stock_mx04=stock_mx04,
                    stock_mx07=stock_mx07,
                    is_active=True,
                )
                db.add(product)
                db.flush()
                created_products += 1
            else:
                product.name = name
                product.name_pl = name_pl or None
                product.fiscal_code = fiscal_code
                product.type_code = type_code
                product.family_code = family_code
                product.brand_1 = brand
                product.catalog_price = catalog_price
                product.sale_price_gross = sale_price_gross
                product.s_u = s_u
                product.stock_mx03 = stock_mx03
                product.stock_mx04 = stock_mx04
                product.stock_mx07 = stock_mx07
                product.is_active = True
                updated_products += 1

            link = link_by_product_id.get(product.id)
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
                db.flush()
                link_by_product_id[product.id] = link
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
            key = (salon.id, product.id)
            if key not in processed_links:
                processed_links.add(key)
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
