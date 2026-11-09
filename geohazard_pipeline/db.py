"""SQLite importer for pipeline tables and the preserved legacy baseline."""

import csv
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .schema import ENTITY_ORDER, PRIMARY_KEYS, TABLE_COLUMNS
from .util import ROOT, compact_id, iso_utc

SCHEMA_PATH = ROOT / "database" / "schema.sql"
DEFAULT_DB_PATH = ROOT / "database" / "geohazard.db"

NULLABLE_EMPTY_COLUMNS = {
    "document_source_id",
    "document_raw_payload_id",
    "event_primary_source_id",
    "source_id",
    "linked_event_id",
    "duplicate_of_document_id",
    "attribute_source_id",
    "run_id",
}


def connect(db_path=None):
    db_path = Path(db_path or DEFAULT_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path=None, schema_path=None):
    schema_path = Path(schema_path or SCHEMA_PATH)
    with closing(connect(db_path)) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
    return Path(db_path or DEFAULT_DB_PATH)


def _normalize(row, columns):
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
    columns = TABLE_COLUMNS[table]
    placeholders = ", ".join("?" for _ in columns)
    quoted = ", ".join(f'"{column}"' for column in columns)
    sql = (
        f'INSERT OR IGNORE INTO "{table}" ({quoted}) '
        f"VALUES ({placeholders})"
    )
    inserted = 0
    for row in rows:
        normalized = _normalize(row, columns)
        primary_key = PRIMARY_KEYS[table]
        if str(normalized.get(primary_key, "") or "") == "":
            raise ValueError(f"{table}: primary key {primary_key} kosong")
        cursor = connection.execute(sql, [normalized[column] for column in columns])
        inserted += cursor.rowcount
    return inserted


def import_tables(connection, tables, run_id=None, source_note=""):
    stats = {}
    for table in ENTITY_ORDER:
        rows = tables.get(table, [])
        stats[table] = {
            "rows": len(rows),
            "inserted": _insert_rows(connection, table, rows),
        }
    if run_id is None and tables.get("pipeline_run"):
        run_id = tables["pipeline_run"][0].get("run_id", "")
    imported_at = iso_utc()
    import_id = compact_id("IMP", f"{run_id}|{source_note}", 16)
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO import_log
        (import_id, run_id, imported_at, tables_json, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            import_id,
            run_id or None,
            imported_at,
            json.dumps(stats, ensure_ascii=False, sort_keys=True),
            "imported",
            source_note or "Import tabel pipeline ke SQLite.",
        ),
    )
    stats["import_log"] = {
        "rows": len(tables.get("import_log", [])) + 1,
        "inserted": cursor.rowcount,
    }
    return stats


def read_table_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def import_run_dir(db_path, run_dir, initialize=True):
    run_dir = Path(run_dir)
    tables_dir = run_dir / "tables"
    if not tables_dir.exists():
        raise FileNotFoundError(f"Direktori tabel tidak ditemukan: {tables_dir}")
    if initialize:
        initialize_database(db_path)
    tables = {}
    for table in ENTITY_ORDER:
        path = tables_dir / f"{table}.csv"
        if path.exists():
            tables[table] = read_table_csv(path)
    with closing(connect(db_path)) as connection:
        connection.execute("BEGIN")
        stats = import_tables(
            connection,
            tables,
            run_id=(tables.get("pipeline_run") or [{}])[0].get("run_id", ""),
            source_note=f"Import run dir {run_dir.name}.",
        )
        connection.commit()
        integrity = [
            dict(row) for row in connection.execute("PRAGMA foreign_key_check")
        ]
    return {"stats": stats, "foreign_key_check": integrity, "db_path": str(db_path)}


def import_baseline(db_path, tables, initialize=True):
    if initialize:
        initialize_database(db_path)
    with closing(connect(db_path)) as connection:
        connection.execute("BEGIN")
        stats = import_tables(
            connection,
            tables,
            run_id=(tables.get("pipeline_run") or [{}])[0].get("run_id", ""),
            source_note="Import baseline legacy 787 baris.",
        )
        connection.commit()
        integrity = [
            dict(row) for row in connection.execute("PRAGMA foreign_key_check")
        ]
    return {"stats": stats, "foreign_key_check": integrity, "db_path": str(db_path)}
