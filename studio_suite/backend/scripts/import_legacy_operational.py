#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable

from sqlalchemy import text

from app.database import SessionLocal
from app.models.salon_core import (
    Appointment,
    AppointmentPerformedLine,
    AppointmentResource,
    AppointmentService,
    BundleCatalog,
    Customer,
    LegacyClientCard,
    LegacyCustomerMatch,
    LegacyHistoryCard,
    LegacyImportBatch,
    LegacyRawRecord,
    LegacySourceFile,
    LegacyVisitDocument,
    LegacyVisitDocumentLine,
    LegacyWorkerCard,
    Salon,
    ServiceCatalogItem,
    ServicePriceHistory,
    StaffMember,
    StaffRole,
)
from app.utils.file_utils import calculate_file_hash


ROOT_DIR = Path(__file__).resolve().parents[1]

ROLE_BY_CATEGORY = {
    "1": "MANAGER",
    "2": "EMPLOYEE",
    "3": "EMPLOYEE",
    "4": "EMPLOYEE",
    "5": "EMPLOYEE",
    "6": "EMPLOYEE",
    "7": "RECEPTIONIST",
    "8": "EMPLOYEE",
    "9": "EMPLOYEE",
    "A": "EMPLOYEE",
}


@dataclass
class SalonInput:
    code: str
    fic_dir: Path
    domain_dir: Path
    priced_fiche_csv: Path | None


def parse_date_token(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    if not re.fullmatch(r"\d{8}", value):
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None


def normalize_name(*parts: str) -> str:
    merged = " ".join((p or "").strip() for p in parts if (p or "").strip())
    merged = re.sub(r"\s+", " ", merged).strip()
    if not merged:
        return ""
    merged = merged.replace("?", "").replace("  ", " ").strip()
    return merged.title()


def dedupe_key(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "", name.upper())
    return normalized[:128]


def parse_fic(path: Path) -> tuple[int, int, list[list[str]]]:
    data = path.read_bytes()
    rec_len = int(data[7:11].decode("ascii"))
    offset = rec_len
    total = max(0, (len(data) - offset) // rec_len)
    rows: list[list[str]] = []
    for i in range(total):
        chunk = data[offset + i * rec_len : offset + (i + 1) * rec_len]
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        rows.append(parts)
    return rec_len, total, rows


def to_amount(value: str | None) -> float:
    if not value:
        return 0.0
    clean = str(value).strip().replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def reset_target_data(db) -> None:
    db.execute(
        text(
            """
            TRUNCATE TABLE
              legacy_customer_matches,
              legacy_visit_document_lines,
              legacy_visit_documents,
              legacy_worker_cards,
              legacy_history_cards,
              legacy_client_cards,
              legacy_raw_records,
              legacy_source_files,
              legacy_import_batches
            RESTART IDENTITY CASCADE
            """
        )
    )
    db.execute(
        text(
            """
            TRUNCATE TABLE
              appointment_performed_lines,
              appointment_services,
              appointment_resources,
              appointments,
              customers,
              staff_members
            RESTART IDENTITY CASCADE
            """
        )
    )
    db.commit()


def ensure_role_ids(db) -> dict[str, int]:
    required = {
        "ADMIN": "Admin",
        "MANAGER": "Manager",
        "EMPLOYEE": "Employee",
        "RECEPTIONIST": "Receptionist",
    }
    out: dict[str, int] = {}
    for code, name in required.items():
        row = db.query(StaffRole).filter(StaffRole.code == code).first()
        if not row:
            row = StaffRole(code=code, name=name)
            db.add(row)
            db.flush()
        out[code] = row.id
    db.commit()
    return out


def ensure_unknown_customer(db, salon_id: int, salon_code: str) -> Customer:
    key = f"UNKNOWN-{salon_code}"
    row = db.query(Customer).filter(Customer.legacy_code == key).first()
    if row:
        return row
    row = Customer(
        legacy_code=key,
        display_name=f"Niezidentyfikowany klient ({salon_code})",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Import operational legacy data for two salons into shared database.")
    parser.add_argument("--reset", action="store_true", help="Reset import/staging and operational tables before import")
    args = parser.parse_args()

    salons = [
        SalonInput(
            code="05",
            fic_dir=ROOT_DIR / "tmp" / "legacy_05",
            domain_dir=ROOT_DIR / "tmp" / "legacy_05" / "domain_export",
            priced_fiche_csv=ROOT_DIR / "tmp" / "legacy_05" / "report_export" / "fiche_lines_priced.csv",
        ),
        SalonInput(
            code="12",
            fic_dir=ROOT_DIR / "tmp" / "legacy_12",
            domain_dir=ROOT_DIR / "tmp" / "legacy_12" / "domain_export",
            priced_fiche_csv=None,
        ),
    ]

    db = SessionLocal()
    try:
        if args.reset:
            reset_target_data(db)

        role_ids = ensure_role_ids(db)
        service_by_code = {row.legacy_code: row.id for row in db.query(ServiceCatalogItem).all()}
        service_price_by_salon_code: dict[str, dict[str, float]] = defaultdict(dict)
        salon_by_id = {row.id: row.code for row in db.query(Salon).all()}
        for row in db.query(ServicePriceHistory).all():
            code = salon_by_id.get(row.salon_id or -1)
            if code:
                svc = db.query(ServiceCatalogItem).filter(ServiceCatalogItem.id == row.service_id).first()
                if svc:
                    service_price_by_salon_code[code][svc.legacy_code] = float(row.price or 0)

        total_raw = 0
        total_customers = 0
        total_appointments = 0

        for source in salons:
            if not source.fic_dir.exists():
                continue

            salon = db.query(Salon).filter(Salon.code == source.code).first()
            if not salon:
                salon = Salon(code=source.code, name=f"SALON {source.code}", is_active=True)
                db.add(salon)
                db.commit()
                db.refresh(salon)

            batch = LegacyImportBatch(
                source_salon_code=source.code,
                source_path=str(source.fic_dir),
                status="running",
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)

            source_file_by_name: dict[str, LegacySourceFile] = {}
            for fic_path in sorted(source.fic_dir.glob("*.FIC")):
                rec_len, total, rows = parse_fic(fic_path)
                source_file = LegacySourceFile(
                    batch_id=batch.id,
                    salon_id=salon.id,
                    salon_code=source.code,
                    file_name=fic_path.name,
                    record_length=rec_len,
                    row_count=total,
                    parsed_row_count=total,
                    file_size_bytes=fic_path.stat().st_size,
                    sha256=calculate_file_hash(str(fic_path)),
                )
                db.add(source_file)
                db.flush()
                source_file_by_name[fic_path.name] = source_file

                raw_rows = []
                for idx, tokens in enumerate(rows):
                    raw_rows.append(
                        {
                            "source_file_id": source_file.id,
                            "row_index": idx,
                            "token_count": len(tokens),
                            "tokens_payload": json.dumps(tokens, ensure_ascii=False),
                            "parse_status": "raw",
                        }
                    )
                    if len(raw_rows) >= 1000:
                        db.execute(LegacyRawRecord.__table__.insert(), raw_rows)
                        total_raw += len(raw_rows)
                        raw_rows = []
                if raw_rows:
                    db.execute(LegacyRawRecord.__table__.insert(), raw_rows)
                    total_raw += len(raw_rows)
            db.commit()

            workers_csv = load_csv(source.domain_dir / "staff_candidates.csv")
            worker_card_by_code: dict[str, LegacyWorkerCard] = {}
            for row in workers_csv:
                worker_code = (row.get("code") or "").strip()
                role_code = ROLE_BY_CATEGORY.get((row.get("category_token") or "").strip(), "EMPLOYEE")
                full_name = normalize_name(row.get("full_label") or "", f"{row.get('first_label') or ''} {row.get('second_label') or ''}")
                if not full_name:
                    full_name = f"Pracownik {source.code}-{worker_code or row.get('row_index', 'x')}"
                mapped_staff_id = None
                if row.get("is_probable_employee") == "yes":
                    staff = (
                        db.query(StaffMember)
                        .filter(StaffMember.salon_id == salon.id, StaffMember.legacy_code == worker_code)
                        .first()
                    )
                    if not staff:
                        names = full_name.split(maxsplit=1)
                        staff = StaffMember(
                            salon_id=salon.id,
                            role_id=role_ids.get(role_code, role_ids["EMPLOYEE"]),
                            legacy_code=worker_code or None,
                            first_name=names[0] if names else None,
                            last_name=names[1] if len(names) > 1 else None,
                            display_name=full_name,
                            is_active=True,
                        )
                        db.add(staff)
                        db.flush()
                    mapped_staff_id = staff.id
                card = LegacyWorkerCard(
                    batch_id=batch.id,
                    source_file_id=source_file_by_name.get("PERSONNE.FIC").id if source_file_by_name.get("PERSONNE.FIC") else None,
                    salon_id=salon.id,
                    salon_code=source.code,
                    source_row_index=int(row.get("row_index") or 0),
                    worker_code=worker_code or None,
                    first_label=(row.get("first_label") or "").strip() or None,
                    second_label=(row.get("second_label") or "").strip() or None,
                    full_label=(row.get("full_label") or "").strip() or None,
                    category_token=(row.get("category_token") or "").strip() or None,
                    is_probable_employee=row.get("is_probable_employee") == "yes",
                    mapped_staff_id=mapped_staff_id,
                    confidence=1 if mapped_staff_id else 0,
                )
                db.add(card)
                db.flush()
                if worker_code:
                    worker_card_by_code[worker_code] = card

            clients_csv = load_csv(source.domain_dir / "clients_candidates.csv")
            client_cards_by_date: dict[str, list[LegacyClientCard]] = defaultdict(list)
            for row in clients_csv:
                name = normalize_name(row.get("label_2") or "", row.get("label_1") or "")
                if not name:
                    name = f"Klient {source.code}-{row.get('row_index', 'x')}"
                key = f"{source.code}:{row.get('row_index')}"
                existing_customer = db.query(Customer).filter(Customer.legacy_code == key).first()
                if not existing_customer:
                    names = name.split(maxsplit=1)
                    existing_customer = Customer(
                        legacy_code=key,
                        first_name=names[0] if names else None,
                        last_name=names[1] if len(names) > 1 else None,
                        display_name=name,
                        first_visit_at=parse_date_token(row.get("date_token")),
                        last_visit_at=parse_date_token(row.get("date_token")),
                    )
                    db.add(existing_customer)
                    db.flush()
                    total_customers += 1

                card = LegacyClientCard(
                    batch_id=batch.id,
                    source_file_id=source_file_by_name.get("CLIENT.FIC").id if source_file_by_name.get("CLIENT.FIC") else None,
                    salon_id=salon.id,
                    salon_code=source.code,
                    source_row_index=int(row.get("row_index") or 0),
                    label_1=(row.get("label_1") or "").strip() or None,
                    label_2=(row.get("label_2") or "").strip() or None,
                    gender=(row.get("gender") or "").strip() or None,
                    date_token=(row.get("date_token") or "").strip() or None,
                    service_code_count=int(row.get("service_code_count") or 0),
                    service_codes_sample=(row.get("service_codes_sample") or "").strip() or None,
                    normalized_name=name,
                    dedupe_key=dedupe_key(name),
                    mapped_customer_id=existing_customer.id,
                    confidence=1,
                )
                db.add(card)
                db.flush()
                if card.date_token:
                    client_cards_by_date[card.date_token].append(card)
                db.add(
                    LegacyCustomerMatch(
                        salon_id=salon.id,
                        salon_code=source.code,
                        client_card_id=card.id,
                        customer_id=existing_customer.id,
                        match_rule="client_card_row",
                        confidence=1,
                        is_accepted=True,
                    )
                )

            history_csv = load_csv(source.domain_dir / "history_cards.csv")
            customer_by_name = {dedupe_key(c.display_name): c for c in db.query(Customer).filter(Customer.legacy_code.like(f"{source.code}:%")).all()}
            for row in history_csv:
                name = normalize_name(row.get("name") or "", row.get("surname") or "")
                if not name:
                    continue
                key = dedupe_key(name)
                customer = customer_by_name.get(key)
                if not customer:
                    customer = Customer(
                        legacy_code=f"{source.code}:H:{row.get('row_index')}",
                        display_name=name,
                    )
                    db.add(customer)
                    db.flush()
                    customer_by_name[key] = customer
                    total_customers += 1
                db.add(
                    LegacyHistoryCard(
                        batch_id=batch.id,
                        source_file_id=source_file_by_name.get("HISTORIQ.FIC").id if source_file_by_name.get("HISTORIQ.FIC") else None,
                        salon_id=salon.id,
                        salon_code=source.code,
                        source_row_index=int(row.get("row_index") or 0),
                        surname=(row.get("surname") or "").strip() or None,
                        name=(row.get("name") or "").strip() or None,
                        birth_or_ref=(row.get("birth_or_ref") or "").strip() or None,
                        text_events_count=int(row.get("text_events_count") or 0),
                        text_events_sample=(row.get("text_events_sample") or "").strip() or None,
                        normalized_name=name,
                        mapped_customer_id=customer.id,
                        confidence=0.9,
                    )
                )

            visit_lines_domain = load_csv(source.domain_dir / "visit_lines.csv")
            channel_by_ticket_date: dict[tuple[str, str], str] = {}
            for r in visit_lines_domain:
                ticket = (r.get("ticket_code") or "").strip()
                dt = (r.get("date_token") or "").strip()
                if ticket and dt and (ticket, dt) not in channel_by_ticket_date:
                    channel_by_ticket_date[(ticket, dt)] = (r.get("channel_code") or "").strip()

            if source.priced_fiche_csv and source.priced_fiche_csv.exists():
                raw_lines = load_csv(source.priced_fiche_csv)
            else:
                raw_lines = []
                for r in visit_lines_domain:
                    service_code = (r.get("service_code") or "").strip().zfill(4)
                    amount = service_price_by_salon_code[source.code].get(service_code, 0.0)
                    raw_lines.append(
                        {
                            "row_index": r.get("row_index"),
                            "ticket_code": r.get("ticket_code"),
                            "line_code": r.get("line_code"),
                            "date_token": r.get("date_token"),
                            "worker_code": r.get("worker_code"),
                            "service_code": service_code,
                            "amount": amount,
                            "payment_hint": "",
                            "bundle_code": "",
                        }
                    )

            grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
            for row in raw_lines:
                ticket = (row.get("ticket_code") or "").strip()
                dt = (row.get("date_token") or "").strip()
                if not ticket or not dt:
                    continue
                grouped[(ticket, dt)].append(row)

            bundle_by_code = {
                (str(row.salon_id), row.legacy_code): row.id
                for row in db.query(BundleCatalog).all()
            }

            unknown_customer = ensure_unknown_customer(db, salon.id, source.code)
            customer_usage: dict[int, int] = defaultdict(int)
            all_client_cards = [card for cards in client_cards_by_date.values() for card in cards if card.mapped_customer_id]
            all_client_cards.sort(key=lambda c: c.source_row_index)

            for (ticket, dt), lines in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
                service_set = {(ln.get("service_code") or "").strip().zfill(4) for ln in lines if (ln.get("service_code") or "").strip()}
                candidates = client_cards_by_date.get(dt, [])
                chosen: LegacyClientCard | None = None
                chosen_score: tuple[int, int] = (-1, -10**9)
                for cand in candidates:
                    sample = set((cand.service_codes_sample or "").split(";")) if cand.service_codes_sample else set()
                    overlap = len(service_set.intersection(sample))
                    usage = customer_usage.get(cand.mapped_customer_id or -1, 0)
                    score = (overlap, -usage)
                    if score > chosen_score:
                        chosen_score = score
                        chosen = cand

                if chosen and chosen.mapped_customer_id:
                    customer_id = chosen.mapped_customer_id
                    doc_match_rule = "date+service_overlap"
                    doc_confidence = 0.8
                elif all_client_cards:
                    ticket_num = int(ticket) if ticket.isdigit() else 0
                    day_num = int(dt[-2:]) if dt and dt[-2:].isdigit() else 0
                    idx = (ticket_num + day_num) % len(all_client_cards)
                    customer_id = all_client_cards[idx].mapped_customer_id or unknown_customer.id
                    doc_match_rule = "fallback_hash"
                    doc_confidence = 0.35
                else:
                    customer_id = unknown_customer.id
                    doc_match_rule = "unknown_fallback"
                    doc_confidence = 0.2
                customer_usage[customer_id] = customer_usage.get(customer_id, 0) + 1
                visit_date = parse_date_token(dt) or date.today()
                slot = (int(ticket) if ticket.isdigit() else 0) % 20
                start_dt = datetime.combine(visit_date, time(8, 0)) + timedelta(minutes=30 * slot)
                duration = max(30, 20 * max(1, len(lines)))
                end_dt = start_dt + timedelta(minutes=duration)
                payment_hint = next((ln.get("payment_hint") for ln in lines if ln.get("payment_hint")), "")
                total_amount = round(sum(to_amount(ln.get("amount")) for ln in lines), 2)
                channel_code = channel_by_ticket_date.get((ticket, dt), source.code)
                bundle_code = next((ln.get("bundle_code") or "" for ln in lines if (ln.get("bundle_code") or "").strip()), "")
                bundle_id = bundle_by_code.get((str(salon.id), bundle_code)) if bundle_code else None

                appointment = Appointment(
                    salon_id=salon.id,
                    client_id=customer_id,
                    start_at=start_dt,
                    end_at=end_dt,
                    status="done",
                    bundle_id=bundle_id,
                    total_price_snapshot=total_amount,
                )
                db.add(appointment)
                db.flush()
                total_appointments += 1

                doc = LegacyVisitDocument(
                    batch_id=batch.id,
                    source_file_id=source_file_by_name.get("FICHE.FIC").id if source_file_by_name.get("FICHE.FIC") else None,
                    salon_id=salon.id,
                    salon_code=source.code,
                    ticket_code=ticket,
                    date_token=dt,
                    visit_date=visit_date,
                    channel_code=channel_code or None,
                    mapped_customer_id=customer_id,
                    mapped_appointment_id=appointment.id,
                    total_amount=total_amount,
                    payment_hint=(payment_hint or "").strip() or None,
                    source_client_row_index=chosen.source_row_index if chosen else None,
                    match_rule=doc_match_rule,
                    confidence=doc_confidence,
                )
                db.add(doc)
                db.flush()

                seen_services: set[int] = set()
                seen_staff: set[int] = set()
                for ln in lines:
                    service_code = (ln.get("service_code") or "").strip().zfill(4)
                    service_id = service_by_code.get(service_code)
                    worker_code = (ln.get("worker_code") or "").strip()
                    worker = worker_card_by_code.get(worker_code)
                    staff_id = worker.mapped_staff_id if worker else None

                    if service_id and service_id not in seen_services:
                        db.add(AppointmentService(appointment_id=appointment.id, service_id=service_id))
                        seen_services.add(service_id)
                    if staff_id and staff_id not in seen_staff:
                        db.add(AppointmentResource(appointment_id=appointment.id, staff_id=staff_id))
                        seen_staff.add(staff_id)

                    mapped_performed_line_id = None
                    if service_id and staff_id:
                        staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
                        performed = AppointmentPerformedLine(
                            appointment_id=appointment.id,
                            service_id=service_id,
                            worker_id=staff_id,
                            worker_role_id=(staff.role_id if staff and staff.role_id else role_ids["EMPLOYEE"]),
                            price_snapshot=to_amount(ln.get("amount")),
                            performed_at=end_dt,
                            color_product_id=None,
                        )
                        db.add(performed)
                        db.flush()
                        mapped_performed_line_id = performed.id

                    db.add(
                        LegacyVisitDocumentLine(
                            document_id=doc.id,
                            source_file_id=source_file_by_name.get("FICHE.FIC").id if source_file_by_name.get("FICHE.FIC") else None,
                            source_row_index=int(ln.get("row_index") or 0),
                            line_code=f"{(ln.get('line_code') or '').strip()}:{int(ln.get('row_index') or 0)}",
                            service_code=service_code,
                            worker_code=worker_code or None,
                            qty_token=(ln.get("qty_token") or "").strip() or None,
                            state_flag=(ln.get("state_flag") or "").strip() or None,
                            kind_flag=(ln.get("kind_flag") or "").strip() or None,
                            group_code=(ln.get("group_code") or "").strip() or None,
                            amount=to_amount(ln.get("amount")),
                            price_token_raw=(ln.get("price_token_raw") or "").strip() or None,
                            mapped_service_id=service_id,
                            mapped_staff_id=staff_id,
                            mapped_performed_line_id=mapped_performed_line_id,
                        )
                    )
                db.commit()

            for customer in db.query(Customer).all():
                visits = (
                    db.query(Appointment)
                    .filter(Appointment.client_id == customer.id)
                    .order_by(Appointment.start_at.asc())
                    .all()
                )
                if visits:
                    customer.first_visit_at = visits[0].start_at.date()
                    customer.last_visit_at = visits[-1].start_at.date()
            batch.status = "completed"
            batch.finished_at = datetime.utcnow()
            db.commit()

        print("import_done")
        print(f"raw_records={total_raw}")
        print(f"customers={db.query(Customer).count()}")
        print(f"appointments={db.query(Appointment).count()}")
        print(f"visit_documents={db.query(LegacyVisitDocument).count()}")
        print(f"visit_document_lines={db.query(LegacyVisitDocumentLine).count()}")
        print(f"worker_cards={db.query(LegacyWorkerCard).count()}")
        print(f"client_cards={db.query(LegacyClientCard).count()}")
        print(f"history_cards={db.query(LegacyHistoryCard).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
