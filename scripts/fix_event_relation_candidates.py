#!/usr/bin/env python3
"""Catat relasi kandidat duplikat BMKG-USGS tanpa merge atau hapus event."""

import argparse
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import pilot_collect_official_geohazard as pilot

FIX_PREFIX = "FIX-EVENT-RELATION-"
DEFAULT_SOURCE_FIX = (
    pilot.PILOT_ROOT / "fixes" / "FIX-TSUNAMI-20261102T171637Z"
)
RELATION_TYPE = "related_to"
RELATION_CONFIDENCE = "medium"
RELATION_SOURCE = "system_fix_event_relation"
RELATION_RULES = {"R-REL-01", "R-REL-02", "R-REL-03"}
ALLOWED_RELATION_TYPES = {
    "same_event",
    "component_of",
    "secondary_hazard_of",
    "duplicate_of",
    "supersedes",
    "related_to",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low", "unknown"}
SCHEMA_RECOMMENDATIONS = [
    (
        "event_relation_assessment enum: possible_same_event|likely_same_event|"
        "unresolved|likely_distinct_event|confirmed_same_event"
    ),
    "event_relation_reason text: alasan penilaian yang terpisah dari bukti mentah",
    "event_relation_source_refs text/JSON: daftar event, dokumen, raw payload, dan hash",
]


def table_path(base, name):
    return base / "tables" / f"{name}.csv"


def latest_tsunami_fix():
    fixes = sorted(
        path
        for path in (pilot.PILOT_ROOT / "fixes").glob("FIX-TSUNAMI-*")
        if (path / "tables" / "event.csv").is_file()
    )
    return fixes[-1] if fixes else DEFAULT_SOURCE_FIX


def latest_event_relation_fix():
    fixes = sorted(
        path
        for path in (pilot.PILOT_ROOT / "fixes").glob(
            FIX_PREFIX + "*"
        )
        if (path / "tables" / "event_relation.csv").is_file()
    )
    return fixes[-1] if fixes else None


def parse_float(value):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def load_tables(base):
    names = [
        "event",
        "event_time",
        "event_location",
        "event_attribute",
        "document",
        "document_event_link",
        "raw_payload",
    ]
    return {name: pilot.read_csv(table_path(base, name)) for name in names}


def event_attributes(tables):
    attributes = defaultdict(dict)
    for row in tables["event_attribute"]:
        attributes[row["event_id"]][row["attribute_name"]] = row[
            "attribute_value"
        ]
    return attributes


def source_references(tables):
    documents = {row["document_id"]: row for row in tables["document"]}
    raw_payloads = {
        row["raw_payload_id"]: row for row in tables["raw_payload"]
    }
    links_by_event = defaultdict(list)
    for link in tables["document_event_link"]:
        links_by_event[link["event_id"]].append(link)

    references = {}
    for event in tables["event"]:
        event_id = event["event_id"]
        parts = []
        seen = set()
        links = sorted(
            links_by_event.get(event_id, []),
            key=lambda row: (
                row["is_primary"] != "ya",
                row["document_id"],
            ),
        )
        for link in links:
            document = documents.get(link["document_id"])
            if document is None:
                continue
            raw = raw_payloads.get(document["document_raw_payload_id"])
            label = (
                "USGS"
                if document["document_source_id"] == "usgs_m45"
                else "BMKG"
            )
            key = (label, document["document_id"])
            if key in seen:
                continue
            seen.add(key)
            if raw is None:
                parts.append(
                    f"{label}_DOC={document['document_id']}"
                )
            else:
                parts.append(
                    f"{label}_DOC={document['document_id']};"
                    f"{label}_RAW={raw['raw_payload_id']};"
                    f"{label}_RAW_SHA256={raw['raw_payload_sha256']}"
                )
        references[event_id] = " | ".join(parts)
    return references


def classify_pair(pair):
    magnitude_gap = None
    if pair["bmkg_magnitude"] is not None and pair["usgs_magnitude"] is not None:
        magnitude_gap = abs(pair["bmkg_magnitude"] - pair["usgs_magnitude"])

    if pair["time_diff_seconds"] <= 10 and pair["distance_km"] <= 50:
        if magnitude_gap is None or magnitude_gap <= 0.5:
            assessment = "likely_same_event"
        else:
            assessment = "possible_same_event"
    elif pair["time_diff_seconds"] <= 60 and pair["distance_km"] <= 50:
        assessment = "possible_same_event"
    elif pair["time_diff_seconds"] <= 300 and pair["distance_km"] <= 150:
        assessment = "possible_same_event"
    else:
        assessment = "likely_distinct_event"

    parts = [
        f"Waktu berbeda {pair['time_diff_seconds']:.0f} detik",
        f"jarak episentrum {pair['distance_km']:.1f} km",
    ]
    if pair["bmkg_magnitude"] is not None:
        parts.append(f"magnitudo BMKG {pair['bmkg_magnitude']:.1f}")
    if pair["usgs_magnitude"] is not None:
        parts.append(f"magnitudo USGS {pair['usgs_magnitude']:.1f}")
    if pair["bmkg_depth_km"] is not None:
        parts.append(f"kedalaman BMKG {pair['bmkg_depth_km']:.1f} km")
    if pair["usgs_depth_km"] is not None:
        parts.append(f"kedalaman USGS {pair['usgs_depth_km']:.1f} km")
    parts.append(
        "wilayah/judul kedua sumber konsisten"
        if pair["region_consistent"]
        else "wilayah/judul kedua sumber tidak sepenuhnya konsisten"
    )
    reason = (
        "; ".join(parts)
        + f". Penilaian lokal: {assessment}; bukan confirmed_same_event, "
        "tidak ada katalog independen, dan tidak dilakukan merge."
    )
    return assessment, reason


def pair_label(pair):
    title = pair["bmkg_title"].upper()
    if "TOMOHON" in title:
        return "Tomohon"
    if "TANIMBAR" in title:
        return "Tanimbar"
    return pair["bmkg_event_id"]


def candidate_pairs(tables):
    events = {row["event_id"]: row for row in tables["event"]}
    times = {row["event_id"]: row for row in tables["event_time"]}
    locations = {
        row["event_id"]: row for row in tables["event_location"]
    }
    attributes = event_attributes(tables)
    references = source_references(tables)

    bmkg_events = [
        row
        for row in tables["event"]
        if row["event_primary_source_id"].startswith("bmkg_")
    ]
    usgs_events = [
        row
        for row in tables["event"]
        if row["event_primary_source_id"] == "usgs_m45"
    ]

    pairs = []
    for left in bmkg_events:
        left_event_id = left["event_id"]
        left_time = times[left_event_id]
        left_location = locations[left_event_id]
        for right in usgs_events:
            right_event_id = right["event_id"]
            right_time = times[right_event_id]
            right_location = locations[right_event_id]
            distance = pilot.haversine_km(
                float(left_location["latitude"]),
                float(left_location["longitude"]),
                float(right_location["latitude"]),
                float(right_location["longitude"]),
            )
            time_diff = abs(
                (
                    pilot.parse_iso(left_time["event_time"])
                    - pilot.parse_iso(right_time["event_time"])
                ).total_seconds()
            )
            if distance > 150 or time_diff > 300:
                continue

            left_attributes = attributes.get(left_event_id, {})
            right_attributes = attributes.get(right_event_id, {})
            left_title = left["event_title"].upper()
            right_title = right["event_title"].upper()
            region_consistent = (
                ("TOMOHON" in left_title and "TOMOHON" in right_title)
                or ("TANIMBAR" in left_title and "BANDA SEA" in right_title)
                or ("TANIMBAR" in left_title and "TANIMBAR" in right_title)
            )
            pair = {
                "pair_label": "",
                "bmkg_event_id": left_event_id,
                "usgs_event_id": right_event_id,
                "bmkg_source_id": left["event_primary_source_id"],
                "usgs_source_id": right["event_primary_source_id"],
                "bmkg_native_id": left["event_source_native_id"],
                "usgs_native_id": right["event_source_native_id"],
                "bmkg_title": left["event_title"],
                "usgs_title": right["event_title"],
                "bmkg_time": left_time["event_time"],
                "usgs_time": right_time["event_time"],
                "bmkg_latitude": left_location["latitude"],
                "bmkg_longitude": left_location["longitude"],
                "usgs_latitude": right_location["latitude"],
                "usgs_longitude": right_location["longitude"],
                "bmkg_magnitude": parse_float(
                    left_attributes.get("magnitude")
                ),
                "usgs_magnitude": parse_float(
                    right_attributes.get("magnitude")
                ),
                "bmkg_depth_km": parse_float(
                    left_attributes.get("depth")
                ),
                "usgs_depth_km": parse_float(
                    right_attributes.get("depth")
                ),
                "time_diff_seconds": time_diff,
                "distance_km": distance,
                "region_consistent": region_consistent,
                "bmkg_source_refs": references.get(left_event_id, ""),
                "usgs_source_refs": references.get(right_event_id, ""),
            }
            pair["pair_label"] = pair_label(pair)
            assessment, reason = classify_pair(pair)
            pair["assessment"] = assessment
            pair["reason"] = reason
            pairs.append(pair)

    return sorted(
        pairs,
        key=lambda value: (
            value["pair_label"],
            value["bmkg_event_id"],
            value["usgs_event_id"],
        ),
    )


def relation_row(pair, created_at):
    relation_id = "EREL-" + pilot.sha256_text(
        f"{pair['bmkg_event_id']}|{pair['usgs_event_id']}|"
        f"candidate_duplicate|{RELATION_TYPE}"
    )[:16].upper()
    evidence = (
        f"candidate_duplicate=true; assessment={pair['assessment']}; "
        f"relation_type={RELATION_TYPE}; no_merge=true; "
        "confirmed_same_event=false; "
        f"bmkg_event_id={pair['bmkg_event_id']}; "
        f"usgs_event_id={pair['usgs_event_id']}; "
        f"bmkg_native_id={pair['bmkg_native_id'] or 'null'}; "
        f"usgs_native_id={pair['usgs_native_id'] or 'null'}; "
        f"bmkg_time={pair['bmkg_time']}; usgs_time={pair['usgs_time']}; "
        f"time_diff_seconds={pair['time_diff_seconds']:.0f}; "
        f"distance_km={pair['distance_km']:.3f}; "
        f"bmkg_coordinate={pair['bmkg_latitude']},{pair['bmkg_longitude']}; "
        f"usgs_coordinate={pair['usgs_latitude']},{pair['usgs_longitude']}; "
        f"bmkg_magnitude={pair['bmkg_magnitude']}; "
        f"usgs_magnitude={pair['usgs_magnitude']}; "
        f"bmkg_depth_km={pair['bmkg_depth_km']}; "
        f"usgs_depth_km={pair['usgs_depth_km']}; "
        f"reason={pair['reason']}; "
        f"source_refs=BMKG[{pair['bmkg_source_refs']}] "
        f"USGS[{pair['usgs_source_refs']}]; "
        "caveat=Bukti lokal tidak sama dengan verifikasi katalog independen; "
        "relasi tidak menyatakan kedua event pasti sama dan tidak melakukan merge."
    )
    return {
        "event_relation_id": relation_id,
        "from_event_id": pair["bmkg_event_id"],
        "to_event_id": pair["usgs_event_id"],
        "event_relation_type": RELATION_TYPE,
        "event_relation_confidence": RELATION_CONFIDENCE,
        "event_relation_evidence": evidence,
        "created_at": created_at,
    }


def build_relation_rows(pairs, created_at):
    return [relation_row(pair, created_at) for pair in pairs]


def build_change_log_rows(
    source_changes, relations, pairs, dictionary, generated_at
):
    rows = [dict(row) for row in source_changes]
    pair_by_relation = {
        relation["event_relation_id"]: pair
        for relation, pair in zip(relations, pairs)
    }
    for relation in relations:
        pair = pair_by_relation[relation["event_relation_id"]]
        row = {field: "" for field in dictionary["change_log"]}
        row.update(
            {
                "change_id": "CHG-"
                + pilot.sha256_text(
                    f"event_relation|{relation['event_relation_id']}"
                )[:16].upper(),
                "target_type": "event_relation",
                "target_id": relation["event_relation_id"],
                "change_type": "create",
                "changed_at": generated_at,
                "changed_by": RELATION_SOURCE,
                "change_reason": (
                    "Pencatatan relasi kandidat duplikat tanpa merge; "
                    f"assessment={pair['assessment']}; "
                    f"{pair['bmkg_event_id']} <-> {pair['usgs_event_id']}."
                ),
                "schema_version": pilot.SCHEMA_VERSION,
                "manual_review": "tidak",
            }
        )
        rows.append(row)
    return rows


def validate_relations(relations, event_ids):
    results = []

    def add(rule_id, severity, status, detail, failures):
        results.append(
            {
                "rule_id": rule_id,
                "severity": severity,
                "entity": "event_relation",
                "records_checked": len(relations),
                "status": status,
                "detail": (
                    f"{len(failures)} pelanggaran; contoh: "
                    + " | ".join(failures[:5])
                    if failures
                    else detail
                ),
                "record_refs": " | ".join(failures[:10]),
            }
        )

    relation_ids = [row["event_relation_id"] for row in relations]
    failures = [
        f"{relation_id}: event_relation_id duplikat"
        for relation_id in relation_ids
        if relation_ids.count(relation_id) > 1
    ]
    failures.extend(
        f"{row['event_relation_id']}: from_event_id tidak valid"
        for row in relations
        if row["from_event_id"] not in event_ids
    )
    failures.extend(
        f"{row['event_relation_id']}: to_event_id tidak valid"
        for row in relations
        if row["to_event_id"] not in event_ids
    )
    failures.extend(
        f"{row['event_relation_id']}: relasi ke diri sendiri"
        for row in relations
        if row["from_event_id"] == row["to_event_id"]
    )
    add(
        "R-REL-01",
        "P0",
        "gagal" if failures else "lulus",
        f"{len(relations)} relasi diperiksa; ID unik dan FK valid.",
        failures,
    )

    failures = []
    for row in relations:
        if row["event_relation_type"] not in ALLOWED_RELATION_TYPES:
            failures.append(
                f"{row['event_relation_id']}: tipe relasi tidak valid"
            )
        if row["event_relation_confidence"] not in ALLOWED_CONFIDENCE:
            failures.append(
                f"{row['event_relation_id']}: confidence tidak valid"
            )
        if not row["event_relation_evidence"]:
            failures.append(
                f"{row['event_relation_id']}: bukti kosong"
            )
    add(
        "R-REL-02",
        "P1",
        "perlu_review" if failures else "lulus",
        f"{len(relations)} relasi memiliki tipe, confidence, dan bukti.",
        failures,
    )

    graph = defaultdict(list)
    for row in relations:
        graph[row["from_event_id"]].append(row["to_event_id"])
    visiting = set()
    visited = set()
    cycles = []

    def visit(node, path):
        if node in visiting:
            cycles.append(" -> ".join(path + [node]))
            return
        if node in visited:
            return
        visiting.add(node)
        for child in graph.get(node, []):
            visit(child, path + [node])
        visiting.remove(node)
        visited.add(node)

    for event_id in event_ids:
        visit(event_id, [])
    failures = [f"siklus relasi: {cycle}" for cycle in cycles]
    add(
        "R-REL-03",
        "P1",
        "perlu_review" if failures else "lulus",
        "Tidak ada siklus relasi dan tidak ada pertentangan grup.",
        failures,
    )
    return results


def raw_payload_snapshot(tables):
    snapshot = {}
    for row in tables["raw_payload"]:
        path = ROOT / row["raw_payload_path"]
        snapshot[row["raw_payload_id"]] = {
            "path": row["raw_payload_path"],
            "sha256": (
                pilot.sha256_file(path)
                if path.is_file()
                else "missing"
            ),
        }
    return snapshot


def event_snapshot(tables, event_csv_path):
    return {
        "count": len(tables["event"]),
        "ids": sorted(row["event_id"] for row in tables["event"]),
        "event_csv_sha256": pilot.sha256_file(event_csv_path),
    }


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
    source_tables = load_tables(source_fix)
    source_changes = pilot.read_csv(table_path(source_fix, "change_log"))
    source_relations = pilot.read_csv(
        table_path(source_fix, "event_relation")
    )

    baseline_before = pilot.dataset_baseline.verify_dataset()
    events_before = event_snapshot(
        source_tables, table_path(source_fix, "event")
    )
    raw_before = raw_payload_snapshot(source_tables)
    source_table_hashes = {
        path.name: pilot.sha256_file(path)
        for path in sorted((source_fix / "tables").glob("*.csv"))
    }

    pairs = candidate_pairs(source_tables)
    relations = build_relation_rows(pairs, generated_at)
    changes = build_change_log_rows(
        source_changes,
        relations,
        pairs,
        dictionary,
        generated_at,
    )
    event_ids = {row["event_id"] for row in source_tables["event"]}
    validation = validate_relations(relations, event_ids)

    output_tables = output_dir / "tables"
    output_tables.mkdir(parents=True, exist_ok=False)
    for path in sorted((source_fix / "tables").glob("*.csv")):
        if path.name in {"event_relation.csv", "change_log.csv"}:
            continue
        shutil.copy2(path, output_tables / path.name)
    pilot.write_csv(
        output_tables / "event_relation.csv",
        relations,
        dictionary["event_relation"],
    )
    pilot.write_csv(
        output_tables / "change_log.csv",
        changes,
        dictionary["change_log"],
    )

    output_tables_rows = {
        name: pilot.read_csv(table_path(output_dir, name))
        for name in [
            "event",
            "event_time",
            "event_location",
            "event_attribute",
            "document",
            "document_event_link",
            "raw_payload",
            "event_relation",
            "change_log",
        ]
    }
    events_after = event_snapshot(
        output_tables_rows, table_path(output_dir, "event")
    )
    raw_after = raw_payload_snapshot(output_tables_rows)
    baseline_after = pilot.dataset_baseline.verify_dataset()
    output_table_hashes = {
        path.name: pilot.sha256_file(path)
        for path in sorted(output_tables.glob("*.csv"))
    }

    summary_rows = []
    evidence_rows = []
    for pair, relation in zip(pairs, relations):
        summary_rows.append(
            {
                "pair_label": pair["pair_label"],
                "bmkg_event_id": pair["bmkg_event_id"],
                "usgs_event_id": pair["usgs_event_id"],
                "time_diff_seconds": f"{pair['time_diff_seconds']:.0f}",
                "distance_km": f"{pair['distance_km']:.3f}",
                "bmkg_magnitude": (
                    f"{pair['bmkg_magnitude']:.2f}"
                    if pair["bmkg_magnitude"] is not None
                    else ""
                ),
                "usgs_magnitude": (
                    f"{pair['usgs_magnitude']:.2f}"
                    if pair["usgs_magnitude"] is not None
                    else ""
                ),
                "bmkg_depth_km": (
                    f"{pair['bmkg_depth_km']:.2f}"
                    if pair["bmkg_depth_km"] is not None
                    else ""
                ),
                "usgs_depth_km": (
                    f"{pair['usgs_depth_km']:.2f}"
                    if pair["usgs_depth_km"] is not None
                    else ""
                ),
                "assessment": pair["assessment"],
                "relation_id": relation["event_relation_id"],
                "relation_type": relation["event_relation_type"],
                "relation_confidence": relation[
                    "event_relation_confidence"
                ],
                "reason": pair["reason"],
            }
        )
        evidence_rows.append(
            {
                "relation_id": relation["event_relation_id"],
                "pair_label": pair["pair_label"],
                "assessment": pair["assessment"],
                "reason": pair["reason"],
                "event_relation_type": relation[
                    "event_relation_type"
                ],
                "event_relation_confidence": relation[
                    "event_relation_confidence"
                ],
                "created_at": generated_at,
                "metrics": {
                    "time_diff_seconds": pair["time_diff_seconds"],
                    "distance_km": pair["distance_km"],
                    "bmkg_time": pair["bmkg_time"],
                    "usgs_time": pair["usgs_time"],
                    "bmkg_coordinate": [
                        pair["bmkg_latitude"],
                        pair["bmkg_longitude"],
                    ],
                    "usgs_coordinate": [
                        pair["usgs_latitude"],
                        pair["usgs_longitude"],
                    ],
                    "bmkg_magnitude": pair["bmkg_magnitude"],
                    "usgs_magnitude": pair["usgs_magnitude"],
                    "bmkg_depth_km": pair["bmkg_depth_km"],
                    "usgs_depth_km": pair["usgs_depth_km"],
                },
                "source_refs": {
                    "bmkg": pair["bmkg_source_refs"],
                    "usgs": pair["usgs_source_refs"],
                },
                "caveat": (
                    "Bukti lokal tidak sama dengan verifikasi katalog "
                    "independen; bukan confirmed_same_event; tidak merge."
                ),
            }
        )

    summary_fields = [
        "pair_label",
        "bmkg_event_id",
        "usgs_event_id",
        "time_diff_seconds",
        "distance_km",
        "bmkg_magnitude",
        "usgs_magnitude",
        "bmkg_depth_km",
        "usgs_depth_km",
        "assessment",
        "relation_id",
        "relation_type",
        "relation_confidence",
        "reason",
    ]
    pilot.write_csv(
        output_dir / "event_relation_fix_summary.csv",
        summary_rows,
        summary_fields,
    )
    pilot.write_json(
        output_dir / "event_relation_evidence.json", evidence_rows
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
        output_dir / "event_relation_validation.csv",
        validation,
        validation_fields,
    )

    source_manifest_path = source_fix / "fix_manifest.json"
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
        "source_fix_relations_were_empty": len(source_relations) == 0,
        "relations_point_to_existing_events": all(
            row["from_event_id"] in event_ids
            and row["to_event_id"] in event_ids
            for row in relations
        ),
        "relation_validation_no_p0": not any(
            row["severity"] == "P0" and row["status"] == "gagal"
            for row in validation
        ),
    }

    manifest = {
        "fix_id": fix_id,
        "generated_at": generated_at,
        "source_fix": str(source_fix.relative_to(ROOT)).replace("\\", "/"),
        "source_fix_manifest_sha256": (
            pilot.sha256_file(source_manifest_path)
            if source_manifest_path.is_file()
            else ""
        ),
        "source_tables_sha256": source_table_hashes,
        "output_tables_sha256": output_table_hashes,
        "baseline_before": baseline_before,
        "baseline_after": baseline_after,
        "raw_payload_before": raw_before,
        "raw_payload_after": raw_after,
        "events_before": events_before,
        "events_after": events_after,
        "relations": [
            {
                **relation,
                "assessment": pair["assessment"],
                "reason": pair["reason"],
            }
            for pair, relation in zip(pairs, relations)
        ],
        "counts": {
            "events_before": events_before["count"],
            "events_after": events_after["count"],
            "relations_before": len(source_relations),
            "relations_after": len(relations),
            "change_log_before": len(source_changes),
            "change_log_after": len(changes),
        },
        "checks": checks,
        "validation": validation,
        "schema_changes": {
            "applied": False,
            "reason": (
                "Schema event_relation sudah menyediakan tipe, confidence, "
                "evidence, dan created_at. Penilaian, alasan, dan referensi "
                "sumber disimpan di evidence tanpa mengubah schema."
            ),
            "recommended_minimum": SCHEMA_RECOMMENDATIONS,
        },
    }
    pilot.write_json(output_dir / "fix_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Catat relasi kandidat duplikat BMKG-USGS pada snapshot turunan "
            "tanpa merge, hapus, atau perubahan baseline/raw payload."
        )
    )
    parser.add_argument(
        "--source-fix",
        default=str(latest_tsunami_fix()),
        help="Direktori FIX 01 atau snapshot turunan yang menjadi sumber.",
    )
    parser.add_argument(
        "--fix-id",
        default="",
        help="ID direktori fix; default memakai timestamp UTC.",
    )
    args = parser.parse_args()

    source_fix = Path(args.source_fix)
    if not source_fix.is_absolute():
        source_fix = ROOT / source_fix
    required = [
        table_path(source_fix, name)
        for name in [
            "event",
            "event_time",
            "event_location",
            "event_attribute",
            "document",
            "document_event_link",
            "raw_payload",
            "event_relation",
            "change_log",
        ]
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("File sumber tidak ditemukan: " + ", ".join(missing))

    output_dir = choose_output_dir(args.fix_id)
    manifest = write_fix(
        source_fix, output_dir, fix_id=output_dir.name
    )
    failed = [
        name for name, passed in manifest["checks"].items() if not passed
    ]
    print(str(output_dir.relative_to(ROOT)))
    print(f"RELATIONS={manifest['counts']['relations_after']}")
    print(f"ASSESSMENTS={[row['assessment'] for row in manifest['relations']]}")
    print(f"CHECKS_FAILED={failed}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
