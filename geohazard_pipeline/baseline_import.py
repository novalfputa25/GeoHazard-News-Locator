"""Convert the preserved 787-row baseline into legacy database rows.

The baseline is imported as a legacy snapshot: source identity is label-only,
raw payload and run are absent, and any event is a candidate, not a confirmed
fact.
"""

import csv
import json
from pathlib import Path

import geographic_scope as geo

from relevance import classify_relevance

from .schema import empty_row
from .util import (
    BASELINE_PATH,
    BASELINE_SHA256,
    SCOPE_IN,
    SCOPE_OUT,
    SCOPE_UNCLASSIFIED,
    TARGET_CATEGORIES,
    compact_id,
    file_sha256,
    parse_datetime,
    sha256_text,
)

BASELINE_RUN_ID = "LEGACY-BASELINE-20261101T150501Z"
BASELINE_IMPORTED_AT = "2026-11-01T15:05:01+00:00"


def _split(value):
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


def _document_id(url):
    return "DOC-" + sha256_text(url)[:16]


def _scope(row):
    status = str(row.get("status_cakupan", "")).strip()
    if status == "dalam_8_kategori":
        return SCOPE_IN
    if status == "di_luar_8_kategori":
        return SCOPE_OUT
    if str(row.get("kategori", "")) in TARGET_CATEGORIES:
        return SCOPE_IN
    return SCOPE_UNCLASSIFIED


def _location_name(row):
    parts = [
        row.get("provinsi", ""),
        row.get("kabupaten_kota", ""),
        row.get("kecamatan", ""),
        row.get("desa_kelurahan", ""),
        row.get("dusun_kampung", ""),
        row.get("alamat_detail", ""),
    ]
    return ", ".join(part.strip() for part in parts if part and part.strip())


def _inside_indonesia(row, lat, lon):
    domain = str(row.get("domain_lokasi", "")).strip()
    if domain == "indonesia":
        return "ya"
    if domain in {"luar_indonesia", "internasional"}:
        return "tidak"
    if lat not in ("", None) and lon not in ("", None):
        result = geo.classify_location(
            _location_name(row), lat, lon, "source_coordinate", "legacy_baseline"
        )
        return result["is_inside_indonesia"]
    return "tidak_diketahui"


def _time_row(row, event_id):
    raw = str(row.get("event_time", "")).strip()
    status = str(row.get("event_time_status", "")).strip()
    if not raw:
        return None
    parsed = parse_datetime(raw)
    kind_map = {
        "prediksi_nowcast": "nowcast",
        "nowcast": "nowcast",
        "prakiraan": "forecast",
        "forecast": "forecast",
        "perkiraan": "estimated",
    }
    kind = kind_map.get(str(row.get("event_time_jenis", "")).strip(), "actual")
    basis_map = {
        "bmkg_tanggal": "official_field",
        "bmkg_nowcast": "official_field",
        "usgs_time": "official_field",
        "gdacs_start": "official_field",
        "gdacs_judul": "official_field",
        "isi_berita": "news_text",
        "isi_berita_tanpa_zona": "news_text",
    }
    basis = basis_map.get(str(row.get("event_time_basis", "")).strip(), "news_text")
    timezone = str(row.get("event_time_zona", "")).strip() or "Etc/UTC"
    row_time = empty_row("event_time")
    row_time.update(
        {
            "event_time_id": compact_id("TIME", event_id, 12),
            "event_id": event_id,
            "event_time_status": "unknown",
            "event_time_basis": basis,
            "event_time_kind": kind,
            "event_time_timezone": timezone,
        }
    )
    if status == "perlu_review":
        row_time.update(
            {
                "event_time": "",
                "event_time_candidate_text": raw,
                "event_time_status": "manual_review",
                "event_time_basis": "manual_review",
                "event_time_review_reason": str(
                    row.get("event_time_evidence", "")
                ),
                "event_time_precision": "unknown",
                "event_time_confidence": "low",
            }
        )
        return row_time
    if parsed is None:
        row_time.update(
            {
                "event_time": "",
                "event_time_candidate_text": raw,
                "event_time_status": "manual_review",
                "event_time_basis": "manual_review",
                "event_time_review_reason": "Nilai waktu legacy tidak dapat diparse.",
                "event_time_precision": "unknown",
                "event_time_confidence": "low",
            }
        )
        return row_time
    precision = "second"
    if status == "tanggal_saja":
        precision = "day"
    elif parsed.second == 0 and parsed.minute == 0:
        precision = "hour"
    elif parsed.second == 0:
        precision = "minute"
    row_time.update(
        {
            "event_time": parsed.isoformat(),
            "event_time_precision": precision,
            "event_time_status": "date_only" if precision == "day" else "extracted",
            "event_time_evidence": str(row.get("event_time_evidence", "")),
            "event_time_confidence": "medium",
        }
    )
    return row_time


def _location_row(row, event_id):
    lat = str(row.get("latitude", "")).strip()
    lon = str(row.get("longitude", "")).strip()
    has_coords = lat not in ("", "None", "nan") and lon not in ("", "None", "nan")
    row_location = empty_row("event_location")
    row_location.update(
        {
            "event_location_id": compact_id("LOCE", event_id, 12),
            "event_id": event_id,
            "location_name": _location_name(row),
            "location_role": (
                "epicenter" if row.get("kategori") == "Gempabumi" else "event_area"
            ),
            "admin_province": row.get("provinsi", ""),
            "admin_kabupaten_kota": row.get("kabupaten_kota", ""),
            "admin_kecamatan": row.get("kecamatan", ""),
            "admin_desa_kelurahan": row.get("desa_kelurahan", ""),
            "latitude": f"{float(lat):.6f}" if has_coords else "",
            "longitude": f"{float(lon):.6f}" if has_coords else "",
            "coordinate_source": "source_document" if has_coords else "",
            "coordinate_status": (
                "source_coordinate" if has_coords else "not_available"
            ),
            "coordinate_precision": "point" if has_coords else "",
            "coordinate_confidence": "medium" if has_coords else "unknown",
            "is_inside_indonesia": _inside_indonesia(row, lat, lon),
            "location_evidence": (
                "Baseline legacy: kolom lokasi/koordinat; "
                f"koordinat_status={row.get('koordinat_status', '')}; "
                f"lokasi_basis={row.get('lokasi_basis', '')}"
            ),
            "location_notes": "Data legacy tanpa raw payload; belum diverifikasi manual.",
        }
    )
    return row_location


def _category_row(row, event_id):
    category_name = str(row.get("kategori", "")).strip() or "Lainnya"
    scope = _scope(row)
    row_category = empty_row("category")
    row_category.update(
        {
            "category_assignment_id": compact_id("CAT", event_id, 12),
            "event_id": event_id,
            "category_name": category_name,
            "category_rank": "primary",
            "category_scope": scope,
            "category_basis": "legacy_label",
            "category_confidence": "medium",
            "category_review_status": "not_reviewed",
            "category_original": row.get("kategori_asal", "") or category_name,
            "category_notes": (
                "Kategori diimpor dari baseline legacy; bukan klasifikasi baru."
            ),
        }
    )
    return row_category


def _assertions(row, event_id, document_id, event_time_row):
    values = []
    if event_time_row and event_time_row.get("event_time"):
        values.append(
            (
                "event_time",
                event_time_row["event_time"],
                event_time_row.get("event_time_evidence", ""),
            )
        )
    if str(row.get("latitude", "")).strip() not in ("", "None", "nan"):
        values.append(("latitude", row["latitude"], "Kolom latitude baseline"))
        values.append(("longitude", row["longitude"], "Kolom longitude baseline"))
    if _location_name(row):
        values.append(("location_name", _location_name(row), "Kolom lokasi baseline"))
    if row.get("kategori"):
        values.append(("category", row["kategori"], "Kolom kategori baseline"))
    rows = []
    for field_name, value, evidence in values:
        assertion = empty_row("event_assertion")
        assertion.update(
            {
                "assertion_id": compact_id(
                    "AST", f"{event_id}|{field_name}|legacy", 16
                ),
                "event_id": event_id,
                "document_id": document_id,
                "source_id": "",
                "field_name": field_name,
                "asserted_value": str(value),
                "assertion_status": "proposed",
                "assertion_confidence": "medium",
                "assertion_evidence": evidence,
                "asserted_at": BASELINE_IMPORTED_AT,
                "assertion_notes": "Klaim legacy; belum diverifikasi.",
            }
        )
        rows.append(assertion)
    return rows


def build_baseline_rows(path=BASELINE_PATH):
    path = Path(path)
    actual_hash = file_sha256(path)
    if actual_hash != BASELINE_SHA256:
        raise ValueError(
            f"Hash baseline tidak cocok: {actual_hash} != {BASELINE_SHA256}"
        )
    tables = {
        "document": [],
        "document_classification": [],
        "document_relevance": [],
        "document_duplicate": [],
        "event": [],
        "event_time": [],
        "event_location": [],
        "category": [],
        "document_event_link": [],
        "event_assertion": [],
        "event_relation": [],
        "verification": [],
        "change_log": [],
        "event_attribute": [],
        "pipeline_run": [],
        "import_log": [],
    }
    events = 0
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            url = str(row.get("url", "")).strip()
            if not url:
                continue
            document_id = _document_id(url)
            category = str(row.get("kategori", "")).strip() or "Lainnya"
            scope = _scope(row)
            document = empty_row("document")
            document.update(
                {
                    "document_id": document_id,
                    "document_type": (
                        "official_event_record"
                        if str(row.get("sumber", "")).strip()
                        in {"BMKG", "USGS", "GDACS"}
                        else "news_article"
                    ),
                    "document_source_id": "",
                    "document_source_label": row.get("sumber", ""),
                    "document_source_identity_status": "legacy_label_only",
                    "document_source_type": "unknown",
                    "document_source_role": "unknown",
                    "document_url": url,
                    "document_url_canonical": url,
                    "document_title": row.get("judul", ""),
                    "document_publisher": row.get("sumber", ""),
                    "document_author": "",
                    "document_language": "id",
                    "document_external_id": "",
                    "document_legacy_row_ref": f"data-index:{index}",
                    "document_content_hash": sha256_text(
                        f"{row.get('judul', '')}\n{row.get('isi_berita', '')}"
                    ),
                    "document_raw_payload_id": "",
                    "document_published_at": parse_datetime(
                        row.get("published_time", "")
                    ).isoformat()
                    if parse_datetime(row.get("published_time", ""))
                    else "",
                    "document_retrieved_at": "",
                    "document_updated_at": "",
                    "document_run_id": BASELINE_RUN_ID,
                    "document_status": "active",
                    "document_provenance_status": "legacy_incomplete",
                    "document_notes": (
                        "Baseline legacy; tidak ada raw payload/run. "
                        f"Baris data-index:{index}."
                    ),
                }
            )
            tables["document"].append(document)

            classification = empty_row("document_classification")
            classification.update(
                {
                    "classification_id": compact_id(
                        "CLS", f"{document_id}|{category}", 16
                    ),
                    "document_id": document_id,
                    "category_name": category,
                    "category_scope": scope,
                    "category_basis": "legacy_label",
                    "category_confidence": "medium",
                    "category_evidence": (
                        "Kolom kategori/status_cakupan baseline legacy."
                    ),
                    "classified_at": BASELINE_IMPORTED_AT,
                    "review_status": "not_reviewed",
                }
            )
            tables["document_classification"].append(classification)

            relevance = empty_row("document_relevance")
            decision = classify_relevance(
                row.get("judul", ""),
                row.get("isi_berita", ""),
                category,
                row.get("sumber", ""),
                "news",
            )
            relevance.update(
                {
                    "document_id": document_id,
                    "relevance_status": decision["relevance_status"],
                    "relevance_category": decision["relevance_category"],
                    "relevance_basis": decision["relevance_basis"],
                    "relevance_confidence": decision["relevance_confidence"],
                    "relevance_evidence": decision["relevance_evidence"],
                    "classifier_version": decision["classifier_version"],
                    "classified_at": BASELINE_IMPORTED_AT,
                    "review_status": "not_reviewed",
                    "reviewed_at": "",
                    "reviewed_by": "",
                    "relevance_notes": (
                        "Klasifikasi relevansi otomatis dari baseline legacy; "
                        "belum direview manual."
                    ),
                }
            )
            tables["document_relevance"].append(relevance)

            duplicate_reason = []
            for field, label in (
                ("duplikat_url", "url_sama"),
                ("duplikat_judul", "judul_sama"),
                ("duplikat_isi", "isi_sama"),
            ):
                if str(row.get(field, "")).strip().lower() in {"ya", "true", "1"}:
                    duplicate_reason.append(label)
            reference = str(row.get("duplikat_dengan", "")).strip()
            if duplicate_reason and reference.startswith("http"):
                tables["document_duplicate"].append(
                    {
                        "duplicate_id": compact_id(
                            "DUPDOC", document_id, 16
                        ),
                        "document_id": document_id,
                        "duplicate_of_document_id": _document_id(reference),
                        "duplicate_reason": "+".join(duplicate_reason),
                        "duplicate_confidence": "medium",
                        "detected_at": BASELINE_IMPORTED_AT,
                    }
                )

            if category not in TARGET_CATEGORIES:
                continue
            time_row = _time_row(row, "PENDING")
            if time_row is None:
                continue
            event_id = "EVT-LEGACY-" + sha256_text(url)[:12].upper()
            time_row["event_time_id"] = compact_id("TIME", event_id, 12)
            time_row["event_id"] = event_id
            event = empty_row("event")
            event.update(
                {
                    "event_id": event_id,
                    "event_group_id": "",
                    "event_source_native_id": "",
                    "event_primary_source_id": "",
                    "event_title": row.get("judul", ""),
                    "event_summary": str(row.get("isi_berita", ""))[:2000],
                    "event_status": "candidate",
                    "event_verification_status": "unverified",
                    "event_verification_level": "none",
                    "event_first_reported_at": document["document_published_at"],
                    "event_last_updated_at": "",
                    "event_notes": (
                        "Kandidat event dari baseline legacy; bukan fakta terverifikasi."
                    ),
                }
            )
            tables["event"].append(event)
            tables["event_time"].append(time_row)
            tables["event_location"].append(_location_row(row, event_id))
            tables["category"].append(_category_row(row, event_id))
            tables["document_event_link"].append(
                {
                    "link_id": compact_id(
                        "LINK", f"{document_id}|{event_id}", 12
                    ),
                    "document_id": document_id,
                    "event_id": event_id,
                    "relation_type": "reports",
                    "relation_direction": "document_to_event",
                    "relevance": "primary",
                    "is_primary": "ya",
                    "relation_confidence": "medium",
                    "relation_evidence": (
                        "Baseline legacy memiliki kategori target dan "
                        f"event_time_status={row.get('event_time_status', '')}."
                    ),
                    "event_count_mentioned": "1",
                    "link_status": "active",
                    "link_created_at": BASELINE_IMPORTED_AT,
                    "link_created_by": "system_baseline_import",
                }
            )
            tables["event_assertion"].extend(
                _assertions(row, event_id, document_id, time_row)
            )
            verification = empty_row("verification")
            verification.update(
                {
                    "verification_id": compact_id("VER", event_id, 12),
                    "target_type": "event",
                    "target_id": event_id,
                    "verification_status": "unverified",
                    "verification_level": "none",
                    "verification_basis": (
                        "Baseline legacy; tidak ada raw payload/run."
                    ),
                    "verification_source_count": "0",
                    "verification_method": "legacy_import",
                    "verification_notes": (
                        "Kandidat event legacy; belum diverifikasi."
                    ),
                }
            )
            tables["verification"].append(verification)
            events += 1

    tables["change_log"] = build_baseline_change_logs(tables)
    counts = {key: len(value) for key, value in tables.items()}
    run_row = empty_row("pipeline_run")
    run_row.update(
        {
            "run_id": BASELINE_RUN_ID,
            "started_at": BASELINE_IMPORTED_AT,
            "finished_at": BASELINE_IMPORTED_AT,
            "status": "imported",
            "baseline_path": str(path),
            "baseline_sha256": actual_hash,
            "sources_json": "[]",
            "counts_json": json.dumps(counts, ensure_ascii=False, sort_keys=True),
            "manifest_path": "",
            "notes": "Import baseline legacy; event berstatus kandidat.",
        }
    )
    tables["pipeline_run"].append(run_row)
    return tables


def build_baseline_change_logs(tables):
    rows = []
    for entity in (
        "document",
        "document_classification",
        "document_relevance",
        "document_duplicate",
        "event",
        "event_time",
        "event_location",
        "category",
        "document_event_link",
        "event_assertion",
        "verification",
    ):
        key = {
            "document": "document_id",
            "document_classification": "classification_id",
            "document_relevance": "document_id",
            "document_duplicate": "duplicate_id",
            "event": "event_id",
            "event_time": "event_time_id",
            "event_location": "event_location_id",
            "category": "category_assignment_id",
            "document_event_link": "link_id",
            "event_assertion": "assertion_id",
            "verification": "verification_id",
        }[entity]
        for target in tables.get(entity, []):
            target_id = target.get(key, "")
            if not target_id:
                continue
            rows.append(
                {
                    "change_id": compact_id("CHG", f"{entity}|{target_id}", 16),
                    "target_type": entity,
                    "target_id": target_id,
                    "change_type": "create",
                    "changed_at": BASELINE_IMPORTED_AT,
                    "changed_by": "system_baseline_import",
                    "change_reason": "Import baseline legacy yang dipertahankan.",
                    "schema_version": "1.0.0",
                    "manual_review": "ya",
                }
            )
    return rows
