#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import struct
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


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


def write_csv(path: Path, fieldnames: List[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def as_double(chunk: bytes, offset: int) -> float:
    if offset + 8 > len(chunk):
        return 0.0
    value = struct.unpack("<d", chunk[offset : offset + 8])[0]
    if not (0 <= value <= 1_000_000):
        return 0.0
    return round(value, 2)


def load_workers(personne_fic: Path) -> Dict[str, str]:
    _, _, rows = parse_records(personne_fic)
    out: Dict[str, str] = {}
    for row in rows:
        if len(row) < 4 or not row[0].isdigit():
            continue
        code = row[0].zfill(2)
        full = row[3].strip()
        first = row[1].strip() if len(row) > 1 else ""
        second = row[2].strip() if len(row) > 2 else ""
        name = full or f"{first} {second}".strip()
        out[code] = name
    return out


def load_services(service_fic: Path) -> Dict[str, str]:
    _, _, rows = parse_records(service_fic)
    out: Dict[str, str] = {}
    for row in rows:
        if len(row) < 4 or not row[0].isdigit():
            continue
        out[row[0].zfill(4)] = row[3].strip()
    return out


def extract_forfaits_list(forfaits_fic: Path, output_dir: Path) -> Dict[str, Dict[str, object]]:
    _, chunks, rows = parse_records(forfaits_fic)
    transactions: List[Dict[str, object]] = []
    grouped: Dict[str, Dict[str, object]] = defaultdict(lambda: {"name": "", "count": 0, "revenue": 0.0})

    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 5 or not row[1].isdigit():
            continue
        bundle_code = row[1].zfill(4)
        bundle_name = row[3].strip()
        date_token = row[4] if row[4].isdigit() else ""
        price = as_double(chunk, 56)
        transactions.append(
            {
                "row_index": idx,
                "date_token": date_token,
                "bundle_code": bundle_code,
                "bundle_name": bundle_name,
                "price": price,
            }
        )
        grouped[bundle_code]["name"] = bundle_name
        grouped[bundle_code]["count"] += 1
        grouped[bundle_code]["revenue"] = round(float(grouped[bundle_code]["revenue"]) + price, 2)

    analysis_rows = [
        {
            "bundle_code": code,
            "bundle_name": meta["name"],
            "count": meta["count"],
            "revenue": round(float(meta["revenue"]), 2),
        }
        for code, meta in sorted(grouped.items())
    ]

    write_csv(
        output_dir / "ed5_forfaits_list.csv",
        ["row_index", "date_token", "bundle_code", "bundle_name", "price"],
        transactions,
    )
    write_csv(
        output_dir / "ed4_forfaits_analysis.csv",
        ["bundle_code", "bundle_name", "count", "revenue"],
        analysis_rows,
    )
    return grouped


def extract_edservic(eds_fic: Path, workers: Dict[str, str], services: Dict[str, str], output_dir: Path) -> None:
    _, chunks, rows = parse_records(eds_fic)
    detail: List[Dict[str, object]] = []
    by_service: Dict[str, Dict[str, object]] = defaultdict(lambda: {"service_name": "", "qty": 0, "revenue": 0.0})

    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 2 or not row[0].isdigit() or not row[1].isdigit():
            continue
        service_code = row[0].zfill(4)
        worker_code = row[1].zfill(2)
        amount = as_double(chunk, 9)
        detail.append(
            {
                "row_index": idx,
                "service_code": service_code,
                "service_name": services.get(service_code, ""),
                "worker_code": worker_code,
                "worker_name": workers.get(worker_code, ""),
                "amount": amount,
            }
        )
        by_service[service_code]["service_name"] = services.get(service_code, "")
        by_service[service_code]["qty"] += 1
        by_service[service_code]["revenue"] = round(float(by_service[service_code]["revenue"]) + amount, 2)

    aggregate = [
        {
            "service_code": code,
            "service_name": meta["service_name"],
            "qty": meta["qty"],
            "revenue": round(float(meta["revenue"]), 2),
        }
        for code, meta in sorted(by_service.items())
    ]

    write_csv(
        output_dir / "ed6_services_by_worker_detail.csv",
        ["row_index", "service_code", "service_name", "worker_code", "worker_name", "amount"],
        detail,
    )
    write_csv(
        output_dir / "ed6_services_aggregate.csv",
        ["service_code", "service_name", "qty", "revenue"],
        aggregate,
    )


def extract_edition1(edition1_fic: Path, output_dir: Path) -> None:
    _, chunks, rows = parse_records(edition1_fic)
    # Confirmed numeric offsets from file inspection.
    numeric_offsets = [47, 79, 119, 165, 173, 189]
    out_rows: List[Dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 7:
            continue
        item: Dict[str, object] = {
            "row_index": idx,
            "period_major": row[0] if len(row) > 0 else "",
            "period_minor": row[1] if len(row) > 1 else "",
            "day_number": row[2] if len(row) > 2 else "",
            "day_name": row[3] if len(row) > 3 else "",
            "date_token": row[5] if len(row) > 5 else "",
            "salon_code": row[6] if len(row) > 6 else "",
        }
        for offset in numeric_offsets:
            item[f"value_{offset}"] = as_double(chunk, offset)
        out_rows.append(item)
    write_csv(
        output_dir / "ed1_daily_summary_raw.csv",
        ["row_index", "period_major", "period_minor", "day_number", "day_name", "date_token", "salon_code"]
        + [f"value_{offset}" for offset in numeric_offsets],
        out_rows,
    )


def extract_stat7(stat7_fic: Path, output_dir: Path) -> None:
    _, chunks, rows = parse_records(stat7_fic)
    # Store tokens + strongest numeric offsets for offline mapping.
    numeric_offsets = [295, 323, 331, 339, 347]
    out_rows: List[Dict[str, object]] = []
    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 6:
            continue
        item: Dict[str, object] = {
            "row_index": idx,
            "date_token_compact": row[0] if len(row) > 0 else "",
            "worker_code": row[1] if len(row) > 1 else "",
            "payment_a": row[2] if len(row) > 2 else "",
            "payment_b": row[3] if len(row) > 3 else "",
            "payment_c": row[4] if len(row) > 4 else "",
            "worker_name": row[5] if len(row) > 5 else "",
        }
        for offset in numeric_offsets:
            item[f"value_{offset}"] = as_double(chunk, offset)
        out_rows.append(item)
    write_csv(
        output_dir / "ed7_stat7_raw.csv",
        ["row_index", "date_token_compact", "worker_code", "payment_a", "payment_b", "payment_c", "worker_name"]
        + [f"value_{offset}" for offset in numeric_offsets],
        out_rows,
    )


def extract_fiche_for_reports(
    fiche_fic: Path,
    workers: Dict[str, str],
    services: Dict[str, str],
    output_dir: Path,
) -> None:
    _, chunks, rows = parse_records(fiche_fic)
    detail_rows: List[Dict[str, object]] = []
    by_worker_service: Dict[Tuple[str, str], Dict[str, object]] = defaultdict(
        lambda: {"worker_name": "", "service_name": "", "qty": 0, "revenue": 0.0}
    )
    by_day_payment: Dict[Tuple[str, str], Dict[str, object]] = defaultdict(lambda: {"count": 0, "revenue": 0.0})

    for idx, (chunk, row) in enumerate(zip(chunks, rows)):
        if len(row) < 9 or not row[8].isdigit():
            continue
        date_token = row[4] if len(row) > 4 and row[4].isdigit() else ""
        worker_code = row[5].zfill(2) if len(row) > 5 and row[5].isdigit() else ""
        service_code = row[8].zfill(4)
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

        detail_rows.append(
            {
                "row_index": idx,
                "ticket_code": row[0] if len(row) > 0 else "",
                "line_code": row[1] if len(row) > 1 else "",
                "date_token": date_token,
                "worker_code": worker_code,
                "worker_name": workers.get(worker_code, ""),
                "service_code": service_code,
                "service_name": services.get(service_code, ""),
                "amount": amount,
                "payment_hint": payment_hint,
                "bundle_code": row[27] if len(row) > 27 else "",
            }
        )

        key = (worker_code, service_code)
        by_worker_service[key]["worker_name"] = workers.get(worker_code, "")
        by_worker_service[key]["service_name"] = services.get(service_code, "")
        by_worker_service[key]["qty"] += 1
        by_worker_service[key]["revenue"] = round(float(by_worker_service[key]["revenue"]) + amount, 2)

        pay_key = (date_token, payment_hint or "UNKNOWN")
        by_day_payment[pay_key]["count"] += 1
        by_day_payment[pay_key]["revenue"] = round(float(by_day_payment[pay_key]["revenue"]) + amount, 2)

    worker_service_rows = [
        {
            "worker_code": worker_code,
            "worker_name": meta["worker_name"],
            "service_code": service_code,
            "service_name": meta["service_name"],
            "qty": meta["qty"],
            "revenue": round(float(meta["revenue"]), 2),
        }
        for (worker_code, service_code), meta in sorted(by_worker_service.items())
    ]
    day_payment_rows = [
        {
            "date_token": date_token,
            "payment_hint": payment_hint,
            "count": meta["count"],
            "revenue": round(float(meta["revenue"]), 2),
        }
        for (date_token, payment_hint), meta in sorted(by_day_payment.items())
    ]

    write_csv(
        output_dir / "fiche_lines_priced.csv",
        [
            "row_index",
            "ticket_code",
            "line_code",
            "date_token",
            "worker_code",
            "worker_name",
            "service_code",
            "service_name",
            "amount",
            "payment_hint",
            "bundle_code",
        ],
        detail_rows,
    )
    write_csv(
        output_dir / "ed8_worker_service_from_fiche.csv",
        ["worker_code", "worker_name", "service_code", "service_name", "qty", "revenue"],
        worker_service_rows,
    )
    write_csv(
        output_dir / "cashflow_by_day_payment_hint.csv",
        ["date_token", "payment_hint", "count", "revenue"],
        day_payment_rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract legacy report-source datasets from FIC files.")
    parser.add_argument("--input-dir", required=True, help="Directory with legacy .FIC files")
    parser.add_argument("--output-dir", required=True, help="Directory for report CSV outputs")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workers = load_workers(input_dir / "PERSONNE.FIC")
    services = load_services(input_dir / "SERVICE.FIC")
    forfaits_meta = extract_forfaits_list(input_dir / "FORFAITS.FIC", output_dir)
    extract_edservic(input_dir / "EDSERVIC.FIC", workers, services, output_dir)
    extract_edition1(input_dir / "EDITION1.FIC", output_dir)
    extract_stat7(input_dir / "STAT7.FIC", output_dir)
    extract_fiche_for_reports(input_dir / "FICHE.FIC", workers, services, output_dir)

    summary = {
        "workers_count": len(workers),
        "services_count": len(services),
        "forfaits_count_in_transactions": len(forfaits_meta),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"output={output_dir}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
