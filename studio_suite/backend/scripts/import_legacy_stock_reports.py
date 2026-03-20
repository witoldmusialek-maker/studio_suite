from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import py7zr

from app.database import SessionLocal
from app.models.salon_core import (
    InventoryIssue,
    InventoryIssueLine,
    LegacyProductCatalogItem,
    LegacyStockReportBatch,
    LegacyStockReportFile,
    LegacyStockReportRow,
    Salon,
    StockLevel,
    StockLocation,
)


@dataclass
class ParsedFileMeta:
    report_type: str
    salon_label: str | None
    report_year: int | None
    report_month: int | None
    report_generated_at: datetime | None


def _normalize_text(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", text)


def _slug(value: str) -> str:
    if not value:
        return ""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.lower())


def _to_decimal(value: object) -> Decimal | None:
    text = _normalize_text(value).replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _to_int(value: object) -> int | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        return int(float(text))
    except Exception:
        return None


def _map_salon_id(salons: list[Salon], salon_label: str | None) -> int | None:
    if not salon_label:
        return None
    label = salon_label.lower()
    label_slug = _slug(salon_label)
    for salon in salons:
        code = (salon.code or "").strip()
        name = (salon.name or "").strip()
        name_slug = _slug(name)
        if name and (name.lower() in label or label in name.lower()):
            return salon.id
        if name_slug and (name_slug in label_slug or label_slug in name_slug):
            return salon.id
        if code and code in label:
            return salon.id
    if "pulaw" in label_slug:
        return next((s.id for s in salons if "pulaw" in _slug(s.name)), None)
    if "kras" in label_slug:
        return next((s.id for s in salons if "kras" in _slug(s.name)), None)
    if "odyn" in label_slug:
        return next((s.id for s in salons if "odyn" in _slug(s.name)), None)
    return None


def _normalize_headers(columns: list[object]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for raw in columns:
        source = _normalize_text(raw)
        if not source:
            continue
        key = source.lower()
        key = (
            key.replace("ł", "l")
            .replace("ó", "o")
            .replace("ą", "a")
            .replace("ś", "s")
            .replace("ż", "z")
            .replace("ź", "z")
            .replace("ć", "c")
            .replace("ń", "n")
            .replace("ę", "e")
        )
        key = re.sub(r"\s+", " ", key)
        mapped[key] = source
    return mapped


def _parse_file_meta(file_name: str) -> ParsedFileMeta:
    lower_name = file_name.lower()
    if lower_name.startswith("rem_table"):
        # rem_table2026_2_2026_03_01-10_24_21_Puławska.xls
        match = re.match(
            r"^rem_table(?P<year>\d{4})_(?P<month>\d{1,2})_(?P<dt>\d{4}_\d{2}_\d{2}-\d{2}_\d{2}_\d{2})_(?P<salon>.+)\.xls$",
            file_name,
            flags=re.IGNORECASE,
        )
        if match:
            dt = datetime.strptime(match.group("dt"), "%Y_%m_%d-%H_%M_%S")
            return ParsedFileMeta(
                report_type="rem_table",
                salon_label=match.group("salon"),
                report_year=int(match.group("year")),
                report_month=int(match.group("month")),
                report_generated_at=dt,
            )
        return ParsedFileMeta("rem_table", None, None, None, None)
    if lower_name.startswith("stan_balance") and lower_name.endswith(".xls"):
        # stan_balancePuławska02_03_2026_23_00.xls
        match = re.match(
            r"^stan_balance(?P<salon>.+?)(?P<dd>\d{2})_(?P<mm>\d{2})_(?P<yyyy>\d{4})_(?P<hh>\d{2})_(?P<mi>\d{2})\.xls$",
            file_name,
            flags=re.IGNORECASE,
        )
        if match:
            dt = datetime.strptime(
                f"{match.group('yyyy')}-{match.group('mm')}-{match.group('dd')} {match.group('hh')}:{match.group('mi')}",
                "%Y-%m-%d %H:%M",
            )
            return ParsedFileMeta(
                report_type="stan_balance",
                salon_label=match.group("salon"),
                report_year=int(match.group("yyyy")),
                report_month=int(match.group("mm")),
                report_generated_at=dt,
            )
        return ParsedFileMeta("stan_balance", None, None, None, None)
    return ParsedFileMeta("other", None, None, None, None)


def _parse_rem_table(df: pd.DataFrame) -> list[dict[str, object]]:
    colmap = _normalize_headers(list(df.columns))
    id_col = colmap.get("idprod")
    if id_col is None:
        return []
    out: list[dict[str, object]] = []
    for idx, row in df.iterrows():
        product_code = _normalize_text(row.get(id_col))
        if not product_code:
            continue
        out.append(
            {
                "row_index": int(idx) + 1,
                "product_code": product_code,
                "product_name_pl": _normalize_text(row.get(colmap.get("nazwapl", ""))),
                "product_name": _normalize_text(row.get(colmap.get("nazwa1", ""))),
                "family_code": _normalize_text(row.get(colmap.get("rodzina", ""))),
                "package_label": _normalize_text(row.get(colmap.get("poj", ""))),
                "catalog_price": _to_decimal(row.get(colmap.get("cenakat", ""))),
                "sale_price_gross": _to_decimal(row.get(colmap.get("cenaspbrt", ""))),
                "unit_count": _to_decimal(row.get(colmap.get("il_jedn", ""))),
                "counted_units_pcs": _to_decimal(row.get(colmap.get("szt", ""))),
                "counted_units_dose": _to_decimal(row.get(colmap.get("jedn", ""))),
                "counted_weight_gross": _to_decimal(row.get(colmap.get("waga", ""))),
                "counted_packages": _to_decimal(row.get(colmap.get("il_op", ""))),
                "raw_payload": {k: _normalize_text(v) for k, v in row.to_dict().items()},
            }
        )
    return out


def _parse_balance_table(df: pd.DataFrame) -> list[dict[str, object]]:
    colmap = _normalize_headers(list(df.columns))
    id_col = colmap.get("id p") or colmap.get("id_p")
    if id_col is None:
        return []
    out: list[dict[str, object]] = []
    for idx, row in df.iterrows():
        product_code = _normalize_text(row.get(id_col))
        if not product_code:
            continue
        out.append(
            {
                "row_index": int(idx) + 1,
                "product_code": product_code,
                "product_name_pl": _normalize_text(row.get(colmap.get("nazwapl", ""))),
                "unit_count": _to_decimal(row.get(colmap.get("jednostek w szt.", ""))),
                "balance_open": _to_decimal(row.get(colmap.get("stan na poczatku okresu", ""))),
                "balance_pz": _to_decimal(row.get(colmap.get("pz", ""))),
                "balance_wz_rw": _to_decimal(row.get(colmap.get("wz", ""))),
                "balance_adjustment": _to_decimal(row.get(colmap.get("rwn", ""))),
                "balance_close": _to_decimal(row.get(colmap.get("stan na koniec okresu", ""))),
                "raw_payload": {k: _normalize_text(v) for k, v in row.to_dict().items()},
            }
        )
    return out


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def run_import(archive_path: Path, tenant_id: int, notes: str | None = None) -> dict[str, Any]:
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    archive_hash = _sha256(archive_path)
    archive_size = archive_path.stat().st_size

    with tempfile.TemporaryDirectory(prefix="legacy_stock_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            archive.extractall(path=tmp_path)

        all_files = sorted([p for p in tmp_path.iterdir() if p.is_file()])
        xls_files = [p for p in all_files if p.suffix.lower() == ".xls"]
        pdf_files = [p for p in all_files if p.suffix.lower() == ".pdf"]

        with SessionLocal() as db:
            salons = db.query(Salon).all()
            product_by_code = {
                (row.legacy_code or "").strip().lower(): row.id
                for row in db.query(LegacyProductCatalogItem.id, LegacyProductCatalogItem.legacy_code).all()
                if row.legacy_code
            }

            batch = LegacyStockReportBatch(
                tenant_id=tenant_id,
                source_archive_path=str(archive_path.resolve()),
                source_archive_name=archive_path.name,
                source_archive_sha256=archive_hash,
                source_archive_size_bytes=archive_size,
                notes=notes,
            )
            db.add(batch)
            db.flush()

            imported_rows = 0
            mapped_rows = 0
            parse_errors = 0

            for file_path in all_files:
                meta = _parse_file_meta(file_path.name)
                salon_id = _map_salon_id(salons, meta.salon_label)
                report_file = LegacyStockReportFile(
                    batch_id=batch.id,
                    tenant_id=tenant_id,
                    salon_id=salon_id,
                    salon_label=meta.salon_label,
                    file_name=file_path.name,
                    file_ext=file_path.suffix.lower().lstrip("."),
                    report_type=meta.report_type if file_path.suffix.lower() == ".xls" else "pdf_report",
                    report_year=meta.report_year,
                    report_month=meta.report_month,
                    report_generated_at=meta.report_generated_at,
                    row_count=0,
                    parse_status="pending",
                    file_size_bytes=file_path.stat().st_size,
                )
                db.add(report_file)
                db.flush()

                if file_path.suffix.lower() != ".xls":
                    report_file.parse_status = "stored"
                    continue

                try:
                    df = pd.read_excel(file_path, engine="xlrd")
                    if meta.report_type == "rem_table":
                        parsed_rows = _parse_rem_table(df)
                    elif meta.report_type == "stan_balance":
                        parsed_rows = _parse_balance_table(df)
                    else:
                        parsed_rows = []

                    for parsed in parsed_rows:
                        code = str(parsed.get("product_code") or "").strip().lower()
                        mapped_product_id = product_by_code.get(code)
                        if mapped_product_id is not None:
                            mapped_rows += 1
                        db.add(
                            LegacyStockReportRow(
                                report_file_id=report_file.id,
                                tenant_id=tenant_id,
                                salon_id=salon_id,
                                row_index=int(parsed.get("row_index") or 0),
                                product_code=str(parsed.get("product_code") or "") or None,
                                product_name_pl=str(parsed.get("product_name_pl") or "") or None,
                                product_name=str(parsed.get("product_name") or "") or None,
                                family_code=str(parsed.get("family_code") or "") or None,
                                package_label=str(parsed.get("package_label") or "") or None,
                                catalog_price=parsed.get("catalog_price"),
                                sale_price_gross=parsed.get("sale_price_gross"),
                                unit_count=parsed.get("unit_count"),
                                counted_units_pcs=parsed.get("counted_units_pcs"),
                                counted_units_dose=parsed.get("counted_units_dose"),
                                counted_weight_gross=parsed.get("counted_weight_gross"),
                                counted_packages=parsed.get("counted_packages"),
                                balance_open=parsed.get("balance_open"),
                                balance_pz=parsed.get("balance_pz"),
                                balance_wz_rw=parsed.get("balance_wz_rw"),
                                balance_adjustment=parsed.get("balance_adjustment"),
                                balance_close=parsed.get("balance_close"),
                                raw_payload=json.dumps(parsed.get("raw_payload", {}), ensure_ascii=False),
                                mapped_product_id=mapped_product_id,
                                mapping_confidence=Decimal("1.0") if mapped_product_id is not None else None,
                            )
                        )
                    report_file.row_count = len(parsed_rows)
                    report_file.parse_status = "parsed"
                    imported_rows += len(parsed_rows)
                except Exception as exc:
                    parse_errors += 1
                    report_file.parse_status = "error"
                    report_file.parse_error = str(exc)[:5000]

            db.commit()

            stats = {
                "archive": str(archive_path),
                "batch_id": batch.id,
                "files_total": len(all_files),
                "xls_files": len(xls_files),
                "pdf_files": len(pdf_files),
                "rows_imported": imported_rows,
                "rows_mapped_product": mapped_rows,
                "rows_unmapped_product": max(imported_rows - mapped_rows, 0),
                "mapping_coverage": float((mapped_rows / imported_rows * 100)) if imported_rows else 0.0,
                "parse_errors": parse_errors,
            }
            return stats


def _is_weight_product(product: LegacyProductCatalogItem) -> bool:
    dose_weight = Decimal(str(product.min_unit or 0))
    has_weight_profile = product.weight is not None or product.package_weight is not None
    return dose_weight > Decimal("0") and has_weight_profile


def _resolve_counted_quantity(
    row: LegacyStockReportRow,
    product: LegacyProductCatalogItem,
) -> Decimal | None:
    if _is_weight_product(product):
        if row.counted_units_dose is not None:
            return Decimal(str(row.counted_units_dose))
        if row.counted_weight_gross is not None:
            gross = Decimal(str(row.counted_weight_gross))
            tare = Decimal(str(product.package_weight or 0))
            dose_weight = Decimal(str(product.min_unit or 0))
            if dose_weight > Decimal("0"):
                net = gross - tare
                if net < Decimal("0"):
                    net = Decimal("0")
                return net / dose_weight
        if row.counted_packages is not None and row.unit_count is not None:
            return Decimal(str(row.counted_packages)) * Decimal(str(row.unit_count))
        return None

    if row.counted_units_pcs is not None:
        return Decimal(str(row.counted_units_pcs))
    if row.counted_packages is not None:
        return Decimal(str(row.counted_packages))
    if row.counted_units_dose is not None:
        return Decimal(str(row.counted_units_dose))
    return None


def _get_or_create_stock_level(db, stock_location_id: int, product_id: int) -> StockLevel:
    level = (
        db.query(StockLevel)
        .filter(
            StockLevel.stock_location_id == stock_location_id,
            StockLevel.product_id == product_id,
        )
        .first()
    )
    if level:
        return level
    level = StockLevel(
        stock_location_id=stock_location_id,
        product_id=product_id,
        quantity=Decimal("0"),
    )
    db.add(level)
    db.flush()
    return level


def _get_or_create_default_location(db, tenant_id: int, salon_id: int) -> StockLocation:
    location = (
        db.query(StockLocation)
        .filter(
            StockLocation.tenant_id == tenant_id,
            StockLocation.salon_id == salon_id,
            StockLocation.code == "SALON_GLOWNY",
        )
        .first()
    )
    if location is None:
        location = (
            db.query(StockLocation)
            .filter(
                StockLocation.tenant_id == tenant_id,
                StockLocation.salon_id == salon_id,
                StockLocation.is_active.is_(True),
            )
            .order_by(StockLocation.id.asc())
            .first()
        )
    if location is None:
        location = StockLocation(
            tenant_id=tenant_id,
            salon_id=salon_id,
            code="SALON_GLOWNY",
            name="Salon główny",
            location_type="MIXED",
            is_active=True,
        )
        db.add(location)
        db.flush()
    return location


def apply_stock_levels_from_latest_rem_table(
    batch_id: int,
    tenant_id: int,
    remarks_prefix: str = "Legacy rem_table import",
) -> dict[str, Any]:
    with SessionLocal() as db:
        rem_files = (
            db.query(LegacyStockReportFile)
            .filter(
                LegacyStockReportFile.batch_id == batch_id,
                LegacyStockReportFile.tenant_id == tenant_id,
                LegacyStockReportFile.report_type == "rem_table",
                LegacyStockReportFile.parse_status == "parsed",
                LegacyStockReportFile.salon_id.isnot(None),
            )
            .order_by(
                LegacyStockReportFile.salon_id.asc(),
                LegacyStockReportFile.report_generated_at.desc().nullslast(),
                LegacyStockReportFile.id.desc(),
            )
            .all()
        )

        latest_per_salon: dict[int, LegacyStockReportFile] = {}
        for report_file in rem_files:
            if report_file.salon_id not in latest_per_salon:
                latest_per_salon[report_file.salon_id] = report_file

        result: dict[str, Any] = {
            "batch_id": batch_id,
            "salons_total": len(latest_per_salon),
            "salons_applied": 0,
            "levels_updated": 0,
            "lines_created": 0,
            "issues_created": 0,
            "salons": [],
        }

        if not latest_per_salon:
            return result

        product_by_id = {
            row.id: row
            for row in db.query(LegacyProductCatalogItem).all()
        }

        for salon_id, report_file in latest_per_salon.items():
            location = _get_or_create_default_location(db, tenant_id, salon_id)

            rows = (
                db.query(LegacyStockReportRow)
                .filter(
                    LegacyStockReportRow.report_file_id == report_file.id,
                    LegacyStockReportRow.mapped_product_id.isnot(None),
                )
                .all()
            )
            if not rows:
                result["salons"].append(
                    {
                        "salon_id": salon_id,
                        "report_file_id": report_file.id,
                        "status": "skipped_no_rows",
                    }
                )
                continue

            issue = InventoryIssue(
                tenant_id=tenant_id,
                salon_id=salon_id,
                stock_location_id=location.id,
                appointment_id=None,
                service_id=None,
                performed_line_id=None,
                staff_id=None,
                issue_time=datetime.utcnow(),
                status="POSTED",
                remarks=f"{remarks_prefix}: {report_file.file_name}",
            )
            db.add(issue)
            db.flush()

            salon_levels_updated = 0
            salon_lines = 0
            for row in rows:
                if row.mapped_product_id is None:
                    continue
                product = product_by_id.get(row.mapped_product_id)
                if product is None:
                    continue
                counted = _resolve_counted_quantity(row, product)
                if counted is None:
                    continue
                if counted < Decimal("0"):
                    counted = Decimal("0")

                level = _get_or_create_stock_level(db, location.id, row.mapped_product_id)
                before = Decimal(str(level.quantity or 0))
                delta = counted - before
                level.quantity = counted
                salon_levels_updated += 1
                if delta != Decimal("0"):
                    db.add(
                        InventoryIssueLine(
                            inventory_issue_id=issue.id,
                            appointment_id=None,
                            service_id=None,
                            performed_line_id=None,
                            product_id=row.mapped_product_id,
                            quantity_planned=before,
                            quantity_actual=delta,
                            unit="DOSE" if _is_weight_product(product) else "PCS",
                            unit_cost=Decimal("0"),
                            total_cost=Decimal("0"),
                        )
                    )
                    salon_lines += 1

            if salon_lines == 0:
                db.delete(issue)
                status = "applied_no_delta"
            else:
                result["issues_created"] += 1
                result["lines_created"] += salon_lines
                status = "applied"

            result["salons"].append(
                {
                    "salon_id": salon_id,
                    "report_file_id": report_file.id,
                    "stock_location_id": location.id,
                    "rows_considered": len(rows),
                    "levels_updated": salon_levels_updated,
                    "delta_lines_created": salon_lines,
                    "status": status,
                }
            )
            result["salons_applied"] += 1
            result["levels_updated"] += salon_levels_updated

        db.commit()
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Import legacy stock report archive (7z with XLS/PDF) into staging tables.")
    parser.add_argument("--archive", required=True, help="Path to archive .7z")
    parser.add_argument("--tenant-id", type=int, default=1, help="Tenant ID (default: 1)")
    parser.add_argument("--notes", default=None, help="Optional import notes")
    parser.add_argument(
        "--apply-stock-levels",
        action="store_true",
        help="After import, update stock levels from latest rem_table per salon (same batch).",
    )
    args = parser.parse_args()

    stats = run_import(Path(args.archive), tenant_id=args.tenant_id, notes=args.notes)
    print(f"archive={stats['archive']}")
    print(f"batch_id={stats['batch_id']}")
    print(f"files_total={stats['files_total']} xls={stats['xls_files']} pdf={stats['pdf_files']}")
    print(f"rows_imported={stats['rows_imported']}")
    print(f"rows_mapped_product={stats['rows_mapped_product']}")
    print(f"rows_unmapped_product={stats['rows_unmapped_product']}")
    print(f"mapping_coverage={stats['mapping_coverage']:.2f}%")
    print(f"parse_errors={stats['parse_errors']}")

    if args.apply_stock_levels:
        apply_stats = apply_stock_levels_from_latest_rem_table(
            batch_id=int(stats["batch_id"]),
            tenant_id=args.tenant_id,
        )
        print(
            "stock_apply="
            f"salons_total:{apply_stats['salons_total']} "
            f"salons_applied:{apply_stats['salons_applied']} "
            f"levels_updated:{apply_stats['levels_updated']} "
            f"issues_created:{apply_stats['issues_created']} "
            f"lines_created:{apply_stats['lines_created']}"
        )


if __name__ == "__main__":
    main()
