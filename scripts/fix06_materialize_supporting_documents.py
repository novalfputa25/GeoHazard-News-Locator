#!/usr/bin/env python3
"""FIX06: materialisasi dokumen pendukung BMKG Gempa Dirasakan."""

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import dataset_baseline
from geohazard_pipeline.build import (
    build_assertions,
    build_document,
    build_link,
    build_location_mention,
)
from geohazard_pipeline.db import (
    DEFAULT_DB_PATH,
    NULLABLE_EMPTY_COLUMNS,
    connect,
)
from geohazard_pipeline.schema import TABLE_COLUMNS
from geohazard_pipeline.util import (
    compact_id,
    document_identity,
    event_identity_for_bmkg,
    iso_utc,
    load_register,
    registry_to_source_row,
)
from scripts import pilot_collect_official_geohazard as pilot

FIX_ID = "FIX06-MATERIALIZE-SUPPORTING-DOCUMENTS"
SOURCE_ID = "bmkg_gempa_dirasakan"
CHANGED_BY = "system_fix06"
TARGETS = [
    {
        "label": "Oksibil",
        "document_id": "DOC-f887636094654d53",
        "event_id": "EVT-BMKG-72D9473D8378",
        "event_key": "BMKG|2026-10-29T03:26:49+00:00|-5.45|141.90|6.0",
        "external_id": (
            "bmkg_gempa_dirasakan|2026-10-29T03:26:49+00:00|"
            "-5.4500|141.9000|6.0"
        ),
    },
    {
        "label": "Tanimbar/FFB",
        "document_id": "DOC-cfd2f5df338e302d",
        "event_id": "EVT-BMKG-FFB357F335AE",
        "event_key": "BMKG|2026-10-28T22:06:47+00:00|-6.34|130.52|6.4",
        "external_id": (
            "bmkg_gempa_dirasakan|2026-10-28T22:06:47+00:00|"
            "-6.3400|130.5200|6.4"
        ),
    },
    {
        "label": "Gunungkidul",
        "document_id": "DOC-57dbfb14c6cc3343",
        "event_id": "EVT-BMKG-608A37F640B2",
        "event_key": "BMKG|2026-10-27T14:43:13+00:00|-9.20|110.39|5.4",
        "external_id": (
            "bmkg_gempa_dirasakan|2026-10-27T14:43:13+00:00|"
            "-9.2000|110.3900|5.4"
        ),
    },
]


def _candidate_run_dirs(run_roots=None):
    roots = run_roots or [
        ROOT / "data" / "pipeline",
        ROOT / "data" / "pilot" / "runs",
    ]
    candidates = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for path in root.iterdir():
            if path.is_dir() and (path / "tables" / "raw_payload.csv").is_file():
                candidates.append(path)
    return sorted(candidates, key=lambda path: path.name, reverse=True)


def _read_bytes(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    return path.read_bytes()


def _find_target_record(target, run_roots=None):
    config = {"source_id": SOURCE_ID, "priority": 2}
    for run_dir in _candidate_run_dirs(run_roots):
        raw_table = run_dir / "tables" / "raw_payload.csv"
        for raw_row in pilot.read_csv(raw_table):
            if raw_row.get("raw_payload_source_id") != SOURCE_ID:
                continue
            path = raw_row.get("raw_payload_path", "")
            if not path:
                continue
            content = _read_bytes(path)
            items, _error = pilot.parse_bmkg_items(content, config)
            for item in items:
                if item.get("external_id") != target["external_id"]:
                    continue
                return {
                    "run_dir": run_dir,
                    "run_id": run_dir.name,
                    "raw_row": raw_row,
                    "item": item,
                    "feed_url": raw_row.get("raw_payload_url", ""),
                }
    return None


def _prepare_item(record, register_row):
    item = dict(record["item"])
    item["source_id"] = SOURCE_ID
    item["category_original"] = "Gempabumi"
    item["feed_type"] = "bmkg_xml"
    item["published_at"] = None
    item["updated_at"] = None
    item["canonical_url"] = (
        f"{record['feed_url']}#record={quote(item['external_id'], safe='')}"
    )
    item["register_row"] = register_row
    item["retrieved_at"] = record["raw_row"]["raw_payload_retrieved_at"]
    item["raw_payload_id"] = record["raw_row"]["raw_payload_id"]
    return item


def _normalize_row(row, columns):
    result = {}
    for column in columns:
        value = row.get(column, "")
        if value is None:
            value = ""
        if column in NULLABLE_EMPTY_COLUMNS and str(value) == "":
            value = None
        result[column] = value
    return result


def _insert_rows(connection, table, rows):
    if not rows:
        return 0
    columns = TABLE_COLUMNS[table]
    placeholders = ", ".join("?" for _ in columns)
    quoted = ", ".join(f'"{column}"' for column in columns)
    sql = (
        f'INSERT OR IGNORE INTO "{table}" ({quoted}) '
        f"VALUES ({placeholders})"
    )
    inserted = 0
    for row in rows:
        normalized = _normalize_row(row, columns)
        cursor = connection.execute(
            sql, [normalized[column] for column in columns]
        )
        inserted += cursor.rowcount
    return inserted


def _row_dict(row):
    return dict(row) if row is not None else None


def _source_row(connection, record, register):
    existing = _row_dict(
        connection.execute(
            "SELECT * FROM source WHERE source_id = ?", (SOURCE_ID,)
        ).fetchone()
    )
    if existing:
        return existing
    from feeds import FEEDS

    feed = next((row for row in FEEDS if row.get("id") == SOURCE_ID), None)
    if feed is None:
        raise RuntimeError(f"Konfigurasi feed {SOURCE_ID} tidak ditemukan.")
    config = dict(feed)
    config["source_id"] = SOURCE_ID
    source = registry_to_source_row(
        register[SOURCE_ID],
        config,
        record["raw_row"].get("raw_payload_http_status", ""),
        record["raw_row"].get("raw_payload_retrieved_at", ""),
    )
    _insert_rows(connection, "source", [source])
    return source


def _ensure_raw_payload(connection, raw_row):
    existing = _row_dict(
        connection.execute(
            "SELECT * FROM raw_payload WHERE raw_payload_id = ?",
            (raw_row["raw_payload_id"],),
        ).fetchone()
    )
    if existing:
        return existing, False
    _insert_rows(connection, "raw_payload", [raw_row])
    return raw_row, True


def _existing_document(connection, target):
    rows = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM document "
            "WHERE document_id = ? OR document_external_id = ?",
            (target["document_id"], target["external_id"]),
        )
    ]
    if not rows:
        return None
    if len(rows) > 1 or rows[0]["document_id"] != target["document_id"]:
        raise RuntimeError(
            f"Konflik identitas dokumen untuk {target['label']}: {rows}"
        )
    return rows[0]


def _ensure_link(connection, item, event_id, created_at):
    existing = _row_dict(
        connection.execute(
            "SELECT * FROM document_event_link "
            "WHERE document_id = ? AND event_id = ?",
            (item["document_id"], event_id),
        ).fetchone()
    )
    if existing:
        if (
            existing["relevance"] != "supporting"
            or existing["is_primary"] != "tidak"
        ):
            raise RuntimeError(
                f"Link {existing['link_id']} bukan link supporting."
            )
        return existing, False
    link = build_link(item, event_id, False, created_at)
    link["link_created_by"] = CHANGED_BY
    _insert_rows(connection, "document_event_link", [link])
    return link, True


def _ensure_auxiliary_rows(connection, item, event_id, document_row):
    inserted = {}
    classification = build_document(
        item,
        {
            "source_id": document_row["document_source_id"],
            "source_name": document_row["document_source_label"],
            "source_type": document_row["document_source_type"],
            "source_role": document_row["document_source_role"],
            "source_language": document_row["document_language"],
            "source_institution": document_row["document_publisher"],
        },
        {
            "raw_payload_id": document_row["document_raw_payload_id"],
            "raw_payload_retrieved_at": document_row["document_retrieved_at"],
            "raw_payload_status": "stored",
        },
        document_row["document_run_id"],
    )[1]
    existing = connection.execute(
        "SELECT 1 FROM document_classification WHERE document_id = ?",
        (item["document_id"],),
    ).fetchone()
    if not existing:
        _insert_rows(connection, "document_classification", [classification])
        inserted.setdefault("document_classification", []).append(
            classification
        )

    mention = build_location_mention(item, event_id)
    if mention:
        existing = connection.execute(
            "SELECT 1 FROM location_mention WHERE document_id = ? AND linked_event_id = ?",
            (item["document_id"], event_id),
        ).fetchone()
        if not existing:
            _insert_rows(connection, "location_mention", [mention])
            inserted.setdefault("location_mention", []).append(mention)

    assertions = build_assertions(item, event_id)
    missing_assertions = []
    for assertion in assertions:
        existing = connection.execute(
            "SELECT 1 FROM event_assertion WHERE assertion_id = ?",
            (assertion["assertion_id"],),
        ).fetchone()
        if not existing:
            missing_assertions.append(assertion)
    if missing_assertions:
        _insert_rows(connection, "event_assertion", missing_assertions)
        inserted.setdefault("event_assertion", []).extend(
            missing_assertions
        )
    return inserted


def _change_log_rows(inserted_rows, changed_at):
    rows = []
    for table, rows_for_table in inserted_rows.items():
        key = TABLE_COLUMNS[table][0]
        for row in rows_for_table:
            target_id = row.get(key, "")
            if not target_id:
                continue
            rows.append(
                {
                    "change_id": compact_id("CHG", f"{table}|{target_id}", 16),
                    "target_type": table,
                    "target_id": target_id,
                    "change_type": "create",
                    "changed_at": changed_at,
                    "changed_by": CHANGED_BY,
                    "change_reason": (
                        "Materialisasi dokumen pendukung FIX06 dari raw payload "
                        "resmi yang sudah tersimpan."
                    ),
                    "schema_version": "1.0.0",
                    "manual_review": "tidak",
                }
            )
    return rows


def _snapshot(connection):
    def rows(sql):
        return [
            json.dumps(dict(row), ensure_ascii=False, sort_keys=True)
            for row in connection.execute(sql)
        ]

    counts = {}
    for table in (
        "document",
        "document_event_link",
        "event",
        "raw_payload",
        "category",
        "event_time",
        "event_location",
    ):
        counts[table] = connection.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]
    raw_payload = {
        row["raw_payload_id"]: json.dumps(
            dict(row), ensure_ascii=False, sort_keys=True
        )
        for row in connection.execute(
            "SELECT * FROM raw_payload ORDER BY raw_payload_id"
        )
    }
    return {
        "counts": counts,
        "event_ids": sorted(
            row[0] for row in connection.execute("SELECT event_id FROM event")
        ),
        "category_rows": rows("SELECT * FROM category ORDER BY category_assignment_id"),
        "event_time_rows": rows(
            "SELECT * FROM event_time ORDER BY event_time_id"
        ),
        "event_location_rows": rows(
            "SELECT * FROM event_location ORDER BY event_location_id"
        ),
        "raw_payload": raw_payload,
    }


def _target_state(connection, target):
    documents = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM document WHERE document_id = ?",
            (target["document_id"],),
        )
    ]
    links = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM document_event_link "
            "WHERE document_id = ? AND event_id = ?",
            (target["document_id"], target["event_id"]),
        )
    ]
    duplicates = connection.execute(
        "SELECT COUNT(*) FROM document WHERE document_external_id = ?",
        (target["external_id"],),
    ).fetchone()[0]
    return {
        "documents": documents,
        "links": links,
        "document_count_by_external_id": duplicates,
    }


def _validate(connection, targets, before, after, baseline_before, baseline_after):
    checks = {}
    checks["event_count_unchanged"] = (
        before["counts"]["event"] == after["counts"]["event"]
    )
    checks["event_ids_unchanged"] = before["event_ids"] == after["event_ids"]
    checks["category_unchanged"] = (
        before["category_rows"] == after["category_rows"]
    )
    checks["event_time_unchanged"] = (
        before["event_time_rows"] == after["event_time_rows"]
    )
    checks["event_location_unchanged"] = (
        before["event_location_rows"] == after["event_location_rows"]
    )
    checks["existing_raw_payload_unchanged"] = all(
        after["raw_payload"].get(raw_id) == value
        for raw_id, value in before["raw_payload"].items()
    )
    checks["baseline_unchanged"] = (
        baseline_before["sha256"] == baseline_after["sha256"]
        and baseline_after["rows"] == 787
        and baseline_after["columns"] == 51
    )
    checks["foreign_key_check"] = (
        list(connection.execute("PRAGMA foreign_key_check")) == []
    )

    target_states = {}
    target_checks = []
    for target in targets:
        state = _target_state(connection, target)
        target_states[target["label"]] = state
        documents = state["documents"]
        links = state["links"]
        ok = (
            len(documents) == 1
            and state["document_count_by_external_id"] == 1
            and len(links) == 1
            and links[0]["event_id"] == target["event_id"]
            and links[0]["relevance"] == "supporting"
            and links[0]["is_primary"] == "tidak"
            and links[0]["link_status"] == "active"
            and documents[0]["document_source_id"] == SOURCE_ID
            and documents[0]["document_raw_payload_id"] is not None
        )
        target_checks.append(ok)
    checks["three_documents_present"] = all(
        len(state["documents"]) == 1 for state in target_states.values()
    )
    checks["three_supporting_links_present"] = all(
        len(state["links"]) == 1
        and state["links"][0]["relevance"] == "supporting"
        and state["links"][0]["is_primary"] == "tidak"
        for state in target_states.values()
    )
    checks["target_rows_valid"] = all(target_checks)
    checks["no_target_document_duplicates"] = all(
        state["document_count_by_external_id"] == 1
        for state in target_states.values()
    )
    checks["no_target_link_duplicates"] = all(
        len(state["links"]) == 1 for state in target_states.values()
    )
    return checks, target_states


def apply_fix06(database=None, dry_run=False, run_roots=None):
    database = Path(database or DEFAULT_DB_PATH)
    if not database.is_file():
        raise FileNotFoundError(f"Database tidak ditemukan: {database}")
    register = load_register()
    baseline_before = dataset_baseline.verify_dataset()
    changed_at = iso_utc()
    inserted = {}
    records = {}

    with closing(connect(database)) as connection:
        connection.execute("BEGIN")
        before = _snapshot(connection)
        try:
            for target in TARGETS:
                record = _find_target_record(target, run_roots)
                if record is None:
                    raise RuntimeError(
                        f"Raw record {target['label']} tidak ditemukan."
                    )
                item = _prepare_item(record, register[SOURCE_ID])
                computed_document_id, _canonical = document_identity(
                    SOURCE_ID, item["external_id"], item["canonical_url"]
                )
                computed_event_id, _native = event_identity_for_bmkg(item)
                if computed_document_id != target["document_id"]:
                    raise RuntimeError(
                        f"Document ID {target['label']} tidak sesuai: "
                        f"{computed_document_id} != {target['document_id']}"
                    )
                if computed_event_id != target["event_id"]:
                    raise RuntimeError(
                        f"Event ID {target['label']} tidak sesuai: "
                        f"{computed_event_id} != {target['event_id']}"
                    )
                event_exists = connection.execute(
                    "SELECT 1 FROM event WHERE event_id = ?",
                    (target["event_id"],),
                ).fetchone()
                if not event_exists:
                    raise RuntimeError(
                        f"Event {target['event_id']} tidak ada; FIX06 tidak "
                        "membuat event baru."
                    )

                source_row = _source_row(connection, record, register)
                raw_row, raw_inserted = _ensure_raw_payload(
                    connection, record["raw_row"]
                )
                if raw_inserted:
                    inserted.setdefault("raw_payload", []).append(raw_row)

                document = _existing_document(connection, target)
                document_created = document is None
                if document_created:
                    document, classification = build_document(
                        item, source_row, raw_row, record["run_id"]
                    )
                    _insert_rows(connection, "document", [document])
                    inserted.setdefault("document", []).append(document)
                    _insert_rows(
                        connection, "document_classification", [classification]
                    )
                    inserted.setdefault("document_classification", []).append(
                        classification
                    )
                    document = dict(
                        connection.execute(
                            "SELECT * FROM document WHERE document_id = ?",
                            (target["document_id"],),
                        ).fetchone()
                    )
                item["document_id"] = document["document_id"]

                link, link_inserted = _ensure_link(
                    connection,
                    item,
                    target["event_id"],
                    document["document_retrieved_at"] or changed_at,
                )
                if link_inserted:
                    inserted.setdefault("document_event_link", []).append(link)

                auxiliary = _ensure_auxiliary_rows(
                    connection, item, target["event_id"], document
                )
                for table, rows in auxiliary.items():
                    inserted.setdefault(table, []).extend(rows)
                records[target["label"]] = {
                    "document_id": document["document_id"],
                    "event_id": target["event_id"],
                    "link_id": link["link_id"],
                    "raw_payload_id": document["document_raw_payload_id"],
                    "document_status": "materialized"
                    if document_created
                    else "existing",
                }

            change_rows = _change_log_rows(inserted, changed_at)
            if change_rows:
                _insert_rows(connection, "change_log", change_rows)
                inserted["change_log"] = change_rows

            import_stats = {
                table: len(rows) for table, rows in inserted.items()
            }
            import_row = {
                "import_id": compact_id("IMP", FIX_ID, 16),
                "run_id": FIX_ID,
                "imported_at": changed_at,
                "tables_json": json.dumps(
                    import_stats, ensure_ascii=False, sort_keys=True
                ),
                "status": "imported",
                "notes": (
                    "FIX06 materialisasi tiga dokumen pendukung BMKG Gempa "
                    "Dirasakan dan link supporting; idempotent."
                ),
            }
            _insert_rows(connection, "import_log", [import_row])

            after = _snapshot(connection)
            baseline_after = dataset_baseline.verify_dataset()
            checks, target_states = _validate(
                connection,
                TARGETS,
                before,
                after,
                baseline_before,
                baseline_after,
            )
            if not all(checks.values()):
                failed = [key for key, value in checks.items() if not value]
                raise RuntimeError(f"Validasi FIX06 gagal: {failed}")

            if dry_run:
                connection.rollback()
            else:
                connection.commit()
        except Exception:
            connection.rollback()
            raise

    return {
        "fix_id": FIX_ID,
        "database": str(database),
        "dry_run": dry_run,
        "targets": records,
        "counts_before": before["counts"],
        "counts_after": after["counts"],
        "inserted": {
            table: len(rows) for table, rows in inserted.items()
        },
        "checks": checks,
        "target_state": {
            label: {
                "document_id": state["documents"][0]["document_id"]
                if state["documents"]
                else None,
                "event_id": state["links"][0]["event_id"]
                if state["links"]
                else None,
                "link_id": state["links"][0]["link_id"]
                if state["links"]
                else None,
                "relevance": state["links"][0]["relevance"]
                if state["links"]
                else None,
                "is_primary": state["links"][0]["is_primary"]
                if state["links"]
                else None,
                "raw_payload_id": state["documents"][0][
                    "document_raw_payload_id"
                ]
                if state["documents"]
                else None,
            }
            for label, state in target_states.items()
        },
        "baseline_before": baseline_before,
        "baseline_after": baseline_after,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Materialisasi tiga dokumen BMKG Gempa Dirasakan menjadi document "
            "dan link supporting secara idempotent."
        )
    )
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DB_PATH),
        help=f"Path SQLite (default: {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validasi tanpa commit perubahan.",
    )
    parser.add_argument(
        "--run-root",
        action="append",
        default=None,
        help="Root run tambahan yang berisi direktori tabel/raw_payload.csv.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Cetak ringkasan JSON lengkap.",
    )
    args = parser.parse_args(argv)
    result = apply_fix06(
        database=args.database,
        dry_run=args.dry_run,
        run_roots=args.run_root,
    )
    if args.json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    print(f"Fix ID: {result['fix_id']}")
    print(f"Database: {result['database']}")
    print(f"Dry run: {result['dry_run']}")
    for label, state in result["target_state"].items():
        print(
            f"{label}: document={state['document_id']} "
            f"event={state['event_id']} link={state['link_id']} "
            f"relevance={state['relevance']} raw={state['raw_payload_id']}"
        )
    print(
        "Document: {before} -> {after}; Link: {link_before} -> {link_after}; "
        "Event: {event_before} -> {event_after}".format(
            before=result["counts_before"]["document"],
            after=result["counts_after"]["document"],
            link_before=result["counts_before"]["document_event_link"],
            link_after=result["counts_after"]["document_event_link"],
            event_before=result["counts_before"]["event"],
            event_after=result["counts_after"]["event"],
        )
    )
    print(f"Inserted: {result['inserted']}")
    print(f"Checks: {result['checks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
