#!/usr/bin/env python3
"""Review manual geographic scope tanpa mengubah event, kategori, atau relasi."""

import argparse
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import fix_event_relation_candidates as rel
from scripts import fix_geographic_scope as scope_fix
from scripts import pilot_collect_official_geohazard as pilot

FIX_PREFIX = "FIX-GEOGRAPHIC-REVIEW-"
ALL_TABLES = list(scope_fix.ALL_TABLES)
EXPECTED_RELATION_IDS = set(scope_fix.EXPECTED_RELATION_IDS)
SCOPE_CHANGE_FIELDS = set(scope_fix.SCOPE_CHANGE_FIELDS)
CAVEAT = (
    "Bbox pilot bukan batas wilayah nasional; coordinate_status "
    "source_coordinate tidak dinaikkan menjadi verified."
)
INVARIANT_CHECK_KEYS = (
    "event_count_unchanged",
    "event_ids_unchanged",
    "event_table_unchanged",
    "no_event_deleted",
    "no_merge",
    "event_location_ids_unchanged",
    "event_location_only_scope_fields_changed",
    "all_status_changes_logged",
    "no_unlogged_location_changes",
    "change_log_append_only",
    "category_table_unchanged",
    "category_names_unchanged",
    "category_scope_unchanged",
    "event_relation_table_unchanged",
    "fix02_relations_preserved",
    "raw_payload_table_unchanged",
    "raw_payload_files_unchanged",
    "baseline_unchanged",
    "source_fix_unchanged",
    "source_coordinate_still_unverified",
)
REVIEWED_UNKNOWN_IDS = {
    "EVT-BMKG-8102A3842AA3",
    "EVT-BMKG-9926ADFBE909",
    "EVT-BMKG-72D9473D8378",
    "EVT-BMKG-FFB357F335AE",
    "EVT-BMKG-8F1F74FF387A",
    "EVT-BMKG-9C6C2E535D8B",
    "EVT-BMKG-608A37F640B2",
    "EVT-BMKG-43C1A2818383",
    "EVT-BMKG-B2A5A39AE099",
    "EVT-BMKG-FC99150BA61F",
    "EVT-USGS-7000tusv",
}
REVIEW_DECISIONS = {
    "EVT-BMKG-8102A3842AA3": {
        "decision": "tidak_diketahui",
        "confidence": "high",
        "basis": "episentrum_laut_tanpa_batas_nasional",
        "rationale": (
            "Raw BMKG menyatakan pusat gempa berada di laut 169 km "
            "BaratLaut Tanimbar dan USGS menamai lokasi Banda Sea. Titik "
            "laut tidak dapat ditetapkan sebagai Indonesia tanpa polygon "
            "batas; Tanimbar/Saumlaki adalah rujukan/daerah terdampak, "
            "bukan bukti titik epicenter."
        ),
    },
    "EVT-BMKG-9926ADFBE909": {
        "decision": "tidak_diketahui",
        "confidence": "medium",
        "basis": "tanpa_penanda_darat_laut_tanpa_batas_nasional",
        "rationale": (
            "Lokasi resmi hanya menyebut 139 km BaratLaut Tual-Maluku, "
            "tanpa penanda eksplisit di darat atau di laut. Jarak jauh dan "
            "tidak ada polygon batas nasional; Tual adalah toponimi "
            "rujukan, bukan bukti titik epicenter berada di Indonesia."
        ),
    },
    "EVT-BMKG-72D9473D8378": {
        "decision": "tidak_diketahui",
        "confidence": "high",
        "basis": "episentrum_darat_dekat_perbatasan_tanpa_batas_nasional",
        "rationale": (
            "Raw BMKG menyatakan pusat gempa di darat 153 km tenggara "
            "Oksibil. Penanda darat tidak membuktikan negara karena titik "
            "berada di luar bbox pilot dan dekat perbatasan Indonesia-PNG; "
            "Boven Digoel, Jayapura, dan Merauke adalah daerah yang "
            "merasakan, bukan bukti lokasi epicenter."
        ),
    },
    "EVT-BMKG-FFB357F335AE": {
        "decision": "tidak_diketahui",
        "confidence": "high",
        "basis": "episentrum_laut_tanpa_batas_nasional",
        "rationale": (
            "Raw BMKG menyatakan pusat gempa di laut 60 km baratlaut "
            "Larat-Kepulauan Tanimbar, sementara location_name FIX 03 "
            "menyebut 201 km BaratLaut Tanimbar. Keduanya merujuk laut dan "
            "tidak ada polygon batas nasional untuk menetapkan status."
        ),
    },
    "EVT-BMKG-8F1F74FF387A": {
        "decision": "tidak_diketahui",
        "confidence": "medium",
        "basis": "tanpa_penanda_darat_laut_tanpa_batas_nasional",
        "rationale": (
            "Lokasi resmi hanya menyebut 187 km BaratLaut Tahuna-Kepulauan "
            "Sangihe-Sulawesi Utara, tanpa penanda eksplisit di darat atau "
            "di laut. Jarak jauh dan tidak ada polygon batas nasional."
        ),
    },
    "EVT-BMKG-9C6C2E535D8B": {
        "decision": "tidak_diketahui",
        "confidence": "medium",
        "basis": "tanpa_penanda_darat_laut_tanpa_batas_nasional",
        "rationale": (
            "Lokasi resmi hanya menyebut 221 km BaratLaut Pulau Karatung-"
            "Sulawesi Utara, tanpa penanda eksplisit di darat atau di laut. "
            "Jarak jauh dan tidak ada polygon batas nasional."
        ),
    },
    "EVT-BMKG-608A37F640B2": {
        "decision": "tidak_diketahui",
        "confidence": "high",
        "basis": "episentrum_laut_tanpa_batas_nasional",
        "rationale": (
            "Raw BMKG menyatakan pusat gempa berada di laut 137 km selatan "
            "Gunungkidul. Titik laut tidak dapat ditetapkan sebagai "
            "Indonesia tanpa polygon batas; Gunungkidul adalah toponimi "
            "rujukan, bukan bukti titik epicenter."
        ),
    },
    "EVT-BMKG-43C1A2818383": {
        "decision": "tidak_diketahui",
        "confidence": "medium",
        "basis": "tanpa_penanda_darat_laut_tanpa_batas_nasional",
        "rationale": (
            "Lokasi resmi hanya menyebut 62 km TimurLaut Maluku Barat Daya, "
            "tanpa penanda eksplisit di darat atau di laut. Jarak melewati "
            "ambang dekat classifier dan tidak ada polygon batas nasional."
        ),
    },
    "EVT-BMKG-B2A5A39AE099": {
        "decision": "tidak_diketahui",
        "confidence": "high",
        "basis": "episentrum_laut_tanpa_batas_nasional",
        "rationale": (
            "Raw BMKG menyatakan pusat gempa berada di laut 13 km tenggara "
            "Bahodopi. Titik laut tidak dapat ditetapkan sebagai Indonesia "
            "tanpa polygon batas; Morowali adalah daerah yang merasakan, "
            "bukan bukti lokasi epicenter."
        ),
    },
    "EVT-BMKG-FC99150BA61F": {
        "decision": "tidak_diketahui",
        "confidence": "high",
        "basis": "episentrum_laut_tanpa_batas_nasional",
        "rationale": (
            "Raw BMKG menyatakan pusat gempa berada di laut 97 km barat "
            "Kodi, Sumba Barat Daya. Titik laut tidak dapat ditetapkan "
            "sebagai Indonesia tanpa polygon batas; Kodi/Sumba Barat Daya "
            "adalah toponimi rujukan dan Sumbawa adalah daerah terdampak."
        ),
    },
    "EVT-USGS-7000tusv": {
        "decision": "tidak_diketahui",
        "confidence": "high",
        "basis": "episentrum_laut_tanpa_batas_nasional",
        "rationale": (
            "USGS menamai lokasi Banda Sea dan BMKG counterpart menyatakan "
            "pusat gempa di laut. Titik laut tidak dapat ditetapkan sebagai "
            "Indonesia tanpa polygon batas nasional."
        ),
    },
}


def table_path(base, name):
    return base / "tables" / f"{name}.csv"


def latest_geographic_scope_fix():
    fixes = sorted(
        path
        for path in (pilot.PILOT_ROOT / "fixes").glob(
            "FIX-GEOGRAPHIC-SCOPE-*"
        )
        if path.is_dir()
    )
    return fixes[-1] if fixes else None


def latest_source_fix():
    fix = latest_geographic_scope_fix()
    if fix is None:
        raise RuntimeError("Tidak menemukan output FIX 03 geographic scope.")
    return fix


def load_all_tables(base):
    return {
        name: pilot.read_csv(table_path(base, name))
        for name in ALL_TABLES
    }


def _parse_bmkg_records(path):
    root = ET.parse(path).getroot()
    records = []
    for node in root.findall("gempa"):
        record = {
            child.tag: (child.text or "").strip()
            for child in node
            if child.tag != "point"
        }
        point = node.find("point/coordinates")
        record["coordinates"] = (
            (point.text or "").strip() if point is not None else ""
        )
        records.append(record)
    return records


def _parse_usgs_records(path):
    namespace = {
        "a": "http://www.w3.org/2005/Atom",
        "georss": "http://www.georss.org/georss",
    }
    root = ET.parse(path).getroot()
    records = []
    for entry in root.findall("a:entry", namespace):
        summary_node = entry.find("a:summary", namespace)
        point_node = entry.find("georss:point", namespace)
        records.append(
            {
                "id": entry.findtext("a:id", default="", namespaces=namespace),
                "title": entry.findtext(
                    "a:title", default="", namespaces=namespace
                ),
                "updated": entry.findtext(
                    "a:updated", default="", namespaces=namespace
                ),
                "summary": (
                    (summary_node.text or "").strip()
                    if summary_node is not None
                    else ""
                ),
                "point": (
                    (point_node.text or "").strip()
                    if point_node is not None
                    else ""
                ),
            }
        )
    return records


def _coord_matches(text, latitude, longitude):
    try:
        lat_text, lon_text = [
            item.strip() for item in str(text).split(",", 1)
        ]
        return (
            abs(float(lat_text) - float(latitude)) <= 0.001
            and abs(float(lon_text) - float(longitude)) <= 0.001
        )
    except (TypeError, ValueError):
        return False


def _bmkg_record_matches(record, event_time, latitude, longitude):
    return (
        record.get("DateTime", "") == event_time
        and _coord_matches(
            record.get("coordinates", ""), latitude, longitude
        )
    )


def _record_matches(document, record, event_time, latitude, longitude):
    source_id = document["document_source_id"]
    if source_id.startswith("bmkg_"):
        return _bmkg_record_matches(
            record, event_time, latitude, longitude
        )
    if source_id == "usgs_m45":
        external_id = str(document.get("document_external_id", ""))
        return bool(external_id) and str(record.get("id", "")).endswith(
            f":{external_id}"
        )
    return False


def _raw_location_statement(source_id, record):
    if source_id.startswith("bmkg_"):
        return record.get("Wilayah", "")
    return record.get("title", "")


def _raw_felt_statement(source_id, record):
    if source_id.startswith("bmkg_"):
        return record.get("Dirasakan", "")
    return ""


def _land_sea_evidence(statements):
    text = " ".join(statements).lower()
    if re.search(r"\bdi\s+laut\b|\bsea\b|\bocean\b", text):
        return "laut"
    if re.search(r"\bdi\s+darat\b|\bdarat\b", text):
        return "darat"
    return "tidak_eksplisit"


def _build_event_evidence(
    tables, event, location, event_time, documents, raw_payload_by_id
):
    document_by_id = {
        row["document_id"]: row for row in tables["document"]
    }
    raw_records = []
    location_statements = []
    felt_statements = []
    seen_records = set()
    processed_raw_payload_ids = set()

    def add_record(source_id, document_id, raw_payload_id, record):
        statement = _raw_location_statement(source_id, record)
        felt = _raw_felt_statement(source_id, record)
        key = (
            source_id,
            raw_payload_id,
            record.get("DateTime", "") or record.get("id", ""),
            statement,
            felt,
        )
        if key in seen_records:
            return
        seen_records.add(key)
        if statement:
            location_statements.append(
                {
                    "source_id": source_id,
                    "document_id": document_id,
                    "raw_payload_id": raw_payload_id,
                    "statement": statement,
                }
            )
        if felt:
            felt_statements.append(
                {
                    "source_id": source_id,
                    "document_id": document_id,
                    "raw_payload_id": raw_payload_id,
                    "statement": felt,
                }
            )
        raw_records.append(
            {
                "source_id": source_id,
                "document_id": document_id,
                "raw_payload_id": raw_payload_id,
                "fields": record,
            }
        )

    for link in documents:
        document = document_by_id[link["document_id"]]
        raw_payload = raw_payload_by_id[document["document_raw_payload_id"]]
        path = ROOT / raw_payload["raw_payload_path"]
        source_id = document["document_source_id"]
        processed_raw_payload_ids.add(raw_payload["raw_payload_id"])
        if source_id.startswith("bmkg_"):
            candidates = _parse_bmkg_records(path)
        elif source_id == "usgs_m45":
            candidates = _parse_usgs_records(path)
        else:
            candidates = []
        matched = [
            record
            for record in candidates
            if _record_matches(
                document,
                record,
                event_time,
                location["latitude"],
                location["longitude"],
            )
        ]
        if not matched:
            raise ValueError(
                f"Record raw tidak ditemukan untuk {event['event_id']} "
                f"di {document['document_id']}."
            )
        for record in matched:
            add_record(
                source_id,
                document["document_id"],
                raw_payload["raw_payload_id"],
                record,
            )

    for raw_payload in raw_payload_by_id.values():
        raw_payload_id = raw_payload["raw_payload_id"]
        source_id = raw_payload["raw_payload_source_id"]
        if (
            raw_payload_id in processed_raw_payload_ids
            or not source_id.startswith("bmkg_")
        ):
            continue
        path = ROOT / raw_payload["raw_payload_path"]
        for record in _parse_bmkg_records(path):
            if _bmkg_record_matches(
                record,
                event_time,
                location["latitude"],
                location["longitude"],
            ):
                add_record(source_id, "", raw_payload_id, record)

    if not location_statements:
        raise ValueError(
            f"Tidak ada bukti lokasi raw untuk {event['event_id']}."
        )
    return {
        "official_documents": [
            {
                "document_id": link["document_id"],
                "source_id": document_by_id[link["document_id"]][
                    "document_source_id"
                ],
                "is_primary": link["is_primary"],
                "document_title": document_by_id[link["document_id"]][
                    "document_title"
                ],
                "document_external_id": document_by_id[link["document_id"]][
                    "document_external_id"
                ],
                "raw_payload_id": document_by_id[link["document_id"]][
                    "document_raw_payload_id"
                ],
            }
            for link in documents
        ],
        "raw_location_statements": location_statements,
        "raw_felt_statements": felt_statements,
        "raw_records": raw_records,
        "land_sea_evidence": _land_sea_evidence(
            [item["statement"] for item in location_statements]
        ),
    }


def _format_statements(items):
    return " | ".join(
        f"{item['source_id']}: {item['statement']}" for item in items
    )


def _review_change_row(review_row, generated_at):
    change_id = "CHG-GEO-REV-" + pilot.sha256_text(
        "|".join(
            [
                review_row["event_location_id"],
                review_row["old_is_inside_indonesia"],
                review_row["review_decision"],
                review_row["review_basis"],
            ]
        )
    )[:16].upper()
    return {
        "change_id": change_id,
        "target_type": "event_location",
        "target_id": review_row["event_location_id"],
        "change_type": "update",
        "changed_at": generated_at,
        "changed_by": "system_fix_geographic_review",
        "field_name": "is_inside_indonesia",
        "old_value": review_row["old_is_inside_indonesia"],
        "new_value": review_row["review_decision"],
        "change_reason": (
            f"Review manual mengubah geographic scope dari "
            f"{review_row['old_is_inside_indonesia']} menjadi "
            f"{review_row['review_decision']}; "
            f"basis={review_row['review_basis']}; "
            f"{review_row['review_rationale']} Kategori dan category_scope "
            "tidak diubah; tidak merge/hapus; koordinat sumber belum "
            "diverifikasi."
        ),
        "evidence_ref": (
            f"event:{review_row['event_id']};"
            f"event_location:{review_row['event_location_id']};"
            f"documents:{review_row['evidence_document_ids']};"
            f"raw_payloads:{review_row['evidence_raw_payload_ids']}"
        ),
        "schema_version": pilot.SCHEMA_VERSION,
        "manual_review": "ya",
    }


def build_reviews(source_tables, generated_at):
    events = {row["event_id"]: row for row in source_tables["event"]}
    event_times = {
        row["event_id"]: row["event_time"]
        for row in source_tables["event_time"]
    }
    links_by_event = {}
    for link in source_tables["document_event_link"]:
        links_by_event.setdefault(link["event_id"], []).append(link)
    for links in links_by_event.values():
        links.sort(
            key=lambda link: (
                link["is_primary"] != "ya",
                link["document_id"],
            )
        )
    raw_payload_by_id = {
        row["raw_payload_id"]: row for row in source_tables["raw_payload"]
    }

    output_locations = []
    review_rows = []
    evidence_payload = []
    new_changes = []
    for location in source_tables["event_location"]:
        event_id = location["event_id"]
        output_location = dict(location)
        if event_id not in REVIEW_DECISIONS:
            output_locations.append(output_location)
            continue

        decision = REVIEW_DECISIONS[event_id]
        new_flag = decision["decision"]
        if new_flag not in scope_fix.geo.VALID_FLAGS:
            raise ValueError(
                f"Keputusan review tidak valid untuk {event_id}: {new_flag!r}"
            )
        event = events[event_id]
        evidence = _build_event_evidence(
            source_tables,
            event,
            location,
            event_times[event_id],
            links_by_event.get(event_id, []),
            raw_payload_by_id,
        )
        changed = location["is_inside_indonesia"] != new_flag
        review_row = {
            "event_id": event_id,
            "event_location_id": location["event_location_id"],
            "event_title": event["event_title"],
            "event_primary_source_id": event["event_primary_source_id"],
            "location_name": location["location_name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "coordinate_status": location["coordinate_status"],
            "old_is_inside_indonesia": location["is_inside_indonesia"],
            "review_decision": new_flag,
            "new_is_inside_indonesia": new_flag,
            "status_changed": str(changed),
            "review_confidence": decision["confidence"],
            "review_basis": decision["basis"],
            "review_rationale": decision["rationale"],
            "land_sea_evidence": evidence["land_sea_evidence"],
            "raw_location_statement": _format_statements(
                evidence["raw_location_statements"]
            ),
            "raw_felt_statement": _format_statements(
                evidence["raw_felt_statements"]
            ),
            "evidence_document_ids": ";".join(
                item["document_id"]
                for item in evidence["official_documents"]
            ),
            "evidence_raw_payload_ids": ";".join(
                sorted(
                    {
                        item["raw_payload_id"]
                        for item in (
                            evidence["raw_location_statements"]
                            + evidence["raw_felt_statements"]
                        )
                    }
                )
            ),
            "evidence_summary": (
                f"{len(evidence['official_documents'])} dokumen resmi; "
                f"{len(evidence['raw_records'])} record raw cocok; "
                f"penanda darat/laut={evidence['land_sea_evidence']}."
            ),
            "change_id": "",
            "manual_review": "ya",
            "caveat": CAVEAT,
        }
        if changed:
            change_row = _review_change_row(review_row, generated_at)
            review_row["change_id"] = change_row["change_id"]
            new_changes.append(change_row)
            output_location["is_inside_indonesia"] = new_flag
            output_location["location_evidence"] = scope_fix._append_text(
                location["location_evidence"],
                (
                    f"geographic_review={new_flag}; "
                    f"review_basis={decision['basis']}; "
                    f"review_confidence={decision['confidence']}; "
                    f"review_rule=manual_fix04"
                ),
            )
            output_location["location_notes"] = scope_fix._append_text(
                location["location_notes"],
                (
                    "Keputusan review manual FIX 04; koordinat sumber belum "
                    "diverifikasi."
                ),
            )
        review_rows.append(review_row)
        evidence_payload.append(
            {
                "event_id": event_id,
                "event_location_id": location["event_location_id"],
                "event_title": event["event_title"],
                "event_primary_source_id": event["event_primary_source_id"],
                "location_name": location["location_name"],
                "coordinate": [location["latitude"], location["longitude"]],
                "coordinate_status": location["coordinate_status"],
                "old_is_inside_indonesia": location["is_inside_indonesia"],
                "review_decision": new_flag,
                "new_is_inside_indonesia": new_flag,
                "status_changed": changed,
                "review_confidence": decision["confidence"],
                "review_basis": decision["basis"],
                "review_rationale": decision["rationale"],
                "official_documents": evidence["official_documents"],
                "raw_location_statements": evidence["raw_location_statements"],
                "raw_felt_statements": evidence["raw_felt_statements"],
                "raw_records": evidence["raw_records"],
                "evidence_summary": review_row["evidence_summary"],
                "event_title_used_as_location_evidence": False,
                "caveat": CAVEAT,
            }
        )
        output_locations.append(output_location)

    return output_locations, new_changes, review_rows, evidence_payload


def build_validation(
    review_rows,
    source_tables,
    output_tables,
    new_changes,
    checks,
    collector_validation,
):
    rows = []

    def add(rule_id, severity, records, status, detail, refs=None):
        rows.append(
            {
                "rule_id": rule_id,
                "severity": severity,
                "entity": "event_location",
                "records_checked": records,
                "status": status,
                "detail": detail,
                "record_refs": ";".join(refs or []),
            }
        )

    reviewed_ids = {row["event_id"] for row in review_rows}
    missing = sorted(REVIEWED_UNKNOWN_IDS - reviewed_ids)
    extra = sorted(reviewed_ids - REVIEWED_UNKNOWN_IDS)
    add(
        "R-GEO-07",
        "P0",
        len(review_rows),
        "lulus" if not missing and not extra else "gagal",
        (
            "Seluruh 11 event tidak_diketahui dari FIX 03 direview tepat "
            "sekali; tidak ada event target yang hilang atau ditambah."
        ),
        missing + extra,
    )

    invalid_decisions = [
        row["event_id"]
        for row in review_rows
        if row["review_decision"] not in scope_fix.geo.VALID_FLAGS
    ]
    unlogged_changes = [
        row["event_id"]
        for row in review_rows
        if row["status_changed"] == "True" and not row["change_id"]
    ]
    logged_targets = {
        row["target_id"] for row in new_changes
        if row["target_type"] == "event_location"
    }
    bad_log_targets = [
        row["event_location_id"]
        for row in review_rows
        if row["status_changed"] == "True"
        and row["event_location_id"] not in logged_targets
    ]
    add(
        "R-GEO-08",
        "P0",
        len(review_rows),
        (
            "lulus"
            if not invalid_decisions
            and not unlogged_changes
            and not bad_log_targets
            else "gagal"
        ),
        (
            "Setiap keputusan review memakai vocabulary sah dan setiap "
            "perubahan status memiliki baris change_log."
        ),
        invalid_decisions + unlogged_changes + bad_log_targets,
    )

    incomplete_evidence = [
        row["event_id"]
        for row in review_rows
        if not row["raw_location_statement"]
        or not row["evidence_document_ids"]
        or not row["review_rationale"]
        or not row["review_basis"]
    ]
    add(
        "R-GEO-09",
        "P1",
        len(review_rows),
        "lulus" if not incomplete_evidence else "perlu_review",
        (
            "Setiap review memiliki bukti raw/dokumen resmi, basis, dan "
            "alasan; judul event tidak dipakai sebagai bukti lokasi."
        ),
        incomplete_evidence,
    )

    unchanged_failures = [
        name
        for name in INVARIANT_CHECK_KEYS
        if not checks.get(name, False)
    ]
    add(
        "R-GEO-10",
        "P0",
        len(source_tables["event"]),
        "lulus" if not unchanged_failures else "gagal",
        (
            "Event, kategori, category_scope, relasi FIX 02, raw payload, "
            "baseline, dan koordinat sumber tetap."
        ),
        unchanged_failures,
    )

    unverified_failures = [
        row["event_id"]
        for row in output_tables["event_location"]
        if row["coordinate_status"] == "verified"
        or row["coordinate_verified_at"]
        or row["coordinate_verified_by"]
    ]
    add(
        "R-GEO-11",
        "P0",
        len(output_tables["event_location"]),
        "lulus" if not unverified_failures else "gagal",
        (
            "Review manual tidak menaikkan coordinate_status "
            "source_coordinate menjadi verified."
        ),
        unverified_failures,
    )

    loc_rule = next(
        (
            row
            for row in collector_validation
            if row["rule_id"] == "R-LOC-05"
        ),
        {},
    )
    add(
        "R-LOC-05",
        "P1",
        len(output_tables["event_location"]),
        loc_rule.get("status", "gagal"),
        (
            "Validator pilot menerima output FIX 04; flag scope konsisten "
            "dengan classifier dan tidak ada perubahan paksa."
        ),
        (
            []
            if loc_rule.get("status") == "lulus"
            else [loc_rule.get("record_refs", "R-LOC-05 gagal")]
        ),
    )
    return rows


def choose_output_dir(fix_id=""):
    base_id = fix_id or (
        FIX_PREFIX + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    candidate = pilot.PILOT_ROOT / "fixes" / base_id
    number = 2
    while candidate.exists():
        candidate = pilot.PILOT_ROOT / "fixes" / f"{base_id}-{number:02d}"
        number += 1
    return candidate


def write_fix(source_fix, output_dir, fix_id=None, generated_at=None):
    source_fix = Path(source_fix)
    output_dir = Path(output_dir)
    fix_id = fix_id or output_dir.name
    generated_at = generated_at or pilot.iso_utc()
    dictionary = pilot.load_dictionary()

    source_tables = load_all_tables(source_fix)
    source_table_hashes = {
        path.name: pilot.sha256_file(path)
        for path in sorted((source_fix / "tables").glob("*.csv"))
    }
    source_manifest_path = source_fix / "fix_manifest.json"
    source_manifest_sha256 = (
        pilot.sha256_file(source_manifest_path)
        if source_manifest_path.is_file()
        else ""
    )

    baseline_before = pilot.dataset_baseline.verify_dataset()
    events_before = rel.event_snapshot(
        source_tables, table_path(source_fix, "event")
    )
    locations_before = scope_fix.location_snapshot(
        source_tables, table_path(source_fix, "event_location")
    )
    categories_before = scope_fix.category_snapshot(
        source_tables, table_path(source_fix, "category")
    )
    relations_before = scope_fix.relation_snapshot(
        source_tables, table_path(source_fix, "event_relation")
    )
    raw_before = rel.raw_payload_snapshot(source_tables)
    scope_before = scope_fix.scope_counts(source_tables["event_location"])

    (
        output_locations,
        new_changes,
        review_rows,
        evidence_payload,
    ) = build_reviews(source_tables, generated_at)
    output_changes = list(source_tables["change_log"]) + new_changes

    output_tables_dir = output_dir / "tables"
    output_tables_dir.mkdir(parents=True, exist_ok=False)
    if new_changes:
        for path in sorted((source_fix / "tables").glob("*.csv")):
            if path.name in {"event_location.csv", "change_log.csv"}:
                continue
            shutil.copy2(path, output_tables_dir / path.name)
        pilot.write_csv(
            output_tables_dir / "event_location.csv",
            output_locations,
            dictionary["event_location"],
        )
        pilot.write_csv(
            output_tables_dir / "change_log.csv",
            output_changes,
            dictionary["change_log"],
        )
    else:
        for path in sorted((source_fix / "tables").glob("*.csv")):
            shutil.copy2(path, output_tables_dir / path.name)

    output_tables = load_all_tables(output_dir)
    output_table_hashes = {
        path.name: pilot.sha256_file(path)
        for path in sorted(output_tables_dir.glob("*.csv"))
    }
    events_after = rel.event_snapshot(
        output_tables, table_path(output_dir, "event")
    )
    locations_after = scope_fix.location_snapshot(
        output_tables, table_path(output_dir, "event_location")
    )
    categories_after = scope_fix.category_snapshot(
        output_tables, table_path(output_dir, "category")
    )
    relations_after = scope_fix.relation_snapshot(
        output_tables, table_path(output_dir, "event_relation")
    )
    raw_after = rel.raw_payload_snapshot(output_tables)
    baseline_after = pilot.dataset_baseline.verify_dataset()
    scope_after = scope_fix.scope_counts(output_tables["event_location"])

    source_table_hashes_after = {
        path.name: pilot.sha256_file(path)
        for path in sorted((source_fix / "tables").glob("*.csv"))
    }
    source_manifest_sha256_after = (
        pilot.sha256_file(source_manifest_path)
        if source_manifest_path.is_file()
        else ""
    )
    source_location_by_id = {
        row["event_location_id"]: row
        for row in source_tables["event_location"]
    }
    output_location_by_id = {
        row["event_location_id"]: row
        for row in output_tables["event_location"]
    }
    location_other_fields_equal = True
    for location_id, source_row in source_location_by_id.items():
        output_row = output_location_by_id.get(location_id)
        if output_row is None:
            location_other_fields_equal = False
            break
        for field, value in source_row.items():
            if field in SCOPE_CHANGE_FIELDS:
                continue
            if output_row.get(field) != value:
                location_other_fields_equal = False
                break
        if not location_other_fields_equal:
            break

    changed_location_ids = {
        row["event_location_id"]
        for row in review_rows
        if row["status_changed"] == "True"
    }
    change_rows_by_location = {
        row["target_id"]: row
        for row in new_changes
        if row["target_type"] == "event_location"
    }
    all_status_changes_logged = all(
        location_id in change_rows_by_location
        for location_id in changed_location_ids
    )
    no_unlogged_location_changes = (
        location_other_fields_equal
        and all_status_changes_logged
        and set(source_location_by_id) == set(output_location_by_id)
    )
    reviewed_ids = {row["event_id"] for row in review_rows}
    collector_validation = pilot.validate(
        output_tables, pilot.load_register(), output_dir
    )
    loc_rule = next(
        (
            row
            for row in collector_validation
            if row["rule_id"] == "R-LOC-05"
        ),
        {},
    )

    checks = {
        "event_count_unchanged": (
            events_before["count"] == events_after["count"]
        ),
        "event_ids_unchanged": events_before["ids"] == events_after["ids"],
        "event_table_unchanged": (
            events_before["event_csv_sha256"]
            == events_after["event_csv_sha256"]
        ),
        "no_event_deleted": set(events_after["ids"]).issuperset(
            events_before["ids"]
        ),
        "no_merge": (
            events_before["count"] == events_after["count"]
            and events_before["event_csv_sha256"]
            == events_after["event_csv_sha256"]
        ),
        "event_location_ids_unchanged": (
            locations_before["ids"] == locations_after["ids"]
        ),
        "event_location_only_scope_fields_changed": (
            location_other_fields_equal
        ),
        "all_status_changes_logged": all_status_changes_logged,
        "no_unlogged_location_changes": no_unlogged_location_changes,
        "reviewed_event_ids_complete": (
            reviewed_ids == REVIEWED_UNKNOWN_IDS
        ),
        "reviewed_events_were_unknown": all(
            row["old_is_inside_indonesia"] == "tidak_diketahui"
            for row in review_rows
        ),
        "review_decisions_valid": all(
            row["review_decision"] in scope_fix.geo.VALID_FLAGS
            for row in review_rows
        ),
        "review_evidence_present": all(
            row["raw_location_statement"]
            and row["evidence_document_ids"]
            and row["evidence_raw_payload_ids"]
            and row["review_rationale"]
            for row in review_rows
        ),
        "reviewed_event_count_expected": (
            len(review_rows) == len(REVIEWED_UNKNOWN_IDS)
        ),
        "change_log_append_only": (
            output_changes[: len(source_tables["change_log"])]
            == source_tables["change_log"]
        ),
        "change_log_unchanged": (
            len(output_changes) == len(source_tables["change_log"])
            and pilot.sha256_file(
                table_path(output_dir, "change_log")
            )
            == pilot.sha256_file(table_path(source_fix, "change_log"))
        ),
        "category_table_unchanged": (
            categories_before["category_csv_sha256"]
            == categories_after["category_csv_sha256"]
        ),
        "category_names_unchanged": (
            categories_before["category_names"]
            == categories_after["category_names"]
        ),
        "category_scope_unchanged": (
            categories_before["category_scopes"]
            == categories_after["category_scopes"]
        ),
        "event_relation_table_unchanged": (
            relations_before["event_relation_csv_sha256"]
            == relations_after["event_relation_csv_sha256"]
        ),
        "fix02_relations_preserved": (
            relations_before["ids"] == relations_after["ids"]
            and EXPECTED_RELATION_IDS.issubset(
                set(relations_after["ids"])
            )
        ),
        "raw_payload_table_unchanged": (
            source_table_hashes.get("raw_payload.csv")
            == output_table_hashes.get("raw_payload.csv")
        ),
        "raw_payload_files_unchanged": raw_before == raw_after,
        "baseline_unchanged": (
            baseline_before["sha256"] == baseline_after["sha256"]
            and baseline_after["sha256"]
            == pilot.dataset_baseline.DATASET_SHA256
        ),
        "source_fix_unchanged": (
            source_table_hashes == source_table_hashes_after
            and source_manifest_sha256 == source_manifest_sha256_after
        ),
        "scope_values_valid": all(
            row["is_inside_indonesia"] in scope_fix.geo.VALID_FLAGS
            for row in output_tables["event_location"]
        ),
        "source_coordinate_still_unverified": all(
            row["coordinate_status"] != "verified"
            and not row["coordinate_verified_at"]
            and not row["coordinate_verified_by"]
            for row in output_tables["event_location"]
        ),
        "collector_rule_loc05_passes": (
            loc_rule.get("status") == "lulus"
            and loc_rule.get("records_checked") == 20
        ),
    }
    checks["validation_no_failures"] = not any(
        row["severity"] == "P0" and row["status"] == "gagal"
        for row in build_validation(
            review_rows,
            source_tables,
            output_tables,
            new_changes,
            checks,
            collector_validation,
        )
    )

    validation = build_validation(
        review_rows,
        source_tables,
        output_tables,
        new_changes,
        checks,
        collector_validation,
    )
    review_fields = [
        "event_id",
        "event_location_id",
        "event_title",
        "event_primary_source_id",
        "location_name",
        "latitude",
        "longitude",
        "coordinate_status",
        "old_is_inside_indonesia",
        "review_decision",
        "new_is_inside_indonesia",
        "status_changed",
        "review_confidence",
        "review_basis",
        "review_rationale",
        "land_sea_evidence",
        "raw_location_statement",
        "raw_felt_statement",
        "evidence_document_ids",
        "evidence_raw_payload_ids",
        "evidence_summary",
        "change_id",
        "manual_review",
        "caveat",
    ]
    pilot.write_csv(
        output_dir / "geographic_review.csv",
        review_rows,
        review_fields,
    )
    pilot.write_json(
        output_dir / "geographic_review_evidence.json",
        evidence_payload,
    )
    validation_fields = [
        "rule_id",
        "severity",
        "entity",
        "records_checked",
        "status",
        "detail",
        "record_refs",
    ]
    pilot.write_csv(
        output_dir / "geographic_review_validation.csv",
        validation,
        validation_fields,
    )

    status_counts = Counter(
        row["review_decision"] for row in review_rows
    )
    manifest = {
        "fix_id": fix_id,
        "generated_at": generated_at,
        "source_fix": str(source_fix.relative_to(ROOT)).replace("\\", "/"),
        "source_fix_manifest_sha256": source_manifest_sha256,
        "source_tables_sha256": source_table_hashes,
        "output_tables_sha256": output_table_hashes,
        "baseline_before": baseline_before,
        "baseline_after": baseline_after,
        "raw_payload_before": raw_before,
        "raw_payload_after": raw_after,
        "events_before": events_before,
        "events_after": events_after,
        "event_locations_before": locations_before,
        "event_locations_after": locations_after,
        "categories_before": categories_before,
        "categories_after": categories_after,
        "relations_before": relations_before,
        "relations_after": relations_after,
        "counts": {
            "events_before": events_before["count"],
            "events_after": events_after["count"],
            "event_locations_before": locations_before["count"],
            "event_locations_after": locations_after["count"],
            "relations_before": relations_before["count"],
            "relations_after": relations_after["count"],
            "change_log_before": len(source_tables["change_log"]),
            "change_log_after": len(output_changes),
            "reviewed_events": len(review_rows),
            "status_changes": len(new_changes),
            "remaining_unknown": sum(
                1
                for row in output_tables["event_location"]
                if row["is_inside_indonesia"] == "tidak_diketahui"
            ),
        },
        "scope_counts_before": scope_before,
        "scope_counts_after": scope_after,
        "review_decision_counts": {
            key: status_counts.get(key, 0)
            for key in ["ya", "tidak", "tidak_diketahui"]
        },
        "review_changes": new_changes,
        "reviews": review_rows,
        "checks": checks,
        "validation": validation,
        "rules": {
            "geographic_field": "event_location.is_inside_indonesia",
            "geographic_vocabulary": sorted(scope_fix.geo.VALID_FLAGS),
            "reviewed_targets": sorted(REVIEWED_UNKNOWN_IDS),
            "review_policy": (
                "Review manual memakai raw payload resmi dan dokumen "
                "pendukung. Titik laut, titik dekat perbatasan, jarak jauh, "
                "atau lokasi tanpa penanda/batas yang cukup tetap "
                "tidak_diketahui. Judul event bukan bukti lokasi."
            ),
            "pilot_bbox_is_national_boundary": False,
            "coordinate_verification": (
                "Tidak dilakukan; coordinate_status tetap source_coordinate."
            ),
        },
        "schema_changes": {
            "applied": False,
            "reason": (
                "Field event_location.is_inside_indonesia, change_log, dan "
                "vocabulary sudah tersedia. Tidak ada field baru."
            ),
            "category_scope": (
                "Tidak diubah; category_scope tetap menilai kesesuaian "
                "kategori dengan cakupan proyek, bukan geographic scope."
            ),
        },
    }
    pilot.write_json(output_dir / "fix_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Review manual 11 event tidak_diketahui dari FIX 03 tanpa "
            "mengubah event, kategori, relasi, baseline, atau raw payload."
        )
    )
    parser.add_argument(
        "--source-fix",
        default=str(latest_source_fix()),
        help="Direktori FIX 03 atau snapshot turunan yang menjadi sumber.",
    )
    parser.add_argument(
        "--fix-id",
        default="",
        help="ID direktori fix; default memakai timestamp UTC.",
    )
    args = parser.parse_args()

    source_fix = Path(args.source_fix).resolve()
    output_dir = choose_output_dir(args.fix_id)
    manifest = write_fix(source_fix, output_dir)
    print(f"Fix ID: {manifest['fix_id']}")
    print(f"Output: {output_dir}")
    print(f"Reviews: {manifest['counts']['reviewed_events']}")
    print(f"Scope before: {manifest['scope_counts_before']}")
    print(f"Scope after: {manifest['scope_counts_after']}")
    print(f"Status changes: {manifest['counts']['status_changes']}")
    failed = [
        key for key, value in manifest["checks"].items() if not value
    ]
    print(f"Checks failed: {failed if failed else 'tidak ada'}")


if __name__ == "__main__":
    main()
