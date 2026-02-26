#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass
class ParsedTable:
    name: str
    rec_len: int
    rows: List[List[str]]


def parse_table(path: Path) -> ParsedTable:
    data = path.read_bytes()
    rec_len = int(data[7:11].decode("ascii"))
    offset = rec_len
    total = max(0, (len(data) - offset) // rec_len)
    rows: List[List[str]] = []
    for i in range(total):
        chunk = data[offset + i * rec_len : offset + (i + 1) * rec_len]
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        rows.append(parts)
    return ParsedTable(name=path.name, rec_len=rec_len, rows=rows)


def normalize_ascii(text: str) -> str:
    return text.encode("ascii", "replace").decode()


def write_csv(path: Path, fieldnames: List[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def extract_clients(table: ParsedTable, output_dir: Path) -> None:
    max_cols = max((len(r) for r in table.rows), default=0)
    fieldnames = ["row_index"] + [f"f{i:02d}" for i in range(max_cols)]
    raw_rows = []
    for idx, row in enumerate(table.rows):
        item = {"row_index": idx}
        for i, value in enumerate(row):
            item[f"f{i:02d}"] = normalize_ascii(value)
        raw_rows.append(item)
    write_csv(output_dir / "clients_raw.csv", fieldnames, raw_rows)

    candidates = []
    for idx, row in enumerate(table.rows):
        if len(row) < 3:
            continue
        maybe_date = next((token for token in row if re.fullmatch(r"\d{8}", token)), "")
        service_codes = [token for token in row if re.fullmatch(r"\d{4}", token)]
        candidates.append(
            {
                "row_index": idx,
                "label_1": normalize_ascii(row[0]),
                "label_2": normalize_ascii(row[1]) if len(row) > 1 else "",
                "gender": row[2] if len(row) > 2 and row[2] in {"F", "M"} else "",
                "date_token": maybe_date,
                "service_code_count": len(service_codes),
                "service_codes_sample": ";".join(service_codes[:12]),
            }
        )
    write_csv(
        output_dir / "clients_candidates.csv",
        ["row_index", "label_1", "label_2", "gender", "date_token", "service_code_count", "service_codes_sample"],
        candidates,
    )


def extract_staff(table: ParsedTable, output_dir: Path) -> None:
    rows = []
    for idx, row in enumerate(table.rows):
        code = row[0] if row else ""
        first = row[1] if len(row) > 1 else ""
        second = row[2] if len(row) > 2 else ""
        full = row[3] if len(row) > 3 else ""
        category = row[4] if len(row) > 4 else ""
        letters = re.compile(r"[A-Za-zÀ-ÿ]")
        has_person_shape = bool(letters.search(first)) and bool(letters.search(second)) and len(first) < 40
        looks_keyword = any(
            kw in f"{first} {second} {full}".upper()
            for kw in ["SPRZEDA", "KARTA", "VIP", "OLAPLEX", "DOPLATA", "PROM", "GRATIS"]
        )
        rows.append(
            {
                "row_index": idx,
                "code": code,
                "first_label": normalize_ascii(first),
                "second_label": normalize_ascii(second),
                "full_label": normalize_ascii(full),
                "category_token": category,
                "is_probable_employee": "yes" if has_person_shape and not looks_keyword else "no",
            }
        )
    write_csv(
        output_dir / "staff_candidates.csv",
        ["row_index", "code", "first_label", "second_label", "full_label", "category_token", "is_probable_employee"],
        rows,
    )


def extract_visit_lines(table: ParsedTable, output_dir: Path) -> None:
    rows = []
    for idx, row in enumerate(table.rows):
        rows.append(
            {
                "row_index": idx,
                "ticket_code": row[0] if len(row) > 0 else "",
                "line_code": row[1] if len(row) > 1 else "",
                "channel_code": row[2] if len(row) > 2 else "",
                "kind_flag": row[3] if len(row) > 3 else "",
                "date_token": row[4] if len(row) > 4 else "",
                "worker_code": row[5] if len(row) > 5 else "",
                "qty_token": row[6] if len(row) > 6 else "",
                "state_flag": row[7] if len(row) > 7 else "",
                "service_code": row[8] if len(row) > 8 else "",
                "meta_1": row[9] if len(row) > 9 else "",
                "meta_2": row[10] if len(row) > 10 else "",
                "group_code": row[11] if len(row) > 11 else "",
                "price_token_raw": normalize_ascii(row[12]) if len(row) > 12 else "",
            }
        )
    write_csv(
        output_dir / "visit_lines.csv",
        [
            "row_index",
            "ticket_code",
            "line_code",
            "channel_code",
            "kind_flag",
            "date_token",
            "worker_code",
            "qty_token",
            "state_flag",
            "service_code",
            "meta_1",
            "meta_2",
            "group_code",
            "price_token_raw",
        ],
        rows,
    )


def extract_history(table: ParsedTable, output_dir: Path) -> None:
    rows = []
    for idx, row in enumerate(table.rows):
        texts = [normalize_ascii(token) for token in row[3:25] if token and not re.fullmatch(r"[\d@?'. ]+", token)]
        rows.append(
            {
                "row_index": idx,
                "surname": normalize_ascii(row[0]) if len(row) > 0 else "",
                "name": normalize_ascii(row[1]) if len(row) > 1 else "",
                "birth_or_ref": row[2] if len(row) > 2 else "",
                "text_events_count": len(texts),
                "text_events_sample": " | ".join(texts[:6]),
            }
        )
    write_csv(
        output_dir / "history_cards.csv",
        ["row_index", "surname", "name", "birth_or_ref", "text_events_count", "text_events_sample"],
        rows,
    )


def extract_products(table: ParsedTable, output_dir: Path) -> None:
    rows = []
    for idx, row in enumerate(table.rows):
        rows.append(
            {
                "row_index": idx,
                "product_code": row[0] if len(row) > 0 else "",
                "type_code": row[1] if len(row) > 1 else "",
                "name": normalize_ascii(row[2]) if len(row) > 2 else "",
                "family_code": row[3] if len(row) > 3 else "",
                "brand_1": normalize_ascii(row[6]) if len(row) > 6 else "",
                "brand_2": normalize_ascii(row[8]) if len(row) > 8 else "",
            }
        )
    write_csv(
        output_dir / "products.csv",
        ["row_index", "product_code", "type_code", "name", "family_code", "brand_1", "brand_2"],
        rows,
    )


def extract_stock(table: ParsedTable, output_dir: Path) -> None:
    rows = []
    for idx, row in enumerate(table.rows):
        rows.append(
            {
                "row_index": idx,
                "product_code": row[0] if len(row) > 0 else "",
                "location_code": row[1] if len(row) > 1 else "",
                "date_token": row[2] if len(row) > 2 else "",
                "time_token": row[3] if len(row) > 3 else "",
                "qty_token_raw": normalize_ascii(row[5]) if len(row) > 5 else "",
            }
        )
    write_csv(output_dir / "stock_rows.csv", ["row_index", "product_code", "location_code", "date_token", "time_token", "qty_token_raw"], rows)


def write_summary(output_dir: Path, tables: List[ParsedTable]) -> None:
    payload = {table.name: {"record_length": table.rec_len, "row_count": len(table.rows)} for table in tables}
    (output_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract additional business domains from legacy FIC files.")
    parser.add_argument("--input-dir", required=True, help="Legacy directory with .FIC files")
    parser.add_argument("--output-dir", default="tmp/legacy_domains", help="Output directory")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    clients = parse_table(input_dir / "CLIENT.FIC")
    staff = parse_table(input_dir / "PERSONNE.FIC")
    visit_lines = parse_table(input_dir / "FICHE.FIC")
    history = parse_table(input_dir / "HISTORIQ.FIC")
    products = parse_table(input_dir / "PRODUITS.FIC")
    stock = parse_table(input_dir / "STOCK.FIC")
    resume = parse_table(input_dir / "RESUME.FIC")

    extract_clients(clients, output_dir)
    extract_staff(staff, output_dir)
    extract_visit_lines(visit_lines, output_dir)
    extract_history(history, output_dir)
    extract_products(products, output_dir)
    extract_stock(stock, output_dir)
    write_summary(output_dir, [clients, staff, visit_lines, history, products, stock, resume])

    print(f"output={output_dir}")
    print(f"clients={len(clients.rows)} staff={len(staff.rows)} visits={len(visit_lines.rows)} history={len(history.rows)}")
    print(f"products={len(products.rows)} stock={len(stock.rows)} resume={len(resume.rows)}")


if __name__ == "__main__":
    main()

