#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


KEYWORD_BLOCKLIST = [
    "GROUPON",
    "KARNET",
    "VOUCHER",
    "VIP",
    "PROM",
    "MASKA",
    "SPRZEDA",
    "GRATIS",
    "PRACOWNIK",
    "KARTA",
]

FUNCTION_CODE_TO_ROLE_ID = {
    "1": 5,  # MENAGER
    "2": 1,  # FRYZJER
    "3": 2,  # ASYSTENT
    "4": 2,  # POMOC
    "5": 6,  # TECHNIK
    "6": 3,  # KOSMETYCZKA
    "7": 4,  # RECEPCJONISTA
    "8": 3,  # MANICURZYSTKA
    "9": 7,  # INNY
    "A": 8,  # MASAZYSTKA
}

BOOKABLE_FUNCTION_CODES = {"2", "6", "8"}


def looks_like_person(text: str) -> bool:
    t = text.upper().strip()
    if not t:
        return False
    if any(word in t for word in KEYWORD_BLOCKLIST):
        return False
    letters = sum(1 for ch in t if ch.isalpha())
    return letters >= 3


def normalize_name(label_1: str, label_2: str) -> str:
    a = " ".join(label_1.split())
    b = " ".join(label_2.split())
    if looks_like_person(a) and looks_like_person(b):
        if b.upper() in a.upper():
            return a.title()
        return f"{a} {b}".title()
    if looks_like_person(b):
        return b.title()
    if looks_like_person(a):
        return a.title()
    return ""


def load_services_map(services_import_csv: Path) -> Tuple[Dict[str, int], Dict[str, float]]:
    code_to_id: Dict[str, int] = {}
    code_to_price: Dict[str, float] = {}
    with services_import_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for idx, row in enumerate(rows, start=1):
        code = row["service_code"].zfill(4)
        code_to_id[code] = idx
        raw = (row.get("price") or "0").replace(",", ".")
        try:
            code_to_price[code] = float(raw)
        except ValueError:
            code_to_price[code] = 0.0
    return code_to_id, code_to_price


def parse_clients(clients_candidates_csv: Path, max_clients: int) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    seen = set()
    with clients_candidates_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = normalize_name(row.get("label_1", ""), row.get("label_2", ""))
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "id": len(out) + 1,
                    "full_name": name,
                    "phone": "",
                    "email": "",
                }
            )
            if len(out) >= max_clients:
                break
    return out


def parse_staff(staff_candidates_csv: Path, max_staff: int) -> Tuple[List[Dict[str, object]], Dict[str, int]]:
    resources: List[Dict[str, object]] = []
    code_to_resource_id: Dict[str, int] = {}
    with staff_candidates_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("is_probable_employee") != "yes":
                continue
            code = (row.get("code") or "").zfill(2)
            full = (row.get("full_label") or "").strip()
            first = (row.get("first_label") or "").strip()
            second = (row.get("second_label") or "").strip()
            name = full if looks_like_person(full) else normalize_name(first, second)
            if not name:
                continue
            category = (row.get("category_token") or "").strip()
            role_id = FUNCTION_CODE_TO_ROLE_ID.get(category, 7)
            if category not in BOOKABLE_FUNCTION_CODES:
                continue
            resources.append(
                {
                    "id": len(resources) + 1,
                    "salon_id": 1,
                    "name": name,
                    "role_ids": [role_id],
                }
            )
            code_to_resource_id[code] = resources[-1]["id"]
            if len(resources) >= max_staff:
                break
    return resources, code_to_resource_id


def parse_visit_lines(visit_lines_csv: Path) -> Dict[Tuple[str, str], List[Dict[str, str]]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    with visit_lines_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ticket = (row.get("ticket_code") or "").zfill(4)
            date = (row.get("date_token") or "").strip()
            if not ticket or not date or len(date) != 8:
                continue
            grouped[(ticket, date)].append(row)
    return grouped


def build_operational(
    clients: List[Dict[str, object]],
    resources: List[Dict[str, object]],
    code_to_resource_id: Dict[str, int],
    service_code_to_id: Dict[str, int],
    service_code_to_price: Dict[str, float],
    grouped_lines: Dict[Tuple[str, str], List[Dict[str, str]]],
    max_appointments: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    appointments: List[Dict[str, object]] = []
    performed: List[Dict[str, object]] = []
    if not clients:
        return appointments, performed

    by_date = sorted(grouped_lines.items(), key=lambda item: item[0][1])
    by_date = by_date[-max_appointments:]

    for idx, ((ticket, date_token), lines) in enumerate(by_date, start=1):
        day = datetime.strptime(date_token, "%Y%m%d")
        start_at = day + timedelta(hours=8, minutes=(idx % 18) * 30)
        end_at = start_at + timedelta(minutes=max(30, 20 * len(lines)))
        client_id = ((idx - 1) % len(clients)) + 1

        service_ids = []
        resource_ids = []
        line_payload = []
        for line in lines:
            service_code = (line.get("service_code") or "").zfill(4)
            service_id = service_code_to_id.get(service_code)
            worker_code = (line.get("worker_code") or "").zfill(2)
            worker_id = code_to_resource_id.get(worker_code)
            if service_id:
                service_ids.append(service_id)
            if worker_id:
                resource_ids.append(worker_id)
            if service_id and worker_id:
                worker = next((r for r in resources if r["id"] == worker_id), None)
                role_id = (worker or {}).get("role_ids", [1])[0]
                line_payload.append(
                    {
                        "id": len(performed) + len(line_payload) + 1,
                        "appointment_id": idx,
                        "service_id": service_id,
                        "worker_id": worker_id,
                        "worker_role_id": role_id,
                        "price_snapshot": service_code_to_price.get(service_code, 0.0),
                        "performed_at": end_at.isoformat(timespec="seconds"),
                    }
                )

        service_ids = sorted(set(service_ids))
        resource_ids = sorted(set(resource_ids))
        revenue = round(sum(line["price_snapshot"] for line in line_payload), 2)
        appointments.append(
            {
                "id": idx,
                "salon_id": 1,
                "client_id": client_id,
                "start_at": start_at.isoformat(timespec="seconds"),
                "end_at": end_at.isoformat(timespec="seconds"),
                "status": "done",
                "resources": resource_ids,
                "services": service_ids,
                "total_price_snapshot": revenue,
            }
        )
        performed.extend(line_payload)
    return appointments, performed


def write_seed_ts(
    output_ts: Path,
    clients: List[Dict[str, object]],
    resources: List[Dict[str, object]],
    appointments: List[Dict[str, object]],
    performed: List[Dict[str, object]],
) -> None:
    output_ts.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "import { Appointment, ClientCard, PerformedServiceLine, StaffResource } from '../types'\n\n"
        f"export const legacyClients: ClientCard[] = {json.dumps(clients, ensure_ascii=False)}\n\n"
        f"export const legacyResources: StaffResource[] = {json.dumps(resources, ensure_ascii=False)}\n\n"
        f"export const legacyAppointments: Appointment[] = {json.dumps(appointments, ensure_ascii=False)}\n\n"
        f"export const legacyPerformedServiceLines: PerformedServiceLine[] = {json.dumps(performed, ensure_ascii=False)}\n"
    )
    output_ts.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build operational seed (clients/staff/appointments) from extracted legacy CSV.")
    parser.add_argument("--domain-export-dir", required=True, help="Directory containing clients_candidates.csv etc.")
    parser.add_argument("--services-import-csv", required=True, help="services_import.csv from legacy catalog import")
    parser.add_argument("--output-ts", default="frontend/src/mocks/legacyOperationalSeed.ts")
    parser.add_argument("--max-clients", type=int, default=1200)
    parser.add_argument("--max-staff", type=int, default=80)
    parser.add_argument("--max-appointments", type=int, default=800)
    args = parser.parse_args()

    domain = Path(args.domain_export_dir)
    services_csv = Path(args.services_import_csv)

    service_code_to_id, service_code_to_price = load_services_map(services_csv)
    clients = parse_clients(domain / "clients_candidates.csv", args.max_clients)
    resources, code_to_resource_id = parse_staff(domain / "staff_candidates.csv", args.max_staff)
    grouped_lines = parse_visit_lines(domain / "visit_lines.csv")

    appointments, performed = build_operational(
        clients,
        resources,
        code_to_resource_id,
        service_code_to_id,
        service_code_to_price,
        grouped_lines,
        args.max_appointments,
    )

    write_seed_ts(Path(args.output_ts), clients, resources, appointments, performed)
    print(f"clients={len(clients)} staff={len(resources)} appointments={len(appointments)} performed_lines={len(performed)}")
    print(f"output={args.output_ts}")


if __name__ == "__main__":
    main()
