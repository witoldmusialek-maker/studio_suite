#!/usr/bin/env python3
"""
Initial import from legacy FIC files into application-owned DB tables.
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
    LegacyDictionaryEntry,
    LegacyEdServiceRow,
    LegacyEdition1Daily,
    LegacyFicheLine,
    LegacyForfaitTransaction,
    LegacyStat7Row,
    Salon,
    SalonServiceCatalogItem,
    ServiceCatalogItem,
    ServicePriceHistory,
    StaffMember,
    StaffRole,
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


def parse_lookup_table(path: Path) -> Dict[str, Dict[str, str]]:
    _, _, rows = parse_records(path)
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        if len(row) < 2:
            continue
        code = row[0].strip()
        if not code:
            continue
        out[code] = {
            "label": row[1].strip(),
            "extra": row[2].strip() if len(row) > 2 else "",
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
            "total_price": round(sum(item_prices), 2),
        }
    return bundles


def parse_bundle_transactions(forfaits_fic: Path) -> List[Dict[str, object]]:
    _, chunks, rows = parse_records(forfaits_fic)
    out: List[Dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 5 or not row[1].isdigit():
            continue
        out.append(
            {
                "row_index": idx,
                "bundle_code": row[1].zfill(4),
                "bundle_name": row[3].strip(),
                "date_token": row[4] if row[4].isdigit() else "",
                "price": as_double(chunk, 56),
            }
        )
    return out


def parse_workers(personne_fic: Path) -> Dict[str, str]:
    _, _, rows = parse_records(personne_fic)
    out: Dict[str, str] = {}
    for row in rows:
        if len(row) < 4 or not row[0].isdigit():
            continue
        code = row[0].zfill(2)
        display_name = row[3].strip() or f"{row[1].strip()} {row[2].strip()}".strip()
        out[code] = display_name
    return out


def parse_edservice_rows(eds_fic: Path) -> List[Dict[str, object]]:
    _, chunks, rows = parse_records(eds_fic)
    out: List[Dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 2 or not row[0].isdigit() or not row[1].isdigit():
            continue
        out.append(
            {
                "row_index": idx,
                "service_code": row[0].zfill(4),
                "worker_code": row[1].zfill(2),
                "amount": as_double(chunk, 9),
            }
        )
    return out


def parse_fiche_rows(fiche_fic: Path) -> List[Dict[str, object]]:
    _, chunks, rows = parse_records(fiche_fic)
    out: List[Dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 9 or not row[8].isdigit():
            continue
        amount = as_double(chunk, 44)
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


def parse_edition1_rows(path: Path) -> List[Dict[str, object]]:
    _, chunks, rows = parse_records(path)
    out: List[Dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 7:
            continue
        out.append(
            {
                "row_index": idx,
                "period_major": row[0] if len(row) > 0 else "",
                "period_minor": row[1] if len(row) > 1 else "",
                "day_number": row[2] if len(row) > 2 else "",
                "day_name": row[3] if len(row) > 3 else "",
                "date_token": row[5] if len(row) > 5 else "",
                "salon_code": row[6] if len(row) > 6 else "",
                "value_47": as_double(chunk, 47),
                "value_79": as_double(chunk, 79),
                "value_119": as_double(chunk, 119),
                "value_165": as_double(chunk, 165),
                "value_173": as_double(chunk, 173),
                "value_189": as_double(chunk, 189),
            }
        )
    return out


def parse_stat7_rows(path: Path) -> List[Dict[str, object]]:
    _, chunks, rows = parse_records(path)
    out: List[Dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 6:
            continue
        out.append(
            {
                "row_index": idx,
                "date_token_compact": row[0] if len(row) > 0 else "",
                "worker_code": row[1] if len(row) > 1 else "",
                "payment_a": row[2] if len(row) > 2 else "",
                "payment_b": row[3] if len(row) > 3 else "",
                "payment_c": row[4] if len(row) > 4 else "",
                "worker_name": row[5] if len(row) > 5 else "",
                "value_295": as_double(chunk, 295),
                "value_323": as_double(chunk, 323),
                "value_331": as_double(chunk, 331),
                "value_339": as_double(chunk, 339),
                "value_347": as_double(chunk, 347),
            }
        )
    return out


def seed_default_staff_roles(db) -> None:
    roles = [
        ("ADMIN", "Administrator"),
        ("MANAGER", "Manager salonu"),
        ("RECEPTIONIST", "Recepcjonista"),
        ("HAIRDRESSER", "Fryzjer"),
        ("MANICURIST", "Manicurzystka"),
    ]
    for code, name in roles:
        existing = db.query(StaffRole).filter(StaffRole.code == code).first()
        if existing:
            continue
        db.add(StaffRole(code=code, name=name))


def clear_import_scope(db) -> None:
    models = [
        LegacyEdition1Daily,
        LegacyFicheLine,
        LegacyEdServiceRow,
        LegacyForfaitTransaction,
        LegacyStat7Row,
        BundleCatalogItem,
        BundleCatalog,
        ServicePriceHistory,
        ServiceCatalogItem,
        LegacyDictionaryEntry,
        StaffMember,
    ]
    for model in models:
        db.query(model).delete()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import legacy salon data into DB tables.")
    parser.add_argument("--input-dir", required=True, help="Directory with legacy *.FIC files")
    parser.add_argument("--salon-code", default="05")
    parser.add_argument("--salon-name", default="PULAWSKA")
    parser.add_argument("--truncate", action="store_true", help="Clear legacy import scope before import")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        salon = db.query(Salon).filter(Salon.code == args.salon_code).first()
        if salon is None:
            salon = Salon(code=args.salon_code, name=args.salon_name)
            db.add(salon)
            db.flush()

        if args.truncate:
            clear_import_scope(db)

        seed_default_staff_roles(db)

        lookups = {
            "service_types": parse_lookup_table(input_dir / "PTYPSERV.FIC"),
            "families": parse_lookup_table(input_dir / "PFAMILLE.FIC"),
            "groups": parse_lookup_table(input_dir / "REGROUPE.FIC"),
            "esthetic_types": parse_lookup_table(input_dir / "ESTHETIQ.FIC"),
            "vat_codes": parse_lookup_table(input_dir / "TVA.FIC"),
            "client_types": parse_lookup_table(input_dir / "PTYPECL.FIC"),
        }
        for dictionary_name, entries in lookups.items():
            for code, payload in entries.items():
                db.add(
                    LegacyDictionaryEntry(
                        dictionary_name=dictionary_name,
                        code=code,
                        label=payload.get("label", ""),
                        extra=payload.get("extra", ""),
                    )
                )

        worker_by_code = parse_workers(input_dir / "PERSONNE.FIC")
        for code, display_name in worker_by_code.items():
            db.add(
                StaffMember(
                    salon_id=salon.id,
                    legacy_code=code,
                    display_name=display_name,
                    is_active=True,
                )
            )

        service_meta_by_code = parse_service_catalog(input_dir / "SERVICE.FIC")
        service_id_by_code: Dict[str, int] = {}
        for code, meta in sorted(service_meta_by_code.items()):
            item = ServiceCatalogItem(
                legacy_code=code,
                name=str(meta["name"]),
                service_type_code=str(meta["service_type_code"]),
                grouping_code=str(meta["grouping_code"]),
                family_code=str(meta["family_code"]),
                vat_code=str(meta["vat_code"]),
                duration_minutes=int(meta["duration_minutes"]),
                default_price=float(meta["price_regular"]),
                holiday_price=float(meta["price_holiday"]),
            )
            db.add(item)
            db.flush()
            service_id_by_code[code] = item.id
            db.add(
                SalonServiceCatalogItem(
                    salon_id=salon.id,
                    service_id=item.id,
                    is_active=True,
                )
            )
            db.add(
                ServicePriceHistory(
                    service_id=item.id,
                    salon_id=salon.id,
                    price=float(meta["price_regular"]),
                    holiday_price=float(meta["price_holiday"]),
                    source="legacy_import_service_fic",
                )
            )

        bundles = parse_bundle_lines(input_dir / "FORFAIT.FIC")
        for bundle_code, bundle_data in sorted(bundles.items()):
            item_prices = bundle_data.get("item_prices", [])
            service_codes = [code for code in bundle_data["service_codes"] if code in service_id_by_code]
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

        for row in parse_bundle_transactions(input_dir / "FORFAITS.FIC"):
            db.add(
                LegacyForfaitTransaction(
                    row_index=int(row["row_index"]),
                    date_token=str(row["date_token"]),
                    bundle_code=str(row["bundle_code"]),
                    bundle_name=str(row["bundle_name"]),
                    price=float(row["price"]),
                )
            )

        for row in parse_edservice_rows(input_dir / "EDSERVIC.FIC"):
            db.add(
                LegacyEdServiceRow(
                    row_index=int(row["row_index"]),
                    service_code=str(row["service_code"]),
                    worker_code=str(row["worker_code"]),
                    amount=float(row["amount"]),
                )
            )

        for row in parse_fiche_rows(input_dir / "FICHE.FIC"):
            db.add(
                LegacyFicheLine(
                    row_index=int(row["row_index"]),
                    ticket_code=str(row["ticket_code"]),
                    line_code=str(row["line_code"]),
                    date_token=str(row["date_token"]),
                    worker_code=str(row["worker_code"]),
                    service_code=str(row["service_code"]),
                    amount=float(row["amount"]),
                    payment_hint=str(row["payment_hint"]),
                    bundle_code=str(row["bundle_code"]),
                )
            )

        for row in parse_edition1_rows(input_dir / "EDITION1.FIC"):
            db.add(
                LegacyEdition1Daily(
                    row_index=int(row["row_index"]),
                    period_major=str(row["period_major"]),
                    period_minor=str(row["period_minor"]),
                    day_number=str(row["day_number"]),
                    day_name=str(row["day_name"]),
                    date_token=str(row["date_token"]),
                    salon_code=str(row["salon_code"]),
                    value_47=float(row["value_47"]),
                    value_79=float(row["value_79"]),
                    value_119=float(row["value_119"]),
                    value_165=float(row["value_165"]),
                    value_173=float(row["value_173"]),
                    value_189=float(row["value_189"]),
                )
            )

        for row in parse_stat7_rows(input_dir / "STAT7.FIC"):
            db.add(
                LegacyStat7Row(
                    row_index=int(row["row_index"]),
                    date_token_compact=str(row["date_token_compact"]),
                    worker_code=str(row["worker_code"]),
                    payment_a=str(row["payment_a"]),
                    payment_b=str(row["payment_b"]),
                    payment_c=str(row["payment_c"]),
                    worker_name=str(row["worker_name"]),
                    value_295=float(row["value_295"]),
                    value_323=float(row["value_323"]),
                    value_331=float(row["value_331"]),
                    value_339=float(row["value_339"]),
                    value_347=float(row["value_347"]),
                )
            )

        db.commit()

        print("Import finished.")
        print(f"salon={args.salon_code} workers={len(worker_by_code)} services={len(service_meta_by_code)}")
        print(f"bundles={len(bundles)}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
