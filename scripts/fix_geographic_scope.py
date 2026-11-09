#!/usr/bin/env python3
"""Perbaiki geographic scope tanpa mengubah kategori, relasi, atau event."""

import argparse
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import geographic_scope as geo
from scripts import fix_event_relation_candidates as rel
from scripts import pilot_collect_official_geohazard as pilot

FIX_PREFIX = "FIX-GEOGRAPHIC-SCOPE-"
DEFAULT_SOURCE_FIX = rel.latest_event_relation_fix()
ALL_TABLES = [
    "source",
    "raw_payload",
    "document",
    "event",
    "event_time",
    "event_location",
    "event_attribute",
    "event_assertion",
    "category",
    "document_event_link",
    "location_mention",
    "verification",
    "event_relation",
    "change_log",
]
EXPECTED_RELATION_IDS = {
    "EREL-6947058A57B66894",
    "EREL-058FFADAE49A4801",
}
SCOPE_CHANGE_FIELDS = {
    "is_inside_indonesia",
    "location_evidence",
    "location_notes",
}


def table_path(base, name):
    return base / "tables" / f"{name}.csv"


def latest_source_fix():
    fix = rel.latest_event_relation_fix()
    if fix is None:
        raise RuntimeError("Tidak menemukan output FIX 02 event_relation.")
    return fix


def load_all_tables(base):
    return {
        name: pilot.read_csv(table_path(base, name))
        for name in ALL_TABLES
    }


def event_snapshot(tables, event_csv_path):
    return rel.event_snapshot(tables, event_csv_path)


def raw_payload_snapshot(tables):
    return rel.raw_payload_snapshot(tables)


def category_snapshot(tables, category_csv_path):
    rows = tables["category"]
    return {
        "count": len(rows),
        "ids": sorted(row["category_assignment_id"] for row in rows),
        "category_names": dict(
            sorted(Counter(row["category_name"] for row in rows).items())
        ),
        "category_scopes": dict(
            sorted(Counter(row["category_scope"] for row in rows).items())
        ),
        "category_csv_sha256": pilot.sha256_file(category_csv_path),
    }


def relation_snapshot(tables, relation_csv_path):
    rows = tables["event_relation"]
    return {
        "count": len(rows),
        "ids": sorted(row["event_relation_id"] for row in rows),
        "types": dict(
            sorted(Counter(row["event_relation_type"] for row in rows).items())
        ),
        "pairs": [
            {
                "relation_id": row["event_relation_id"],
                "from_event_id": row["from_event_id"],
                "to_event_id": row["to_event_id"],
                "type": row["event_relation_type"],
            }
            for row in sorted(rows, key=lambda item: item["event_relation_id"])
        ],
        "event_relation_csv_sha256": pilot.sha256_file(relation_csv_path),
    }


def location_snapshot(tables, location_csv_path):
    rows = tables["event_location"]
    return {
        "count": len(rows),
        "ids": sorted(row["event_location_id"] for row in rows),
        "flags": dict(
            sorted(Counter(row["is_inside_indonesia"] for row in rows).items())
        ),
        "event_location_csv_sha256": pilot.sha256_file(location_csv_path),
    }


def scope_counts(rows):
    counts = Counter()
    for row in rows:
        counts[row["is_inside_indonesia"]] += 1
    return {
        key: counts.get(key, 0)
        for key in ["ya", "tidak", "tidak_diketahui"]
    }


def _append_text(old, addition):
    old = str(old or "").strip()
    addition = str(addition or "").strip()
    if not addition:
        return old
    return f"{old}; {addition}" if old else addition


def _scope_note(classification):
    scope = classification["geographic_scope"]
    if scope == geo.UNKNOWN:
        return (
            "Perlu verifikasi batas wilayah untuk geographic scope; "
            "bbox pilot bukan batas nasional."
        )
    if scope == geo.OUTSIDE_INDONESIA:
        return (
            "Geographic scope luar Indonesia berdasarkan penanda wilayah "
            "asing dan koordinat di luar bbox pilot; batas nasional belum "
            "diverifikasi."
        )
    return (
        "Geographic scope Indonesia berdasarkan toponimi resmi dan "
        "koordinat di dalam bbox pilot; koordinat sumber belum diverifikasi."
    )


def build_updates(source_tables, generated_at):
    events = {row["event_id"]: row for row in source_tables["event"]}
    summary = []
    output_locations = []
    changes = []
    scope_changes = []

    for old_row in source_tables["event_location"]:
        event = events[old_row["event_id"]]
        classification = geo.classify_location(
            location_name=old_row["location_name"],
            latitude=old_row["latitude"],
            longitude=old_row["longitude"],
            coordinate_status=old_row["coordinate_status"],
            source_id=event["event_primary_source_id"],
            event_title=event["event_title"],
        )
        new_flag = classification["is_inside_indonesia"]
        old_flag = old_row["is_inside_indonesia"]
        if new_flag not in geo.VALID_FLAGS:
            raise ValueError(
                f"Flag scope tidak valid untuk {old_row['event_id']}: "
                f"{new_flag!r}"
            )
        changed = old_flag != new_flag
        new_row = dict(old_row)
        change_row = None

        if changed:
            evidence = (
                f"geographic_scope={classification['geographic_scope']}; "
                f"scope_flag={new_flag}; "
                f"scope_basis={classification['scope_basis']}; "
                f"scope_confidence={classification['scope_confidence']}; "
                f"scope_rule=geographic_scope.py"
            )
            scope_note = _scope_note(classification)
            new_row["is_inside_indonesia"] = new_flag
            new_row["location_evidence"] = _append_text(
                old_row["location_evidence"], evidence
            )
            new_row["location_notes"] = _append_text(
                old_row["location_notes"], scope_note
            )
            manual_review = (
                "ya" if classification["requires_review"] else "tidak"
            )
            change_id = "CHG-GEO-" + pilot.sha256_text(
                "|".join(
                    [
                        old_row["event_location_id"],
                        old_flag,
                        new_flag,
                        classification["scope_basis"],
                    ]
                )
            )[:16].upper()
            change_row = {
                "change_id": change_id,
                "target_type": "event_location",
                "target_id": old_row["event_location_id"],
                "change_type": "update",
                "changed_at": generated_at,
                "changed_by": "system_fix_geographic_scope",
                "field_name": "is_inside_indonesia",
                "old_value": old_flag,
                "new_value": new_flag,
                "change_reason": (
                    f"Koreksi geographic scope dari {old_flag} menjadi "
                    f"{new_flag}; basis={classification['scope_basis']}; "
                    f"{classification['scope_reason']} Kategori dan "
                    "category_scope tidak diubah; tidak merge/hapus; "
                    "koordinat sumber belum diverifikasi."
                ),
                "evidence_ref": (
                    f"event:{old_row['event_id']};"
                    f"event_location:{old_row['event_location_id']};"
                    f"coordinate_source:{old_row['coordinate_source']};"
                    f"scope_rule:geographic_scope.py"
                ),
                "schema_version": pilot.SCHEMA_VERSION,
                "manual_review": manual_review,
            }
            changes.append(change_row)
            scope_change = {
                "event_id": old_row["event_id"],
                "event_location_id": old_row["event_location_id"],
                "event_title": event["event_title"],
                "location_name": old_row["location_name"],
                "latitude": old_row["latitude"],
                "longitude": old_row["longitude"],
                "coordinate_status": old_row["coordinate_status"],
                "old_is_inside_indonesia": old_flag,
                "new_is_inside_indonesia": new_flag,
                "geographic_scope": classification["geographic_scope"],
                "scope_confidence": classification["scope_confidence"],
                "scope_basis": classification["scope_basis"],
                "scope_reason": classification["scope_reason"],
                "manual_review": manual_review,
                "change_id": change_id,
            }
            scope_changes.append(scope_change)

        output_locations.append(new_row)
        summary.append(
            {
                "event_id": old_row["event_id"],
                "event_title": event["event_title"],
                "event_primary_source_id": event[
                    "event_primary_source_id"
                ],
                "event_location_id": old_row["event_location_id"],
                "location_name": old_row["location_name"],
                "latitude": old_row["latitude"],
                "longitude": old_row["longitude"],
                "coordinate_status": old_row["coordinate_status"],
                "coordinate_source": old_row["coordinate_source"],
                "old_is_inside_indonesia": old_flag,
                "geographic_scope": classification["geographic_scope"],
                "new_is_inside_indonesia": new_flag,
                "scope_changed": changed,
                "scope_confidence": classification["scope_confidence"],
                "scope_basis": classification["scope_basis"],
                "scope_reason": classification["scope_reason"],
                "requires_review": classification["requires_review"],
                "inside_pilot_bbox": classification["inside_pilot_bbox"],
                "distance_km": classification["distance_km"],
                "indonesia_toponyms": ";".join(
                    classification["indonesia_toponyms"]
                ),
                "land_marker": classification["land_marker"],
                "sea_marker": classification["sea_marker"],
                "foreign_marker": classification["foreign_marker"],
                "indonesia_label": classification["indonesia_label"],
            }
        )

    return output_locations, changes, scope_changes, summary


def build_validation(
    summary,
    output_locations,
    source_tables,
    output_tables,
    source_categories,
    output_categories,
    source_relations,
    output_relations,
):
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

    rows = []
    invalid = [
        row["event_id"]
        for row in summary
        if row["new_is_inside_indonesia"] not in geo.VALID_FLAGS
    ]
    add(
        "R-LOC-05",
        "P0",
        len(summary),
        "lulus" if not invalid else "gagal",
        (
            "Flag geographic scope konsisten dengan classifier berbasis "
            "toponimi/koordinat; bbox pilot bukan bukti tunggal."
        ),
        invalid,
    )

    missing_evidence = [
        row["event_id"]
        for row in summary
        if row["geographic_scope"] in {geo.UNKNOWN, geo.OUTSIDE_INDONESIA}
        and not (row["scope_basis"] and row["scope_reason"])
    ]
    add(
        "R-GEO-01",
        "P1",
        len(summary),
        "lulus" if not missing_evidence else "gagal",
        "Setiap scope unknown/luar memiliki basis dan alasan.",
        missing_evidence,
    )

    source_category_by_event = {
        row["event_id"]: row for row in source_categories
    }
    category_scope_changed = [
        row["event_id"]
        for row in output_categories
        if source_category_by_event.get(row["event_id"], {}).get(
            "category_scope"
        )
        != row["category_scope"]
    ]
    add(
        "R-GEO-02",
        "P0",
        len(output_categories),
        "lulus" if not category_scope_changed else "gagal",
        (
            "category_scope tidak diubah dan tidak dipakai sebagai "
            "pengganti geographic scope."
        ),
        category_scope_changed,
    )

    unverified_failures = [
        row["event_id"]
        for row in output_locations
        if row["coordinate_status"] == "verified"
        or row["coordinate_verified_at"]
        or row["coordinate_verified_by"]
    ]
    add(
        "R-GEO-03",
        "P0",
        len(output_locations),
        "lulus" if not unverified_failures else "gagal",
        (
            "Koordinat source_coordinate tidak dinaikkan menjadi verified "
            "oleh fix geographic scope."
        ),
        unverified_failures,
    )

    outside_bbox_indonesia = [
        row["event_id"]
        for row in summary
        if row["inside_pilot_bbox"] is False
        and row["new_is_inside_indonesia"] == "ya"
    ]
    add(
        "R-GEO-04",
        "P0",
        len(
            [
                row
                for row in summary
                if row["inside_pilot_bbox"] is False
            ]
        ),
        "lulus" if not outside_bbox_indonesia else "gagal",
        (
            "Tidak ada titik di luar bbox pilot yang dipaksa menjadi "
            "Indonesia tanpa bukti batas nasional."
        ),
        outside_bbox_indonesia,
    )

    source_relation_ids = sorted(
        row["event_relation_id"] for row in source_relations
    )
    output_relation_ids = sorted(
        row["event_relation_id"] for row in output_relations
    )
    relation_failures = []
    if source_relation_ids != output_relation_ids:
        relation_failures.append("relation_ids_berubah")
    if not EXPECTED_RELATION_IDS.issubset(set(output_relation_ids)):
        relation_failures.append("relasi_fix02_hilang")
    add(
        "R-GEO-05",
        "P0",
        len(output_relations),
        "lulus" if not relation_failures else "gagal",
        (
            "Seluruh relasi FIX 02 dipertahankan tanpa merge/hapus; "
            "relasi tidak diubah oleh fix geographic scope."
        ),
        relation_failures,
    )

    unknown = [
        row
        for row in summary
        if row["new_is_inside_indonesia"] == "tidak_diketahui"
    ]
    add(
        "R-GEO-06",
        "P1",
        len(unknown),
        "perlu_review" if unknown else "lulus",
        (
            "Event dengan scope tidak_diketahui dicatat untuk review manual; "
            "tidak dipaksa menjadi Indonesia atau luar Indonesia."
        ),
        [row["event_id"] for row in unknown],
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
    events_before = event_snapshot(
        source_tables, table_path(source_fix, "event")
    )
    locations_before = location_snapshot(
        source_tables, table_path(source_fix, "event_location")
    )
    categories_before = category_snapshot(
        source_tables, table_path(source_fix, "category")
    )
    relations_before = relation_snapshot(
        source_tables, table_path(source_fix, "event_relation")
    )
    raw_before = raw_payload_snapshot(source_tables)
    scope_before = scope_counts(source_tables["event_location"])

    output_locations, new_changes, scope_changes, summary = build_updates(
        source_tables, generated_at
    )
    output_changes = list(source_tables["change_log"]) + new_changes

    output_tables_dir = output_dir / "tables"
    output_tables_dir.mkdir(parents=True, exist_ok=False)
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

    output_tables = load_all_tables(output_dir)
    output_table_hashes = {
        path.name: pilot.sha256_file(path)
        for path in sorted(output_tables_dir.glob("*.csv"))
    }
    events_after = event_snapshot(
        output_tables, table_path(output_dir, "event")
    )
    locations_after = location_snapshot(
        output_tables, table_path(output_dir, "event_location")
    )
    categories_after = category_snapshot(
        output_tables, table_path(output_dir, "category")
    )
    relations_after = relation_snapshot(
        output_tables, table_path(output_dir, "event_relation")
    )
    raw_after = raw_payload_snapshot(output_tables)
    baseline_after = pilot.dataset_baseline.verify_dataset()
    scope_after = scope_counts(output_tables["event_location"])

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
        row["event_location_id"] for row in scope_changes
    }
    change_rows_by_location = {
        row["target_id"]: row
        for row in new_changes
        if row["target_type"] == "event_location"
    }
    all_scope_changes_logged = all(
        location_id in change_rows_by_location
        for location_id in changed_location_ids
    )
    no_unlogged_location_changes = (
        location_other_fields_equal
        and all_scope_changes_logged
        and set(source_location_by_id) == set(output_location_by_id)
    )

    checks = {
        "event_count_unchanged": (
            events_before["count"] == events_after["count"]
        ),
        "event_ids_unchanged": (
            events_before["ids"] == events_after["ids"]
        ),
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
        "all_scope_changes_logged": all_scope_changes_logged,
        "no_unlogged_location_changes": no_unlogged_location_changes,
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
            row["is_inside_indonesia"] in geo.VALID_FLAGS
            for row in output_tables["event_location"]
        ),
        "no_outer_bbox_marked_indonesia": not any(
            row["inside_pilot_bbox"] is False
            and row["new_is_inside_indonesia"] == "ya"
            for row in summary
        ),
        "change_log_count_expected": (
            len(output_changes) == len(source_tables["change_log"])
            + len(new_changes)
        ),
    }

    validation = build_validation(
        summary,
        output_tables["event_location"],
        source_tables,
        output_tables,
        source_tables["category"],
        output_tables["category"],
        source_tables["event_relation"],
        output_tables["event_relation"],
    )

    summary_fields = [
        "event_id",
        "event_title",
        "event_primary_source_id",
        "event_location_id",
        "location_name",
        "latitude",
        "longitude",
        "coordinate_status",
        "coordinate_source",
        "old_is_inside_indonesia",
        "geographic_scope",
        "new_is_inside_indonesia",
        "scope_changed",
        "scope_confidence",
        "scope_basis",
        "scope_reason",
        "requires_review",
        "inside_pilot_bbox",
        "distance_km",
        "indonesia_toponyms",
        "land_marker",
        "sea_marker",
        "foreign_marker",
        "indonesia_label",
    ]
    pilot.write_csv(
        output_dir / "geographic_scope_summary.csv",
        summary,
        summary_fields,
    )
    evidence_payload = [
        {
            "event_id": row["event_id"],
            "event_title": row["event_title"],
            "event_primary_source_id": row["event_primary_source_id"],
            "event_location_id": row["event_location_id"],
            "location_name": row["location_name"],
            "coordinate": [row["latitude"], row["longitude"]],
            "coordinate_status": row["coordinate_status"],
            "coordinate_source": row["coordinate_source"],
            "old_is_inside_indonesia": row["old_is_inside_indonesia"],
            "geographic_scope": row["geographic_scope"],
            "new_is_inside_indonesia": row["new_is_inside_indonesia"],
            "scope_changed": row["scope_changed"],
            "scope_confidence": row["scope_confidence"],
            "scope_basis": row["scope_basis"],
            "scope_reason": row["scope_reason"],
            "requires_review": row["requires_review"],
            "evidence_used": {
                "location_name": row["location_name"],
                "inside_pilot_bbox": row["inside_pilot_bbox"],
                "distance_km": row["distance_km"],
                "indonesia_toponyms": row["indonesia_toponyms"],
                "land_marker": row["land_marker"],
                "sea_marker": row["sea_marker"],
                "foreign_marker": row["foreign_marker"],
                "indonesia_label": row["indonesia_label"],
            },
            "event_title_used_as_location_evidence": False,
            "caveat": (
                "Bbox pilot bukan batas wilayah nasional; coordinate_status "
                "source_coordinate tidak dinaikkan menjadi verified."
            ),
        }
        for row in summary
    ]
    pilot.write_json(
        output_dir / "geographic_scope_evidence.json", evidence_payload
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
        output_dir / "geographic_scope_validation.csv",
        validation,
        validation_fields,
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
            "scope_changes": len(scope_changes),
        },
        "scope_counts_before": scope_before,
        "scope_counts_after": scope_after,
        "scope_changes": scope_changes,
        "manual_review": [
            row for row in summary if row["requires_review"]
        ],
        "checks": checks,
        "validation": validation,
        "rules": {
            "geographic_field": "event_location.is_inside_indonesia",
            "geographic_vocabulary": sorted(geo.VALID_FLAGS),
            "scope_mapping": geo.SCOPE_TO_FLAG,
            "pilot_bbox": geo.PILOT_BBOX,
            "pilot_bbox_is_national_boundary": False,
            "near_field_km": geo.NEAR_FIELD_KM,
            "evidence_order": [
                "valid coordinate",
                "pilot bbox sanity check",
                "official location_name toponym/land/sea marker",
                "distance from location_name",
                "event_primary_source_id only as administrative context",
                "event_title is not used",
            ],
            "unknown_policy": (
                "Titik di luar bbox, di laut, tanpa koordinat, dekat "
                "perbatasan, atau tanpa toponimi yang cukup ditandai "
                "tidak_diketahui dan masuk review manual."
            ),
        },
        "schema_changes": {
            "applied": False,
            "reason": (
                "Field event_location.is_inside_indonesia sudah ada dengan "
                "vocabulary ya;tidak;tidak_diketahui. Tidak ada field baru."
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
            "Perbaiki geographic scope pada snapshot FIX 02 tanpa mengubah "
            "event, kategori, relasi, baseline, atau raw payload."
        )
    )
    parser.add_argument(
        "--source-fix",
        default=str(latest_source_fix()),
        help="Direktori FIX 02 atau snapshot turunan yang menjadi sumber.",
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
    print(f"Scope before: {manifest['scope_counts_before']}")
    print(f"Scope after: {manifest['scope_counts_after']}")
    print(f"Scope changes: {manifest['counts']['scope_changes']}")
    failed = [
        key for key, value in manifest["checks"].items() if not value
    ]
    print(f"Checks failed: {failed if failed else 'tidak ada'}")


if __name__ == "__main__":
    main()
