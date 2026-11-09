#!/usr/bin/env python3
"""Buat snapshot turunan event_attribute dengan semantik potensi tsunami."""

import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import pilot_collect_official_geohazard as pilot

DEFAULT_SOURCE_RUN = pilot.PILOT_ROOT / "runs" / "PILOT-20261102T110641Z"
LEGACY_NAMES = {"tsunami_potential", "bmkg_potential_note"}
NEW_NAMES = {"bmkg_potential_text", "tsunami_potential_status"}
REPLACED_NAMES = LEGACY_NAMES | NEW_NAMES


def event_attribute_rows(source_run, dictionary):
    attributes = pilot.read_csv(
        source_run / "tables" / "event_attribute.csv"
    )
    events = pilot.read_csv(source_run / "tables" / "event.csv")
    raw_text_by_event = {}
    raw_source_by_event = {}
    for row in attributes:
        name = row["attribute_name"]
        if name not in {"tsunami_potential", "bmkg_potential_note"}:
            if name != "bmkg_potential_text":
                continue
        value = row["attribute_value"]
        if not value.strip():
            continue
        event_id = row["event_id"]
        if event_id not in raw_text_by_event or name == "tsunami_potential":
            raw_text_by_event[event_id] = value
            raw_source_by_event[event_id] = row["attribute_source_id"]

    cleaned = [
        row
        for row in attributes
        if row["attribute_name"] not in REPLACED_NAMES
    ]
    primary_sources = {
        row["event_id"]: row["event_primary_source_id"] for row in events
    }
    summary = []
    rebuilt = []
    for event in events:
        event_id = event["event_id"]
        raw_text = raw_text_by_event.get(event_id, "")
        source_id = (
            raw_source_by_event.get(event_id)
            or primary_sources.get(event_id)
            or ""
        )
        status = pilot.classify_tsunami_potential(raw_text)
        for spec in pilot.tsunami_potential_specs(raw_text):
            row = pilot.build_attribute_row(
                dictionary, event_id, source_id, spec
            )
            if row is not None:
                rebuilt.append(row)
        summary.append(
            {
                "event_id": event_id,
                "event_title": event["event_title"],
                "event_primary_source_id": primary_sources.get(event_id, ""),
                "bmkg_potential_text": raw_text,
                "tsunami_potential_status": status,
                "status_confidence": (
                    "high"
                    if status in {"positive", "negative"}
                    else ("low" if raw_text else "unknown")
                ),
                "action": "migrated" if raw_text else "added_unknown",
            }
        )
    return attributes, cleaned + rebuilt, summary


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Buat snapshot turunan atribut potensi tsunami tanpa mengubah "
            "file pilot sumber."
        )
    )
    parser.add_argument(
        "--source-run",
        default=str(DEFAULT_SOURCE_RUN),
        help="Direktori run pilot sumber.",
    )
    parser.add_argument(
        "--fix-id",
        default="",
        help="ID direktori fix; default memakai timestamp UTC.",
    )
    args = parser.parse_args()

    source_run = Path(args.source_run)
    if not source_run.is_absolute():
        source_run = ROOT / source_run
    required = [
        source_run / "tables" / "event_attribute.csv",
        source_run / "tables" / "event.csv",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("File sumber tidak ditemukan: " + ", ".join(missing))

    fix_id = args.fix_id or (
        "FIX-TSUNAMI-" + pilot.utc_now().strftime("%Y%m%dT%H%M%SZ")
    )
    output_dir = pilot.PILOT_ROOT / "fixes" / fix_id
    if output_dir.exists():
        raise SystemExit(f"Direktori fix sudah ada: {output_dir}")

    dictionary = pilot.load_dictionary()
    attributes, rebuilt, summary = event_attribute_rows(
        source_run, dictionary
    )
    output_tables = output_dir / "tables"
    output_tables.mkdir(parents=True)
    for path in sorted((source_run / "tables").glob("*.csv")):
        if path.name == "event_attribute.csv":
            continue
        shutil.copy2(path, output_tables / path.name)
    attribute_fields = dictionary["event_attribute"]
    pilot.write_csv(
        output_tables / "event_attribute.csv", rebuilt, attribute_fields
    )
    summary_fields = [
        "event_id",
        "event_title",
        "event_primary_source_id",
        "bmkg_potential_text",
        "tsunami_potential_status",
        "status_confidence",
        "action",
    ]
    pilot.write_csv(
        output_dir / "tsunami_potential_fix_summary.csv",
        summary,
        summary_fields,
    )

    source_attribute_path = source_run / "tables" / "event_attribute.csv"
    output_attribute_path = output_tables / "event_attribute.csv"
    output_hashes = {
        path.name: pilot.sha256_file(path)
        for path in sorted(output_tables.glob("*.csv"))
    }
    categories = pilot.read_csv(output_tables / "category.csv")
    status_counts = Counter(row["tsunami_potential_status"] for row in summary)
    baseline = pilot.dataset_baseline.verify_dataset()
    manifest = {
        "fix_id": fix_id,
        "generated_at": pilot.iso_utc(),
        "source_run": str(source_run.relative_to(ROOT)).replace("\\", "/"),
        "source_event_attribute_sha256": pilot.sha256_file(
            source_attribute_path
        ),
        "source_event_attribute_rows": len(attributes),
        "output_event_attribute_sha256": pilot.sha256_file(
            output_attribute_path
        ),
        "output_event_attribute_rows": len(rebuilt),
        "tables_sha256": output_hashes,
        "baseline": {
            "path": pilot.dataset_baseline.DATASET_RELATIVE_PATH,
            "sha256": baseline["sha256"],
            "unchanged": (
                baseline["sha256"]
                == pilot.dataset_baseline.DATASET_SHA256
            ),
        },
        "mapping": {
            "bmkg_potential_text": "nilai mentah field Potensi BMKG",
            "tsunami_potential_status": "positive|negative|unknown",
            "removed": sorted(LEGACY_NAMES),
        },
        "counts": {
            "legacy_rows_removed": len(attributes)
            - len([r for r in attributes if r["attribute_name"] not in REPLACED_NAMES]),
            "raw_text_rows": sum(1 for row in summary if row["bmkg_potential_text"]),
            "status": dict(status_counts),
            "event_rows": len(summary),
        },
        "categories": dict(
            Counter(row["category_name"] for row in categories)
        ),
        "categories_unchanged": sorted(
            {row["category_name"] for row in categories}
        )
        == ["Gempabumi"],
        "events": summary,
    }
    pilot.write_json(output_dir / "fix_manifest.json", manifest)
    print(str(output_dir.relative_to(ROOT)))


if __name__ == "__main__":
    main()
