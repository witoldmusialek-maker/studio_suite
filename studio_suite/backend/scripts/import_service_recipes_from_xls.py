from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import func

from app.database import SessionLocal
from app.models.salon_core import LegacyProductCatalogItem, ServiceCatalogItem, ServiceRecipeItem


@dataclass
class RecipeCandidate:
    service_code_raw: str
    service_code_norm: str
    service_name: str
    product_family: str
    product_label: str
    quantity: Decimal
    package_unit_count: Decimal | None
    package_size_value: Decimal | None
    package_size_unit: str | None


def _norm_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", text)


def _norm_service_code(value: object) -> str | None:
    text = _norm_text(value)
    if not text:
        return None
    if not re.fullmatch(r"\d+(?:\.0+)?", text):
        return None
    number = int(float(text))
    return f"{number:04d}"


def _parse_decimal(value: object) -> Decimal | None:
    text = _norm_text(value).replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _parse_package_size(raw: str) -> tuple[Decimal | None, str | None]:
    text = raw.strip().lower()
    if not text:
        return None, None
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(ml|g|gr|kg|l|j|szt)", text)
    if not match:
        return None, None
    value = _parse_decimal(match.group(1))
    unit = match.group(2).upper()
    if unit == "GR":
        unit = "G"
    return value, unit


def _normalize_family(raw: str) -> str:
    family = _norm_text(raw).upper()
    family = family.replace("Ę", "E").replace("Ó", "O").replace("Ł", "L").replace("Ś", "S").replace("Ż", "Z").replace("Ź", "Z").replace("Ć", "C").replace("Ń", "N").replace("Ą", "A")
    return family or "INNE"


def _norm_key(raw: str) -> str:
    text = _norm_text(raw).lower()
    text = text.replace("+", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _resolve_product_id(label: str, exact: dict[str, int], norm_exact: dict[str, int], norm_candidates: list[tuple[int, str]]) -> int | None:
    key = label.strip().lower()
    if key in exact:
        return exact[key]
    norm = _norm_key(label)
    if norm in norm_exact:
        return norm_exact[norm]
    # Safe fuzzy fallback: unique "contains" hit only.
    hits = [pid for pid, candidate in norm_candidates if norm and (norm in candidate or candidate in norm)]
    if len(set(hits)) == 1:
        return hits[0]
    return None


def _iter_candidates(xls_path: Path, sheet_names: Iterable[str]) -> list[RecipeCandidate]:
    output: list[RecipeCandidate] = []
    for sheet in sheet_names:
        df = pd.read_excel(xls_path, sheet_name=sheet, header=None)
        header_idx = None
        for idx in range(min(40, len(df))):
            row_txt = " | ".join(_norm_text(v) for v in df.iloc[idx].tolist())
            if "kod usługi" in row_txt.lower() or "kod uslugi" in row_txt.lower():
                header_idx = idx
                break
        if header_idx is None:
            continue

        data = df.iloc[header_idx + 1 :].copy()
        data.columns = [_norm_text(v) for v in df.iloc[header_idx].tolist()]

        code_col = "kod usługi według fiszki"
        if code_col not in data.columns:
            code_col = "kod uslugi według fiszki"
        if code_col not in data.columns:
            code_col = "kod uslugi wedlug fiszki"
        if code_col not in data.columns:
            continue

        for _, row in data.iterrows():
            service_code = _norm_service_code(row.get(code_col))
            if not service_code:
                continue
            product_label = _norm_text(row.get("nazwa produktu"))
            if not product_label:
                continue
            quantity = _parse_decimal(row.get("ilość jednostek do receptury")) or Decimal("0")
            package_clients = _parse_decimal(row.get("ilość klientów z opakowania"))
            package_size_raw = _norm_text(row.get("pojemność opak."))
            package_size_value, package_size_unit = _parse_package_size(package_size_raw)
            family = _normalize_family(_norm_text(row.get("rodzina")))
            output.append(
                RecipeCandidate(
                    service_code_raw=str(int(service_code)),
                    service_code_norm=service_code,
                    service_name=_norm_text(row.get("nazwa usługi")),
                    product_family=family,
                    product_label=product_label,
                    quantity=quantity,
                    package_unit_count=package_clients,
                    package_size_value=package_size_value,
                    package_size_unit=package_size_unit,
                )
            )
    return output


def _coalesce_candidates(candidates: list[RecipeCandidate]) -> list[RecipeCandidate]:
    grouped: dict[tuple[str, str, str], list[RecipeCandidate]] = defaultdict(list)
    for item in candidates:
        key = (item.service_code_norm, item.product_family, item.product_label.lower(), item.service_name.lower())
        grouped[key].append(item)

    merged: list[RecipeCandidate] = []
    for _, rows in grouped.items():
        sample = rows[0]
        qty_mode = Counter([r.quantity for r in rows]).most_common(1)[0][0]
        package_count = Counter([r.package_unit_count for r in rows if r.package_unit_count is not None]).most_common(1)
        package_value = Counter([r.package_size_value for r in rows if r.package_size_value is not None]).most_common(1)
        package_unit = Counter([r.package_size_unit for r in rows if r.package_size_unit]).most_common(1)
        merged.append(
            RecipeCandidate(
                service_code_raw=sample.service_code_raw,
                service_code_norm=sample.service_code_norm,
                service_name=sample.service_name,
                product_family=sample.product_family,
                product_label=sample.product_label,
                quantity=qty_mode,
                package_unit_count=package_count[0][0] if package_count else None,
                package_size_value=package_value[0][0] if package_value else None,
                package_size_unit=package_unit[0][0] if package_unit else None,
            )
        )
    return sorted(merged, key=lambda r: (r.service_code_norm, r.service_name.lower(), r.product_family, r.product_label.lower()))


def _norm_service_name(raw: str) -> str:
    text = _norm_key(raw)
    text = text.replace("wlosy", "wl")
    text = text.replace("włosy", "wl")
    text = text.replace("srednie", "sr")
    text = text.replace("srednnie", "sr")
    text = text.replace("dlugie", "dl")
    text = text.replace("krotkie", "kr")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _service_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    ratio = SequenceMatcher(None, left, right).ratio()
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    token_score = len(left_tokens.intersection(right_tokens)) / max(1, len(left_tokens.union(right_tokens)))
    return ratio * 0.75 + token_score * 0.25


def run_import(xls_path: Path, apply: bool) -> None:
    db = SessionLocal()
    try:
        excel = pd.ExcelFile(xls_path)
        sheet_names = [s for s in excel.sheet_names if "kalkulacja" in s.lower()]
        parsed = _iter_candidates(xls_path, sheet_names)
        candidates = _coalesce_candidates(parsed)
        source_services: dict[str, str] = {}
        for row in candidates:
            source_services.setdefault(row.service_code_norm, row.service_name)

        all_services = db.query(ServiceCatalogItem).all()
        service_map: dict[str, ServiceCatalogItem] = {}
        mapping_debug: list[tuple[str, str, str, str, float]] = []
        for source_code, source_name in sorted(source_services.items()):
            src_norm = _norm_service_name(source_name)
            src_num = int(source_code)
            best: ServiceCatalogItem | None = None
            best_score = 0.0
            for target in all_services:
                target_norm = _norm_service_name(target.name)
                sim = _service_similarity(src_norm, target_norm)
                if sim <= 0:
                    continue
                target_num = int(target.legacy_code) if target.legacy_code.isdigit() else 0
                code_penalty = min(abs(target_num - src_num), 400) / 4000.0
                score = sim - code_penalty
                if target_num >= 1000:
                    score -= 0.05
                if best is None or score > best_score:
                    best = target
                    best_score = score
            if best is not None and best_score >= 0.42:
                service_map[source_code] = best
                mapping_debug.append((source_code, source_name, best.legacy_code, best.name, round(best_score, 4)))

        mapped_codes = sorted(service_map.keys())

        products = db.query(LegacyProductCatalogItem.id, LegacyProductCatalogItem.name, LegacyProductCatalogItem.name_pl).all()
        product_exact: dict[str, int] = {}
        product_norm_exact: dict[str, int] = {}
        product_norm_candidates: list[tuple[int, str]] = []
        for pid, name, name_pl in products:
            if name:
                name_str = str(name).strip()
                product_exact[name_str.lower()] = pid
                norm = _norm_key(name_str)
                if norm:
                    product_norm_exact.setdefault(norm, pid)
                    product_norm_candidates.append((pid, norm))
            if name_pl:
                name_pl_str = str(name_pl).strip()
                product_exact[name_pl_str.lower()] = pid
                norm = _norm_key(name_pl_str)
                if norm:
                    product_norm_exact.setdefault(norm, pid)
                    product_norm_candidates.append((pid, norm))

        by_service: dict[str, list[RecipeCandidate]] = defaultdict(list)
        for row in candidates:
            by_service[row.service_code_norm].append(row)

        total_lines = 0
        matched_services = 0
        unmatched_services = []
        unresolved_products = 0

        for service_code, rows in by_service.items():
            service = service_map.get(service_code)
            if not service:
                unmatched_services.append(service_code)
                continue
            matched_services += 1
            total_lines += len(rows)
            for row in rows:
                if _resolve_product_id(row.product_label, product_exact, product_norm_exact, product_norm_candidates) is None:
                    unresolved_products += 1

        print(f"xls={xls_path}")
        print(f"sheets={len(sheet_names)} parsed_rows={len(parsed)} unique_recipe_rows={len(candidates)}")
        print(f"services_total={len(source_services)} services_matched={matched_services} services_unmatched={len(unmatched_services)}")
        if unmatched_services:
            print("unmatched_service_codes=", ",".join(unmatched_services[:40]))
        print(f"import_lines={total_lines} unresolved_product_labels={unresolved_products}")
        print("service_mapping_preview:")
        for src_code, src_name, dst_code, dst_name, score in mapping_debug[:60]:
            print(f"  {src_code} '{src_name}' -> {dst_code} '{dst_name}' score={score}")

        if not apply:
            print("dry_run_only=true (use --apply to write)")
            return

        db.query(ServiceRecipeItem).filter(ServiceRecipeItem.note == f"import_xls:{xls_path.name}").delete(synchronize_session=False)

        updated_services = 0
        inserted_lines = 0
        for service_code, rows in by_service.items():
            service = service_map.get(service_code)
            if not service:
                continue
            db.query(ServiceRecipeItem).filter(ServiceRecipeItem.service_id == service.id).delete(synchronize_session=False)
            position = 1
            for row in rows:
                product_id = _resolve_product_id(row.product_label, product_exact, product_norm_exact, product_norm_candidates)
                item = ServiceRecipeItem(
                    service_id=service.id,
                    variant_code=None,
                    position=position,
                    product_family=row.product_family,
                    product_id=product_id,
                    product_label_snapshot=row.product_label,
                    is_optional=False,
                    is_required=True,
                    quantity_mode="EXACT",
                    planned_quantity=row.quantity,
                    planned_min=None,
                    planned_default=row.quantity,
                    planned_max=None,
                    unit="PCS",
                    recipe_unit_label="DOZA",
                    package_unit_count=row.package_unit_count,
                    package_unit_label="KLIENCI",
                    package_size_value=row.package_size_value,
                    package_size_unit=row.package_size_unit,
                    inventory_mode="PER_SERVICE",
                    note=f"import_xls:{xls_path.name}",
                )
                db.add(item)
                position += 1
                inserted_lines += 1
            updated_services += 1
        db.commit()
        print(f"apply=true updated_services={updated_services} inserted_lines={inserted_lines}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import service recipes from legacy XLS (kalkulacja pakietow).")
    parser.add_argument("--file", required=True, help="Path to .xls file")
    parser.add_argument("--apply", action="store_true", help="Write to DB (without this flag: dry run)")
    args = parser.parse_args()
    run_import(Path(args.file), apply=args.apply)


if __name__ == "__main__":
    main()
