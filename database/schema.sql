PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS pipeline_run (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    baseline_path TEXT,
    baseline_sha256 TEXT,
    sources_json TEXT,
    counts_json TEXT,
    manifest_path TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS source (
    source_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_institution TEXT NOT NULL,
    source_country TEXT,
    source_language TEXT,
    source_type TEXT NOT NULL,
    source_role TEXT NOT NULL,
    source_data_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_feed_url TEXT,
    source_registry_status TEXT NOT NULL,
    source_license_status TEXT NOT NULL,
    source_license TEXT,
    source_terms_url TEXT,
    source_last_tested_at TEXT,
    source_http_status INTEGER,
    source_robots_status TEXT,
    source_notes TEXT
);

CREATE TABLE IF NOT EXISTS raw_payload (
    raw_payload_id TEXT PRIMARY KEY,
    raw_payload_source_id TEXT NOT NULL REFERENCES source(source_id),
    raw_payload_url TEXT NOT NULL,
    raw_payload_retrieved_at TEXT NOT NULL,
    raw_payload_http_status INTEGER,
    raw_payload_content_type TEXT,
    raw_payload_sha256 TEXT NOT NULL,
    raw_payload_size_bytes INTEGER,
    raw_payload_path TEXT,
    raw_payload_status TEXT NOT NULL,
    raw_payload_notes TEXT
);

CREATE TABLE IF NOT EXISTS document (
    document_id TEXT PRIMARY KEY,
    document_type TEXT NOT NULL,
    document_source_id TEXT REFERENCES source(source_id),
    document_source_label TEXT,
    document_source_identity_status TEXT NOT NULL,
    document_source_type TEXT,
    document_source_role TEXT,
    document_url TEXT,
    document_url_canonical TEXT,
    document_title TEXT NOT NULL,
    document_publisher TEXT,
    document_author TEXT,
    document_language TEXT,
    document_external_id TEXT,
    document_legacy_row_ref TEXT,
    document_content_hash TEXT,
    document_raw_payload_id TEXT REFERENCES raw_payload(raw_payload_id),
    document_published_at TEXT,
    document_retrieved_at TEXT,
    document_updated_at TEXT,
    document_run_id TEXT,
    document_status TEXT NOT NULL,
    document_provenance_status TEXT NOT NULL,
    document_notes TEXT
);

CREATE TABLE IF NOT EXISTS document_classification (
    classification_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES document(document_id),
    category_name TEXT NOT NULL,
    category_scope TEXT NOT NULL,
    category_basis TEXT,
    category_confidence TEXT,
    category_evidence TEXT,
    classified_at TEXT,
    review_status TEXT
);

CREATE TABLE IF NOT EXISTS document_relevance (
    document_id TEXT PRIMARY KEY REFERENCES document(document_id),
    relevance_status TEXT NOT NULL,
    relevance_category TEXT NOT NULL,
    relevance_basis TEXT NOT NULL,
    relevance_confidence TEXT,
    relevance_evidence TEXT,
    classifier_version TEXT NOT NULL,
    classified_at TEXT NOT NULL,
    review_status TEXT,
    reviewed_at TEXT,
    reviewed_by TEXT,
    relevance_notes TEXT
);

CREATE TABLE IF NOT EXISTS document_duplicate (
    duplicate_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES document(document_id),
    duplicate_of_document_id TEXT REFERENCES document(document_id),
    duplicate_reason TEXT,
    duplicate_confidence TEXT,
    detected_at TEXT
);

CREATE TABLE IF NOT EXISTS event (
    event_id TEXT PRIMARY KEY,
    event_group_id TEXT,
    event_source_native_id TEXT,
    event_primary_source_id TEXT REFERENCES source(source_id),
    event_title TEXT NOT NULL,
    event_summary TEXT,
    event_status TEXT NOT NULL,
    event_verification_status TEXT NOT NULL,
    event_verification_level TEXT NOT NULL,
    event_first_reported_at TEXT,
    event_last_updated_at TEXT,
    event_notes TEXT
);

CREATE TABLE IF NOT EXISTS event_time (
    event_time_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES event(event_id),
    event_time TEXT,
    event_time_start TEXT,
    event_time_end TEXT,
    event_time_precision TEXT,
    event_time_kind TEXT,
    event_time_status TEXT NOT NULL,
    event_time_basis TEXT NOT NULL,
    event_time_evidence TEXT,
    event_time_candidate_text TEXT,
    event_time_review_reason TEXT,
    event_time_timezone TEXT,
    event_time_confidence TEXT
);

CREATE TABLE IF NOT EXISTS location_mention (
    location_mention_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES document(document_id),
    linked_event_id TEXT REFERENCES event(event_id),
    mention_text TEXT NOT NULL,
    mention_normalized TEXT,
    mention_role TEXT,
    mention_status TEXT,
    mention_confidence TEXT,
    mention_evidence TEXT,
    mention_notes TEXT
);

CREATE TABLE IF NOT EXISTS event_location (
    event_location_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES event(event_id),
    location_name TEXT,
    location_role TEXT,
    admin_province TEXT,
    admin_kabupaten_kota TEXT,
    admin_kecamatan TEXT,
    admin_desa_kelurahan TEXT,
    latitude REAL,
    longitude REAL,
    coordinate_source TEXT,
    coordinate_status TEXT,
    coordinate_precision TEXT,
    coordinate_confidence TEXT,
    coordinate_verified_at TEXT,
    coordinate_verified_by TEXT,
    is_inside_indonesia TEXT NOT NULL,
    location_evidence TEXT,
    location_notes TEXT
);

CREATE TABLE IF NOT EXISTS category (
    category_assignment_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES event(event_id),
    category_name TEXT NOT NULL,
    category_rank TEXT NOT NULL,
    category_scope TEXT NOT NULL,
    category_basis TEXT NOT NULL,
    category_confidence TEXT,
    category_review_status TEXT,
    category_reviewed_by TEXT,
    category_reviewed_at TEXT,
    category_original TEXT,
    category_notes TEXT
);

CREATE TABLE IF NOT EXISTS document_event_link (
    link_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES document(document_id),
    event_id TEXT NOT NULL REFERENCES event(event_id),
    relation_type TEXT NOT NULL,
    relation_direction TEXT NOT NULL,
    relevance TEXT NOT NULL,
    is_primary TEXT NOT NULL,
    relation_confidence TEXT,
    relation_evidence TEXT,
    event_count_mentioned INTEGER,
    link_status TEXT NOT NULL,
    link_created_at TEXT,
    link_created_by TEXT
);

CREATE TABLE IF NOT EXISTS event_assertion (
    assertion_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES event(event_id),
    document_id TEXT REFERENCES document(document_id),
    source_id TEXT REFERENCES source(source_id),
    field_name TEXT NOT NULL,
    asserted_value TEXT,
    assertion_status TEXT NOT NULL,
    assertion_confidence TEXT,
    assertion_evidence TEXT,
    asserted_at TEXT,
    assertion_notes TEXT
);

CREATE TABLE IF NOT EXISTS event_relation (
    event_relation_id TEXT PRIMARY KEY,
    from_event_id TEXT NOT NULL REFERENCES event(event_id),
    to_event_id TEXT NOT NULL REFERENCES event(event_id),
    event_relation_type TEXT NOT NULL,
    event_relation_confidence TEXT,
    event_relation_evidence TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS verification (
    verification_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    verification_level TEXT NOT NULL,
    verification_basis TEXT,
    verification_source_count INTEGER,
    verification_method TEXT,
    verified_at TEXT,
    verified_by TEXT,
    verification_notes TEXT
);

CREATE TABLE IF NOT EXISTS change_log (
    change_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    change_type TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    evidence_ref TEXT,
    schema_version TEXT,
    manual_review TEXT
);

CREATE TABLE IF NOT EXISTS event_attribute (
    event_attribute_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES event(event_id),
    attribute_name TEXT NOT NULL,
    attribute_value TEXT,
    attribute_unit TEXT,
    attribute_source_id TEXT REFERENCES source(source_id),
    attribute_confidence TEXT,
    attribute_notes TEXT
);

CREATE TABLE IF NOT EXISTS import_log (
    import_id TEXT PRIMARY KEY,
    run_id TEXT,
    imported_at TEXT NOT NULL,
    tables_json TEXT,
    status TEXT NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_document_published ON document(document_published_at);
CREATE INDEX IF NOT EXISTS idx_document_source ON document(document_source_id);
CREATE INDEX IF NOT EXISTS idx_document_status ON document(document_status);
CREATE INDEX IF NOT EXISTS idx_doc_class_category ON document_classification(category_name);
CREATE INDEX IF NOT EXISTS idx_doc_class_scope ON document_classification(category_scope);
CREATE INDEX IF NOT EXISTS idx_doc_relevance_status ON document_relevance(relevance_status);
CREATE INDEX IF NOT EXISTS idx_doc_relevance_category ON document_relevance(relevance_category);
CREATE INDEX IF NOT EXISTS idx_event_time_value ON event_time(event_time);
CREATE INDEX IF NOT EXISTS idx_event_time_status ON event_time(event_time_status);
CREATE INDEX IF NOT EXISTS idx_event_location_coords ON event_location(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_event_location_inside ON event_location(is_inside_indonesia);
CREATE INDEX IF NOT EXISTS idx_category_name ON category(category_name);
CREATE INDEX IF NOT EXISTS idx_category_scope ON category(category_scope);
CREATE INDEX IF NOT EXISTS idx_link_event ON document_event_link(event_id);
CREATE INDEX IF NOT EXISTS idx_link_document ON document_event_link(document_id);
CREATE INDEX IF NOT EXISTS idx_raw_source ON raw_payload(raw_payload_source_id);
