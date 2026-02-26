#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import struct
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def parse_service_catalog(service_fic: Path) -> Dict[str, Dict[str, object]]:
    data = service_fic.read_bytes()
    offset = 93
    rec = 93
    out: Dict[str, Dict[str, object]] = {}
    total = max(0, (len(data) - offset) // rec)
    for i in range(total):
        chunk = data[offset + i * rec : offset + (i + 1) * rec]
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        if len(parts) < 4 or not parts[0].isdigit():
            continue
        code = parts[0].zfill(4)
        price_regular = struct.unpack("<d", chunk[46:54])[0]
        price_holiday = struct.unpack("<d", chunk[54:62])[0]
        if not (0 <= price_regular <= 5000):
            price_regular = 0.0
        if not (0 <= price_holiday <= 5000):
            price_holiday = 0.0
        duration_raw = parts[9] if len(parts) > 9 else "60"
        duration_minutes = int(duration_raw) if duration_raw.isdigit() else 60
        out[code] = {
            "service_type_code": parts[1] if len(parts) > 1 else "",
            "grouping_code": parts[2] if len(parts) > 2 else "",
            "name": parts[3],
            "family_code": parts[7] if len(parts) > 7 else "",
            "vat_code": parts[8] if len(parts) > 8 else "",
            "duration_minutes": duration_minutes,
            "price_regular": round(price_regular, 2),
            "price_holiday": round(price_holiday, 2),
        }
    return out


def parse_lookup_table(path: Path) -> Dict[str, Dict[str, str]]:
    data = path.read_bytes()
    rec_len = int(data[7:11].decode("ascii"))
    offset = rec_len
    total = max(0, (len(data) - offset) // rec_len)
    out: Dict[str, Dict[str, str]] = {}
    for i in range(total):
        chunk = data[offset + i * rec_len : offset + (i + 1) * rec_len]
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        if len(parts) < 2:
            continue
        code = parts[0].strip()
        if not code:
            continue
        out[code] = {
            "label": parts[1],
            "extra": parts[2] if len(parts) > 2 else "",
        }
    return out


def parse_service_prices(services_fic: Path) -> Dict[str, str]:
    data = services_fic.read_bytes()
    offset = 93
    rec = 93
    out: Dict[str, str] = {}
    total = max(0, (len(data) - offset) // rec)
    for i in range(total):
        chunk = data[offset + i * rec : offset + (i + 1) * rec]
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        if len(parts) < 4 or not parts[0].isdigit():
            continue
        out[parts[0].zfill(4)] = parts[3]
    return out


def parse_bundle_lines(forfait_fic: Path) -> Dict[str, Dict[str, object]]:
    data = forfait_fic.read_bytes()
    offset = 169
    rec = 169
    bundles: Dict[str, Dict[str, object]] = {}
    total = max(0, (len(data) - offset) // rec)
    for i in range(total):
        chunk = data[offset + i * rec : offset + (i + 1) * rec]
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        if len(parts) < 3 or not parts[0].isdigit():
            continue
        code = parts[0].zfill(4)
        name = parts[1]
        service_codes = [p for p in parts[3:] if p.isdigit() and len(p) == 4]
        item_prices: List[float] = []
        for idx in range(len(service_codes)):
            pos = 89 + idx * 8
            if pos + 8 > len(chunk):
                item_prices.append(0.0)
                continue
            value = struct.unpack("<d", chunk[pos : pos + 8])[0]
            if not (0 <= value <= 5000):
                value = 0.0
            item_prices.append(round(value, 2))
        bundles[code] = {
            "name": name,
            "service_codes": service_codes,
            "item_prices": item_prices,
            "total_price": round(sum(item_prices), 2),
        }
    return bundles


def parse_bundle_prices(forfaits_fic: Path) -> Dict[str, Dict[str, object]]:
    data = forfaits_fic.read_bytes()
    offset = 125
    rec = 125
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    total = max(0, (len(data) - offset) // rec)
    for i in range(total):
        chunk = data[offset + i * rec : offset + (i + 1) * rec]
        parts = [p.decode("latin-1", "replace").strip() for p in chunk.split(b"\x00") if p.strip()]
        # Layout FORFAITS.FIC:
        # parts[0] -> technical row id, parts[1] -> actual bundle code
        if len(parts) < 5 or not parts[1].isdigit():
            continue
        code = parts[1].zfill(4)
        valid_from = parts[4] if len(parts) > 4 and parts[4].isdigit() else ""
        price = struct.unpack("<d", chunk[56:64])[0]
        if not (0 <= price <= 5000):
            price = 0.0
        grouped[code].append({"name": parts[3], "valid_from": valid_from, "price": round(price, 2)})

    out: Dict[str, Dict[str, object]] = {}
    for code, versions in grouped.items():
        versions.sort(key=lambda item: str(item.get("valid_from", "")))
        # Some snapshots contain temporary 0.0 prices; keep latest non-zero if available.
        non_zero_versions = [item for item in versions if float(item.get("price", 0.0)) > 0]
        out[code] = non_zero_versions[-1] if non_zero_versions else versions[-1]
    return out


def generate_catalog(input_dir: Path, output_ts: Path, output_csv_dir: Path) -> None:
    service_catalog = parse_service_catalog(input_dir / "SERVICE.FIC")
    service_prices = parse_service_prices(input_dir / "SERVICES.FIC")
    bundle_lines = parse_bundle_lines(input_dir / "FORFAIT.FIC")
    bundle_prices = parse_bundle_prices(input_dir / "FORFAITS.FIC")
    service_types = parse_lookup_table(input_dir / "PTYPSERV.FIC")
    families = parse_lookup_table(input_dir / "PFAMILLE.FIC")
    groups = parse_lookup_table(input_dir / "REGROUPE.FIC")
    esthetic_types = parse_lookup_table(input_dir / "ESTHETIQ.FIC")
    vat_codes = parse_lookup_table(input_dir / "TVA.FIC")
    client_types = parse_lookup_table(input_dir / "PTYPECL.FIC")

    sorted_codes = sorted(service_catalog.keys())
    service_id_by_code = {code: idx + 1 for idx, code in enumerate(sorted_codes)}

    services = []
    prices = []
    for code in sorted_codes:
        row = service_catalog[code]
        services.append(
            {
                "id": service_id_by_code[code],
                "code": code,
                "name": row["name"],
                "duration_minutes": row["duration_minutes"],
            }
        )
        prices.append(
            {
                "id": len(prices) + 1,
                "salon_id": 1,
                "service_id": service_id_by_code[code],
                "price": float(row["price_regular"]),
            }
        )

    bundles = []
    for code in sorted(bundle_lines.keys()):
        line = bundle_lines[code]
        service_codes = [c for c in line["service_codes"] if c in service_id_by_code]
        service_prices_in_bundle = line.get("item_prices", [])
        items = []
        for idx, service_code in enumerate(service_codes):
            override_price = float(service_prices_in_bundle[idx]) if idx < len(service_prices_in_bundle) else 0.0
            item = {"service_id": service_id_by_code[service_code]}
            if override_price > 0:
                item["override_price"] = override_price
            items.append(item)

        resolved_price = round(
            sum(
                float(service_prices_in_bundle[idx]) if idx < len(service_prices_in_bundle) and float(service_prices_in_bundle[idx]) > 0
                else float(service_catalog[service_code]["price_regular"])
                for idx, service_code in enumerate(service_codes)
            ),
            2,
        )
        bundles.append(
            {
                "id": len(bundles) + 1,
                "salon_id": 1,
                "code": code,
                "name": line["name"],
                "price": resolved_price,
                "items": items,
            }
        )

    output_csv_dir.mkdir(parents=True, exist_ok=True)
    with (output_csv_dir / "services_import.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "service_code",
                "name",
                "service_type_code",
                "service_type_label",
                "grouping_code",
                "grouping_label",
                "family_code",
                "family_label",
                "vat_code",
                "vat_label",
                "duration_minutes",
                "price",
                "price_holiday",
                "legacy_services_price_raw",
            ],
        )
        writer.writeheader()
        for row in services:
            code = row["code"]
            meta = service_catalog[code]
            service_type_label = service_types.get(meta["service_type_code"], {}).get("label", "")
            grouping_label = groups.get(meta["grouping_code"], {}).get("label", "")
            family_meta = families.get(meta["family_code"], {}) or families.get(
                str(meta["family_code"]).zfill(2), {}
            )
            family_label = family_meta.get("label", "")
            vat_label = vat_codes.get(meta["vat_code"], {}).get("label", "")
            writer.writerow(
                {
                    "service_code": code,
                    "name": row["name"],
                    "service_type_code": meta["service_type_code"],
                    "service_type_label": service_type_label,
                    "grouping_code": meta["grouping_code"],
                    "grouping_label": grouping_label,
                    "family_code": meta["family_code"],
                    "family_label": family_label,
                    "vat_code": meta["vat_code"],
                    "vat_label": vat_label,
                    "duration_minutes": meta["duration_minutes"],
                    "price": meta["price_regular"],
                    "price_holiday": meta["price_holiday"],
                    "legacy_services_price_raw": service_prices.get(code, ""),
                }
            )

    with (output_csv_dir / "bundles_import.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "bundle_code",
                "name",
                "price",
                "price_source",
                "forfait_total_price",
                "forfaits_price",
                "sum_of_services",
                "item_count",
            ],
        )
        writer.writeheader()
        for row in bundles:
            line = bundle_lines[row["code"]]
            service_codes = [c for c in line["service_codes"] if c in service_id_by_code]
            sum_of_services = round(sum(float(service_catalog[c]["price_regular"]) for c in service_codes), 2)
            forfaits_price = float(bundle_prices.get(row["code"], {}).get("price", 0.0))
            forfait_total_price = float(line.get("total_price", 0.0))
            writer.writerow(
                {
                    "bundle_code": row["code"],
                    "name": row["name"],
                    "price": row["price"],
                    "price_source": "forfait_fic_items",
                    "forfait_total_price": forfait_total_price,
                    "forfaits_price": forfaits_price,
                    "sum_of_services": sum_of_services,
                    "item_count": len(row["items"]),
                }
            )

    payload = {
        "legacyServices": services,
        "legacyPriceListItems": prices,
        "legacyBundles": bundles,
        "legacyDictionaries": {
            "serviceTypes": [{"code": k, "label": v.get("label", ""), "extra": v.get("extra", "")} for k, v in sorted(service_types.items())],
            "families": [{"code": k, "label": v.get("label", ""), "extra": v.get("extra", "")} for k, v in sorted(families.items())],
            "groups": [{"code": k, "label": v.get("label", ""), "extra": v.get("extra", "")} for k, v in sorted(groups.items())],
            "estheticTypes": [{"code": k, "label": v.get("label", ""), "extra": v.get("extra", "")} for k, v in sorted(esthetic_types.items())],
            "vatCodes": [{"code": k, "label": v.get("label", ""), "extra": v.get("extra", "")} for k, v in sorted(vat_codes.items())],
            "clientTypes": [{"code": k, "label": v.get("label", ""), "extra": v.get("extra", "")} for k, v in sorted(client_types.items())],
        },
        "legacyServiceMetaByCode": {
            code: {
                "service_type_code": meta["service_type_code"],
                "service_type_label": service_types.get(meta["service_type_code"], {}).get("label", ""),
                "grouping_code": meta["grouping_code"],
                "grouping_label": groups.get(meta["grouping_code"], {}).get("label", ""),
                "family_code": meta["family_code"],
                "family_label": (families.get(meta["family_code"], {}) or families.get(str(meta["family_code"]).zfill(2), {})).get("label", ""),
                "vat_code": meta["vat_code"],
                "vat_label": vat_codes.get(meta["vat_code"], {}).get("label", ""),
                "duration_minutes": meta["duration_minutes"],
                "price_regular": meta["price_regular"],
                "price_holiday": meta["price_holiday"],
            }
            for code, meta in service_catalog.items()
        },
    }

    output_ts.parent.mkdir(parents=True, exist_ok=True)
    output_ts.write_text(
        "import { BundleCatalog, PriceListItem, ServiceCatalogItem } from '../types'\n\n"
        f"export const legacyServices: ServiceCatalogItem[] = {json.dumps(payload['legacyServices'], ensure_ascii=False)}\n\n"
        f"export const legacyPriceListItems: PriceListItem[] = {json.dumps(payload['legacyPriceListItems'], ensure_ascii=False)}\n\n"
        f"export const legacyBundles: BundleCatalog[] = {json.dumps(payload['legacyBundles'], ensure_ascii=False)}\n",
        encoding="utf-8",
    )
    with (output_csv_dir / "legacy_dictionaries.json").open("w", encoding="utf-8") as f:
        json.dump(payload["legacyDictionaries"], f, ensure_ascii=False, indent=2)
    with (output_csv_dir / "legacy_service_meta_by_code.json").open("w", encoding="utf-8") as f:
        json.dump(payload["legacyServiceMetaByCode"], f, ensure_ascii=False, indent=2)

    print(f"services={len(services)} bundles={len(bundles)}")
    print(f"ts={output_ts}")
    print(f"csv={output_csv_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import legacy FIC/NDX catalogs to frontend mock data.")
    parser.add_argument("--input-dir", required=True, help="Directory with SERVICE.FIC, SERVICES.FIC, FORFAIT.FIC, FORFAITS.FIC")
    parser.add_argument(
        "--output-ts",
        default=str(Path("frontend/src/mocks/legacyImportedCatalog.ts")),
        help="Target TS file with generated arrays",
    )
    parser.add_argument(
        "--output-csv-dir",
        default=str(Path("tmp/legacy_export")),
        help="Output directory for helper CSV files",
    )
    args = parser.parse_args()

    generate_catalog(Path(args.input_dir), Path(args.output_ts), Path(args.output_csv_dir))


if __name__ == "__main__":
    main()
