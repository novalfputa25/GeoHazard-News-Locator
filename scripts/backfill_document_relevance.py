"""Backfill the FIX07 document relevance status without deleting data.

The script reads the preserved baseline CSV and stored raw payloads as context,
classifies every active document, and upserts ``document_relevance``.  It never
updates ``document``, ``document_classification``, ``event``, or raw payloads.
"""

import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import feedparser

from geohazard_pipeline.db import DEFAULT_DB_PATH, initialize_database
from geohazard_pipeline.util import (
    BASELINE_PATH,
    BASELINE_SHA256,
    file_sha256,
    iso_utc,
    sha256_text,
    strip_html,
)
from relevance import CLASSIFIER_VERSION, classify_relevance


def _document_id(url):
    return "DOC-" + sha256_text(url)[:16]


def _normalize_title(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def load_baseline_context(path=BASELINE_PATH):
    path = Path(path)
    actual = file_sha256(path)
    if actual != BASELINE_SHA256:
        raise ValueError(
            f"Hash baseline tidak cocok: {actual} != {BASELINE_SHA256}"
        )
    context = {}
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            url = str(row.get("url", "")).strip()
            if not url:
                continue
            document_id = _document_id(url)
            context[document_id] = {
                "title": row.get("judul", ""),
                "content": row.get("isi_berita", ""),
                "category": row.get("kategori", ""),
                "source": row.get("sumber", ""),
                "url": url,
            }
    return context


def load_raw_context(connection):
    by_url = {}
    by_title = {}
    rows = connection.execute(
        """
        SELECT raw_payload_path
        FROM raw_payload
        WHERE raw_payload_status = 'stored'
          AND raw_payload_path IS NOT NULL
          AND raw_payload_path <> ''
        """
    ).fetchall()
    for row in rows:
        path = Path(row[0])
        if not path.is_absolute():
            path = ROOT / path
        if not path.is_file():
            continue
        try:
            parsed = feedparser.parse(path.read_bytes())
        except Exception:
            continue
        for entry in parsed.entries:
            title = strip_html(entry.get("title", ""))
            link = entry.get("link", "") or entry.get("id", "")
            summary = ""
            content_value = entry.get("content")
            if isinstance(content_value, list) and content_value:
                summary = content_value[0].get("value", "")
            summary = summary or entry.get("summary") or entry.get("description") or ""
            summary = strip_html(summary)
            if link:
                by_url[str(link)] = summary
            if title:
                by_title[_normalize_title(title)] = summary
    return by_url, by_title


def _classification_map(connection):
    rows = connection.execute(
        """
        SELECT document_id, category_name
        FROM document_classification
        ORDER BY
            CASE category_scope WHEN 'in_scope' THEN 0 ELSE 1 END,
            classification_id
        """
    ).fetchall()
    result = {}
    for document_id, category in rows:
        result.setdefault(document_id, category)
    return result


def _document_rows(connection):
    return connection.execute(
        """
        SELECT
            d.document_id,
            d.document_title,
            d.document_type,
            d.document_source_label,
            d.document_source_type,
            d.document_url,
            d.document_url_canonical
        FROM document d
        WHERE d.document_status = 'active'
        ORDER BY d.document_id
        """
    ).fetchall()


def _upsert(connection, row):
    connection.execute(
        """
        INSERT INTO document_relevance (
            document_id, relevance_status, relevance_category,
            relevance_basis, relevance_confidence, relevance_evidence,
            classifier_version, classified_at, review_status,
            reviewed_at, reviewed_by, relevance_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(document_id) DO UPDATE SET
            relevance_status = excluded.relevance_status,
            relevance_category = excluded.relevance_category,
            relevance_basis = excluded.relevance_basis,
            relevance_confidence = excluded.relevance_confidence,
            relevance_evidence = excluded.relevance_evidence,
            classifier_version = excluded.classifier_version,
            classified_at = excluded.classified_at,
            relevance_notes = excluded.relevance_notes
        WHERE document_relevance.review_status IS NULL
           OR document_relevance.review_status <> 'reviewed'
        """,
        (
            row["document_id"],
            row["relevance_status"],
            row["relevance_category"],
            row["relevance_basis"],
            row["relevance_confidence"],
            row["relevance_evidence"],
            row["classifier_version"],
            row["classified_at"],
            row["review_status"],
            row["reviewed_at"],
            row["reviewed_by"],
            row["relevance_notes"],
        ),
    )


def backfill(db_path=DEFAULT_DB_PATH, dry_run=False):
    db_path = Path(db_path)
    initialize_database(db_path)
    baseline = load_baseline_context()
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    try:
        raw_by_url, raw_by_title = load_raw_context(connection)
        classifications = _classification_map(connection)
        documents = _document_rows(connection)
        counts = Counter()
        category_counts = Counter()
        missing_context = 0
        rows = []
        now = iso_utc()
        for document in documents:
            document_id = document["document_id"]
            base = baseline.get(document_id)
            url = document["document_url_canonical"] or document["document_url"] or ""
            title = document["document_title"] or ""
            content = ""
            category_hint = classifications.get(document_id, "")
            source_label = document["document_source_label"] or ""
            source_type = document["document_source_type"] or ""
            if base:
                content = base.get("content", "")
                category_hint = category_hint or base.get("category", "")
                source_label = source_label or base.get("source", "")
            else:
                content = raw_by_url.get(url, "") or raw_by_title.get(
                    _normalize_title(title), ""
                )
            if not content:
                missing_context += 1
            if not source_type:
                source_type = (
                    "official"
                    if document["document_type"] == "official_event_record"
                    or source_label in {"BMKG", "USGS", "GDACS"}
                    else "news"
                )
            decision = classify_relevance(
                title,
                content,
                category_hint,
                source_label,
                source_type,
            )
            counts[decision["relevance_status"]] += 1
            category_counts[decision["relevance_category"]] += 1
            rows.append(
                {
                    "document_id": document_id,
                    "relevance_status": decision["relevance_status"],
                    "relevance_category": decision["relevance_category"],
                    "relevance_basis": decision["relevance_basis"],
                    "relevance_confidence": decision["relevance_confidence"],
                    "relevance_evidence": decision["relevance_evidence"],
                    "classifier_version": decision["classifier_version"],
                    "classified_at": now,
                    "review_status": "not_reviewed",
                    "reviewed_at": "",
                    "reviewed_by": "",
                    "relevance_notes": (
                        "Backfill FIX07 otomatis; konteks dari baseline/raw payload."
                    ),
                }
            )
        if not dry_run:
            connection.execute("BEGIN")
            for row in rows:
                _upsert(connection, row)
            connection.commit()
        return {
            "db_path": str(db_path),
            "dry_run": dry_run,
            "documents": len(documents),
            "missing_context": missing_context,
            "status_counts": dict(counts),
            "category_counts": dict(category_counts),
            "classifier_version": CLASSIFIER_VERSION,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Backfill status relevansi dokumen GeoHazard (FIX07)."
    )
    parser.add_argument("--database", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = backfill(args.database, dry_run=args.dry_run)
    if args.as_json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
