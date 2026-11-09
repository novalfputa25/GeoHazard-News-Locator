"""Build normalized rows from parsed feed items."""

import re
from collections import defaultdict

import geographic_scope as geo

from relevance import classify_relevance

from .schema import empty_row
from .util import (
    SCOPE_IN,
    SCOPE_OUT,
    TARGET_CATEGORIES,
    category_scope,
    compact_id,
    document_identity,
    event_identity_for_bmkg,
    event_identity_for_gdacs,
    event_identity_for_usgs,
    iso_utc,
    json_dumps,
    sha256_text,
)


def _iso(value):
    return value.isoformat() if value else ""


def _time_precision(value):
    if value is None:
        return "unknown"
    if value.second:
        return "second"
    if value.minute:
        return "minute"
    return "hour"


def _event_identity(item):
    source_id = item["source_id"]
    if source_id.startswith("bmkg_"):
        return event_identity_for_bmkg(item)
    if source_id == "usgs_m45":
        return event_identity_for_usgs(item)
    return event_identity_for_gdacs(item)


def _source_kind(item):
    source_id = item["source_id"]
    if source_id.startswith("bmkg_"):
        return "bmkg"
    if source_id == "usgs_m45":
        return "usgs"
    if source_id == "gdacs_all":
        return "gdacs"
    return "news"


def _location_scope(item):
    if item.get("extra", {}).get("country"):
        country = str(item["extra"]["country"])
        if country and "indonesia" not in country.lower():
            return "tidak"
    if item.get("lat") in ("", None) or item.get("lon") in ("", None):
        return "tidak_diketahui"
    scope = geo.classify_location(
        location_name=item.get("location_name", ""),
        latitude=item.get("lat"),
        longitude=item.get("lon"),
        coordinate_status="source_coordinate",
        source_id=item.get("source_id", ""),
    )
    return scope["is_inside_indonesia"]


def build_document(item, source_row, raw_row, run_id):
    document_id, canonical_url = document_identity(
        item["source_id"],
        item["external_id"],
        item.get("canonical_url") or item.get("document_url", ""),
    )
    item["document_id"] = document_id
    item["canonical_url"] = canonical_url
    document = empty_row("document")
    source_kind = _source_kind(item)
    category = item.get("category_original", "Lainnya")
    document.update(
        {
            "document_id": document_id,
            "document_type": (
                "official_event_record" if source_kind != "news" else "news_article"
            ),
            "document_source_id": source_row["source_id"],
            "document_source_label": source_row["source_name"],
            "document_source_identity_status": "registered",
            "document_source_type": source_row["source_type"],
            "document_source_role": source_row["source_role"],
            "document_url": item.get("document_url", ""),
            "document_url_canonical": canonical_url,
            "document_title": item.get("title", ""),
            "document_publisher": source_row["source_institution"],
            "document_author": "",
            "document_language": source_row["source_language"],
            "document_external_id": item.get("external_id", ""),
            "document_legacy_row_ref": "",
            "document_content_hash": sha256_text(json_dumps(item)),
            "document_raw_payload_id": raw_row["raw_payload_id"],
            "document_published_at": _iso(item.get("published_at")),
            "document_retrieved_at": raw_row["raw_payload_retrieved_at"],
            "document_updated_at": _iso(item.get("updated_at")),
            "document_run_id": run_id,
            "document_status": "active",
            "document_provenance_status": (
                "complete" if raw_row["raw_payload_status"] == "stored" else "partial"
            ),
            "document_notes": (
                f"Kategori awal={category}; waktu publikasi terpisah dari waktu "
                f"kejadian. {'Feed resmi.' if source_kind != 'news' else 'Artikel berita pendukung.'}"
            ),
        }
    )
    classification = empty_row("document_classification")
    scope = category_scope(
        category,
        item.get("title", ""),
        item.get("extra", {}).get("summary", ""),
    )
    classification.update(
        {
            "classification_id": compact_id(
                "CLS", f"{document_id}|{category}", 16
            ),
            "document_id": document_id,
            "category_name": category,
            "category_scope": scope,
            "category_basis": item.get("category_basis")
            or ("official_metadata" if source_kind != "news" else "source_title"),
            "category_confidence": "high" if source_kind != "news" else "medium",
            "category_evidence": (
                f"Klasifikasi dokumen dari {source_row['source_id']}: {category}"
            ),
            "classified_at": raw_row["raw_payload_retrieved_at"],
            "review_status": "not_reviewed",
        }
    )
    item["category_scope"] = scope
    return document, classification


def build_document_relevance(item, source_row, classification, classified_at):
    decision = classify_relevance(
        item.get("title", ""),
        item.get("extra", {}).get("summary", ""),
        classification.get("category_name", ""),
        source_row.get("source_name", ""),
        source_row.get("source_type", ""),
    )
    row = empty_row("document_relevance")
    row.update(
        {
            "document_id": item["document_id"],
            "relevance_status": decision["relevance_status"],
            "relevance_category": decision["relevance_category"],
            "relevance_basis": decision["relevance_basis"],
            "relevance_confidence": decision["relevance_confidence"],
            "relevance_evidence": decision["relevance_evidence"],
            "classifier_version": decision["classifier_version"],
            "classified_at": classified_at,
            "review_status": "not_reviewed",
            "reviewed_at": "",
            "reviewed_by": "",
            "relevance_notes": (
                "Klasifikasi relevansi otomatis; belum direview manual."
            ),
        }
    )
    return row


def build_event(group_items):
    items = sorted(
        group_items,
        key=lambda item: (item.get("priority", 9), item.get("retrieved_at", "")),
    )
    primary = items[0]
    event_id, native_id = _event_identity(primary)
    source_kind = _source_kind(primary)
    event = empty_row("event")
    event.update(
        {
            "event_id": event_id,
            "event_group_id": "",
            "event_source_native_id": native_id,
            "event_primary_source_id": primary["source_id"],
            "event_title": primary.get("title", ""),
            "event_summary": primary.get("extra", {}).get("summary", "")
            or primary.get("title", ""),
            "event_status": "confirmed" if source_kind == "bmkg" else "reported",
            "event_verification_status": (
                "official" if source_kind == "bmkg" else "source_asserted"
            ),
            "event_verification_level": "official" if source_kind == "bmkg" else "low",
            "event_first_reported_at": _iso(primary.get("published_at"))
            or primary.get("retrieved_at", ""),
            "event_last_updated_at": _iso(primary.get("updated_at")),
            "event_notes": (
                "Rekaman resmi BMKG; beberapa feed BMKG dapat menjadi dokumen pendukung."
                if source_kind == "bmkg"
                else (
                    "Rekaman resmi USGS; sumber internasional pendukung, bukan sumber resmi Indonesia."
                    if source_kind == "usgs"
                    else "Rekaman GDACS; sumber internasional pendukung, bukan sumber resmi Indonesia."
                )
            ),
        }
    )

    time_row = empty_row("event_time")
    event_time = primary.get("event_time")
    time_row.update(
        {
            "event_time_id": compact_id("TIME", event_id, 12),
            "event_id": event_id,
            "event_time": _iso(event_time),
            "event_time_precision": _time_precision(event_time),
            "event_time_kind": "actual",
            "event_time_status": "extracted",
            "event_time_basis": "official_field",
            "event_time_evidence": primary.get("event_time_evidence", ""),
            "event_time_timezone": "Etc/UTC",
            "event_time_confidence": "high",
        }
    )

    location_row = empty_row("event_location")
    lat = primary.get("lat", "")
    lon = primary.get("lon", "")
    location_name = primary.get("location_name", "")
    coordinate_status = "source_coordinate" if lat and lon else "not_available"
    location_row.update(
        {
            "event_location_id": compact_id("LOCE", event_id, 12),
            "event_id": event_id,
            "location_name": location_name,
            "location_role": "epicenter" if source_kind in {"bmkg", "usgs"} else "event_area",
            "latitude": f"{float(lat):.4f}" if lat not in ("", None) else "",
            "longitude": f"{float(lon):.4f}" if lon not in ("", None) else "",
            "coordinate_source": "source_api" if lat and lon else "",
            "coordinate_status": coordinate_status,
            "coordinate_precision": "point" if lat and lon else "",
            "coordinate_confidence": "high" if lat and lon else "unknown",
            "is_inside_indonesia": _location_scope(primary),
            "location_evidence": (
                f"{primary['source_id']} field lokasi/koordinat; "
                f"{primary.get('event_time_evidence', '')}"
            ),
            "location_notes": "Koordinat berasal dari field sumber; belum diverifikasi manual.",
        }
    )

    category_name = primary.get("category_original", "Lainnya")
    scope = SCOPE_IN if category_name in TARGET_CATEGORIES else SCOPE_OUT
    category_row = empty_row("category")
    category_row.update(
        {
            "category_assignment_id": compact_id("CAT", event_id, 12),
            "event_id": event_id,
            "category_name": category_name,
            "category_rank": "primary",
            "category_scope": scope,
            "category_basis": "official_metadata",
            "category_confidence": "high" if scope == SCOPE_IN else "medium",
            "category_review_status": "not_reviewed",
            "category_original": category_name,
            "category_notes": (
                "Kategori dari metadata sumber terstruktur; tsunami tetap atribut "
                "potensi, bukan event terpisah."
            ),
        }
    )

    return {
        "event": event,
        "event_time": time_row,
        "event_location": location_row,
        "category": category_row,
        "primary": primary,
        "items": items,
    }


def build_link(item, event_id, is_primary, retrieved_at):
    link = empty_row("document_event_link")
    link.update(
        {
            "link_id": compact_id(
                "LINK", f"{item['document_id']}|{event_id}", 12
            ),
            "document_id": item["document_id"],
            "event_id": event_id,
            "relation_type": "reports",
            "relation_direction": "document_to_event",
            "relevance": "primary" if is_primary else "supporting",
            "is_primary": "ya" if is_primary else "tidak",
            "relation_confidence": "high",
            "relation_evidence": (
                f"Record {item['source_id']} memuat event_key "
                f"{item.get('event_key', '')} dan parameter kejadian."
            ),
            "event_count_mentioned": "1",
            "link_status": "active",
            "link_created_at": retrieved_at,
            "link_created_by": "system_pipeline",
        }
    )
    return link


def build_assertions(item, event_id):
    values = [
        ("event_time", _iso(item.get("event_time")), item.get("event_time_evidence", "")),
        ("latitude", f"{float(item['lat']):.4f}" if item.get("lat") not in ("", None) else "", "Field koordinat sumber"),
        ("longitude", f"{float(item['lon']):.4f}" if item.get("lon") not in ("", None) else "", "Field koordinat sumber"),
        ("location_name", item.get("location_name", ""), "Field lokasi sumber"),
        ("category", item.get("category_original", ""), "Metadata kategori sumber"),
        ("magnitude", item.get("magnitude_text", ""), "Field magnitudo sumber"),
        ("depth", item.get("depth_text", ""), "Field kedalaman sumber"),
    ]
    rows = []
    for field_name, value, evidence in values:
        if value in ("", None):
            continue
        row = empty_row("event_assertion")
        row.update(
            {
                "assertion_id": compact_id(
                    "AST",
                    f"{event_id}|{field_name}|{item['source_id']}|{item['document_id']}",
                    16,
                ),
                "event_id": event_id,
                "document_id": item["document_id"],
                "source_id": item["source_id"],
                "field_name": field_name,
                "asserted_value": str(value),
                "assertion_status": "accepted",
                "assertion_confidence": "high",
                "assertion_evidence": evidence,
                "asserted_at": item.get("retrieved_at", ""),
                "assertion_notes": "Nilai dari dokumen sumber; belum direview manual.",
            }
        )
        rows.append(row)
    return rows


def build_attributes(item, event_id):
    specs = [
        ("magnitude", item.get("magnitude_text", ""), "M", "Field magnitudo sumber.", "high"),
    ]
    depth_match = re.search(
        r"(-?\d+(?:[.,]\d+)?)\s*(km|mi)\b", item.get("depth_text", ""), re.I
    )
    if depth_match:
        specs.append(
            (
                "depth",
                depth_match.group(1).replace(",", "."),
                depth_match.group(2).lower(),
                f"Field kedalaman sumber: {item['depth_text']}",
                "high",
            )
        )
    elif item.get("depth_text"):
        specs.append(("depth", item["depth_text"], "", "Field kedalaman sumber.", "high"))
    extra = item.get("extra", {})
    if extra.get("potensi"):
        specs.append(
            (
                "bmkg_potential_text",
                extra["potensi"],
                "",
                "Nilai mentah field Potensi BMKG; bukan event tsunami terpisah.",
                "high",
            )
        )
        specs.append(
            (
                "tsunami_potential_status",
                pilot_classify_tsunami(extra["potensi"]),
                "",
                "Status ternormalisasi dari field Potensi BMKG.",
                "medium",
            )
        )
    if extra.get("dirasakan"):
        specs.append(
            (
                "felt_reports",
                extra["dirasakan"],
                "",
                "Field Dirasakan BMKG.",
                "high",
            )
        )
    if extra.get("shakemap"):
        specs.append(
            ("shakemap_file", extra["shakemap"], "", "Field Shakemap BMKG.", "high")
        )
    if extra.get("alert_level"):
        specs.append(
            ("gdacs_alert_level", extra["alert_level"], "", "Field alertlevel GDACS.", "high")
        )
    if extra.get("country"):
        specs.append(
            ("source_country", extra["country"], "", "Field country GDACS.", "high")
        )
    rows = []
    for name, value, unit, notes, confidence in specs:
        if value in ("", None):
            continue
        row = empty_row("event_attribute")
        row.update(
            {
                "event_attribute_id": compact_id("EATTR", f"{event_id}|{name}", 16),
                "event_id": event_id,
                "attribute_name": name,
                "attribute_value": str(value),
                "attribute_unit": unit,
                "attribute_source_id": item["source_id"],
                "attribute_confidence": confidence,
                "attribute_notes": notes,
            }
        )
        rows.append(row)
    return rows


def pilot_classify_tsunami(value):
    from scripts import pilot_collect_official_geohazard as pilot

    return pilot.classify_tsunami_potential(value)


def build_verification(event, primary):
    row = empty_row("verification")
    source_kind = _source_kind(primary)
    row.update(
        {
            "verification_id": compact_id("VER", event["event_id"], 12),
            "target_type": "event",
            "target_id": event["event_id"],
            "verification_status": (
                "official" if source_kind == "bmkg" else "source_asserted"
            ),
            "verification_level": "official" if source_kind == "bmkg" else "low",
            "verification_basis": (
                "Rekaman resmi feed BMKG."
                if source_kind == "bmkg"
                else "Rekaman resmi sumber internasional pendukung."
            ),
            "verification_source_count": "1",
            "verification_method": "official_record",
            "verification_notes": "Verifikasi otomatis; belum ada review manual.",
        }
    )
    return row


def build_location_mention(item, event_id):
    if not item.get("location_name"):
        return None
    row = empty_row("location_mention")
    row.update(
        {
            "location_mention_id": compact_id(
                "LOCM", f"{item['document_id']}|{event_id}", 12
            ),
            "document_id": item["document_id"],
            "linked_event_id": event_id,
            "mention_text": item["location_name"],
            "mention_normalized": item["location_name"],
            "mention_role": "event_location",
            "mention_status": "normalized",
            "mention_confidence": "medium",
            "mention_evidence": f"Field lokasi record {item['source_id']}",
            "mention_notes": "Normalisasi teks; belum verifikasi lapangan.",
        }
    )
    return row


def build_document_duplicates(documents, detected_at):
    rows = []
    seen_url = {}
    seen_external = {}
    for document in documents:
        reasons = []
        references = []
        url = document["document_url_canonical"]
        external = document["document_external_id"]
        if url and url in seen_url:
            reasons.append("url_sama")
            references.append(seen_url[url])
        if external and external in seen_external:
            reasons.append("external_id_sama")
            references.append(seen_external[external])
        if reasons:
            duplicate_id = compact_id("DUPDOC", document["document_id"], 16)
            rows.append(
                {
                    "duplicate_id": duplicate_id,
                    "document_id": document["document_id"],
                    "duplicate_of_document_id": references[0],
                    "duplicate_reason": "+".join(reasons),
                    "duplicate_confidence": "high",
                    "detected_at": detected_at,
                }
            )
        if url and url not in seen_url:
            seen_url[url] = document["document_id"]
        if external and external not in seen_external:
            seen_external[external] = document["document_id"]
    return rows


def build_change_logs(tables, changed_at):
    from .schema import ENTITY_ORDER, PRIMARY_KEYS

    rows = []
    for entity in ENTITY_ORDER:
        if entity in {"change_log", "pipeline_run", "import_log"}:
            continue
        key = PRIMARY_KEYS[entity]
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
                    "changed_at": changed_at,
                    "changed_by": "system_pipeline",
                    "change_reason": "Pembuatan record dari pipeline sumber aktif.",
                    "schema_version": "1.0.0",
                    "manual_review": "tidak",
                }
            )
    return rows


def group_items_by_event(items):
    grouped = defaultdict(list)
    for item in items:
        if item.get("event_key") and item.get("event_time") is not None:
            grouped[item["event_key"]].append(item)
    return grouped
