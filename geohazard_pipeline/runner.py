"""Unified pipeline runner."""

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import dataset_baseline

from .build import (
    build_assertions,
    build_attributes,
    build_change_logs,
    build_document,
    build_document_duplicates,
    build_document_relevance,
    build_event,
    build_link,
    build_location_mention,
    build_verification,
    group_items_by_event,
)
from .fetch import fetch_url, read_offline_payload, raw_payload_row
from .parsers import parse_source
from .schema import ENTITY_ORDER, TABLE_COLUMNS, empty_row, write_csv
from .util import (
    ROOT,
    iso_utc,
    load_active_feed_configs,
    load_register,
    registry_to_source_row,
    utc_now,
)

PRIORITY = {
    "bmkg_autogempa": 0,
    "bmkg_gempa_terkini": 1,
    "bmkg_gempa_dirasakan": 2,
    "usgs_m45": 3,
    "gdacs_all": 4,
}

PARSER = {
    "bmkg_xml": "bmkg",
    "rss": "rss",
    "atom": "rss",
    "api": "api",
}


def _run_id():
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    return f"RUN-{stamp}"


def _new_run_dir(output_root, run_id):
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / run_id
    if run_dir.exists():
        index = 2
        while (root / f"{run_id}_{index}").exists():
            index += 1
        run_dir = root / f"{run_id}_{index}"
    run_dir.mkdir(parents=True)
    return run_dir


def _configure_feed(feed):
    config = dict(feed)
    config["source_id"] = feed["id"]
    config["priority"] = PRIORITY.get(config["source_id"], 9)
    if config["source_id"] == "usgs_m45":
        config["parser"] = "usgs"
    elif config["source_id"] == "gdacs_all":
        config["parser"] = "gdacs"
    else:
        config["parser"] = PARSER.get(feed.get("tipe", ""), "rss")
    return config


def _page_url(url, page, pagination):
    mode = pagination.get("type", "query")
    if mode == "query":
        param = pagination.get("param", "page")
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query[param] = str(page)
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query),
                parts.fragment,
            )
        )
    if mode == "template":
        template = pagination.get("template")
        if not template:
            raise ValueError("Pagination template kosong.")
        return template.format(page=page, url=url)
    if mode == "path":
        return f"{url.rstrip('/')}/page/{page}/"
    raise ValueError(f"Tipe pagination tidak dikenal: {mode}")


def _page_targets(config):
    url = config["url"]
    pagination = config.get("pagination") or {}
    max_pages = pagination.get("max_pages")
    if not max_pages or int(max_pages) <= 1:
        return [(1, url)]
    start_page = max(2, int(pagination.get("start_page", 2)))
    targets = [(1, url)]
    for page in range(start_page, int(max_pages) + 1):
        targets.append((page, _page_url(url, page, pagination)))
    return targets


def _item_key(item):
    key = (
        item.get("external_id")
        or item.get("canonical_url")
        or item.get("document_url")
        or item.get("title")
    )
    if key:
        return str(key)
    return json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)


def _dedupe_items(items):
    seen = set()
    unique = []
    duplicates = 0
    for item in items:
        key = _item_key(item)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(item)
    return unique, duplicates


def _effective_max_items(config, max_items_by_source):
    source_id = config["source_id"]
    if max_items_by_source and source_id in max_items_by_source:
        return max_items_by_source[source_id]
    return config.get("max_items")


def _select_items(items, max_items):
    if max_items is None:
        return items
    limit = int(max_items)
    if limit < 0:
        raise ValueError("max_items tidak boleh negatif.")
    return items[:limit]


def _fetch_page(raw_dir, config, source_id, page_number, page_url, timeout, started_at):
    if raw_dir:
        fetch = read_offline_payload(raw_dir, source_id, page_number)
        if fetch is None:
            fetch = {
                "content": b"",
                "http_status": 0,
                "content_type": "",
                "retrieved_at": started_at,
                "error": "Payload offline tidak ditemukan.",
            }
    else:
        fetch = fetch_url(page_url, timeout=timeout)
    fetch["feed_type"] = config.get("tipe", "")
    return fetch


def run_pipeline(
    output_root=None,
    raw_dir=None,
    sources=None,
    max_items=None,
    run_id=None,
    fetch_timeout=30,
    fetch_delay=1.0,
    max_items_by_source=None,
):
    output_root = Path(output_root or (ROOT / "data" / "pipeline"))
    run_id = run_id or _run_id()
    run_dir = _new_run_dir(output_root, run_id)
    started_at = iso_utc()
    tables = {entity: [] for entity in ENTITY_ORDER}
    issues = []
    feed_results = {}
    register = load_register()

    configs = [_configure_feed(feed) for feed in load_active_feed_configs(max_items)]
    if sources:
        wanted = {source.strip() for source in sources if source.strip()}
        configs = [config for config in configs if config["source_id"] in wanted]

    event_items = []
    live_requests = 0
    for config in configs:
        source_id = config["source_id"]
        register_row = register.get(source_id)
        if not register_row:
            issues.append(
                {
                    "issue_id": f"REG-{source_id}",
                    "severity": "P1",
                    "source_id": source_id,
                    "description": "Sumber aktif tidak ada di MASTER_SOURCE_REGISTER.",
                }
            )
            continue
        status = str(register_row.get("status_sumber", "")).upper()
        if status not in {"TERVERIFIKASI_AKTIF"}:
            issues.append(
                {
                    "issue_id": f"STATUS-{source_id}",
                    "severity": "P1",
                    "source_id": source_id,
                    "description": f"Status sumber {status} tidak diizinkan untuk pipeline produksi.",
                }
            )
            continue

        targets = _page_targets(config)
        max_per_source = _effective_max_items(config, max_items_by_source)
        if max_per_source is not None:
            max_per_source = int(max_per_source)
            if max_per_source < 0:
                raise ValueError("max_items tidak boleh negatif.")

        source_row = None
        raw_rows_by_id = {}
        all_items = []
        seen_keys = set()
        unique_count = 0
        pages_fetched = 0
        pages_succeeded = 0
        first_http_status = ""
        network_errors = []
        parse_errors = []
        stop_reason = ""

        for page_number, page_url in targets:
            if not raw_dir and fetch_delay and live_requests:
                time.sleep(fetch_delay)
            fetch = _fetch_page(
                raw_dir,
                config,
                source_id,
                page_number,
                page_url,
                fetch_timeout,
                started_at,
            )
            if not raw_dir:
                live_requests += 1
            pages_fetched += 1
            if source_row is None:
                first_http_status = fetch["http_status"]
                source_row = registry_to_source_row(
                    register_row,
                    config,
                    fetch["http_status"],
                    fetch["retrieved_at"],
                )
                tables["source"].append(source_row)
            raw_row = raw_payload_row(
                source_id,
                page_url,
                fetch,
                run_dir,
                run_id,
                page_number=page_number,
            )
            if raw_row["raw_payload_id"] not in raw_rows_by_id:
                raw_rows_by_id[raw_row["raw_payload_id"]] = raw_row
                tables["raw_payload"].append(raw_row)

            if (
                fetch.get("error")
                or fetch["http_status"] != 200
                or not fetch["content"]
            ):
                network_error = fetch.get("error") or "payload kosong"
                network_errors.append(network_error)
                issue_id = (
                    f"NET-{source_id}"
                    if page_number == 1
                    else f"NET-{source_id}-P{page_number}"
                )
                issues.append(
                    {
                        "issue_id": issue_id,
                        "severity": "P1",
                        "source_id": source_id,
                        "description": (
                            f"Fetch gagal halaman {page_number}: "
                            f"HTTP {fetch['http_status']}; {network_error}"
                        ),
                    }
                )
                stop_reason = "fetch_error"
                break

            pages_succeeded += 1
            items, error = parse_source(source_id, fetch["content"], config)
            if isinstance(items, tuple):
                items, error = items
            new_unique = 0
            for item in items:
                item["source_id"] = source_id
                item["retrieved_at"] = fetch["retrieved_at"]
                item["raw_payload_id"] = raw_row["raw_payload_id"]
                key = _item_key(item)
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_count += 1
                    new_unique += 1
            all_items.extend(items)

            if error:
                parse_errors.append(error)
                issue_id = (
                    f"PARSE-{source_id}"
                    if page_number == 1
                    else f"PARSE-{source_id}-P{page_number}"
                )
                issues.append(
                    {
                        "issue_id": issue_id,
                        "severity": "P1",
                        "source_id": source_id,
                        "description": error,
                    }
                )
            if page_number > 1 and new_unique == 0:
                stop_reason = "no_new_items"
                break
            if max_per_source is not None and unique_count >= max_per_source:
                stop_reason = "max_items"
                break

        if source_row is None:
            source_row = registry_to_source_row(
                register_row, config, 0, started_at
            )
            tables["source"].append(source_row)

        unique_items, duplicates = _dedupe_items(all_items)
        selected_items = _select_items(unique_items, max_per_source)
        imported_count = 0
        for item in selected_items:
            raw_row = raw_rows_by_id[item["raw_payload_id"]]
            item["register_row"] = register_row
            item["source_id"] = source_id
            document, classification = build_document(
                item, source_row, raw_row, run_id
            )
            tables["document"].append(document)
            tables["document_classification"].append(classification)
            tables["document_relevance"].append(
                build_document_relevance(
                    item,
                    source_row,
                    classification,
                    raw_row["raw_payload_retrieved_at"],
                )
            )
            imported_count += 1
            if item.get("event_key") and item.get("event_time") is not None:
                event_items.append(item)

        feed_results[source_id] = {
            "items_parsed": len(all_items),
            "items_selected": len(selected_items),
            "items_imported": imported_count,
            "items_duplicates": duplicates,
            "pages_fetched": pages_fetched,
            "pages_succeeded": pages_succeeded,
            "max_items": max_per_source,
            "stop_reason": stop_reason,
            "http_status": first_http_status,
            "error": "; ".join(network_errors + parse_errors),
        }

    for group_items in group_items_by_event(event_items).values():
        group = build_event(group_items)
        event = group["event"]
        event_id = event["event_id"]
        primary = group["primary"]
        tables["event"].append(event)
        tables["event_time"].append(group["event_time"])
        tables["event_location"].append(group["event_location"])
        tables["category"].append(group["category"])
        for item in group["items"]:
            tables["document_event_link"].append(
                build_link(
                    item,
                    event_id,
                    item is primary,
                    item.get("retrieved_at", started_at),
                )
            )
            tables["event_assertion"].extend(build_assertions(item, event_id))
            mention = build_location_mention(item, event_id)
            if mention:
                tables["location_mention"].append(mention)
        tables["event_attribute"].extend(build_attributes(primary, event_id))
        tables["verification"].append(build_verification(event, primary))

    tables["document_duplicate"] = build_document_duplicates(
        tables["document"], started_at
    )
    tables["change_log"] = build_change_logs(tables, iso_utc())

    counts = {entity: len(tables.get(entity, [])) for entity in ENTITY_ORDER}
    counts["pipeline_run"] = 1
    baseline = None
    try:
        baseline = dataset_baseline.verify_dataset()
    except Exception as exc:  # pragma: no cover - operational guard
        issues.append(
            {
                "issue_id": "BASELINE",
                "severity": "P1",
                "source_id": "baseline",
                "description": f"Baseline tidak dapat diverifikasi: {exc}",
            }
        )

    run_row = empty_row("pipeline_run")
    run_row.update(
        {
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": iso_utc(),
            "status": "success" if any(tables["document"]) else "empty",
            "baseline_path": (
                baseline["path"] if baseline else ""
            ),
            "baseline_sha256": baseline["sha256"] if baseline else "",
            "sources_json": json.dumps(
                [row["source_id"] for row in tables["source"]], ensure_ascii=False
            ),
            "counts_json": json.dumps(counts, ensure_ascii=False, sort_keys=True),
            "manifest_path": str(run_dir / "manifest.json"),
            "notes": "Pipeline run read-only; raw payload immutable; lisensi belum diverifikasi.",
        }
    )
    tables["pipeline_run"].append(run_row)

    for entity in ENTITY_ORDER:
        write_csv(
            run_dir / "tables" / f"{entity}.csv",
            tables[entity],
            TABLE_COLUMNS[entity],
        )

    manifest = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "started_at": started_at,
        "finished_at": iso_utc(),
        "counts": counts,
        "sources": feed_results,
        "selection": {
            "max_items_global": max_items,
            "max_items_by_source": max_items_by_source or {},
            "fetch_delay_seconds": fetch_delay,
            "deduplicate_by": (
                "external_id/canonical_url/document_url/title per source"
            ),
            "pagination": "opt-in per feed; default satu halaman",
        },
        "issues": issues,
        "baseline": baseline,
        "limitations": [
            "Lisensi/redistribusi sumber belum diverifikasi.",
            "robots BMKG tidak terbaca; pipeline memakai laju rendah dan tidak mengklaim izin.",
            "Feed BMKG/USGS/GDACS adalah jendela terbatas, bukan arsip.",
            "Pagination hanya dipakai bila feed menyediakan mekanisme yang terkonfigurasi.",
            "Kategori berita adalah klasifikasi dokumen, bukan bukti kejadian.",
            "Event dari baseline diimpor sebagai kandidat, bukan fakta terverifikasi.",
        ],
    }
    with open(run_dir / "manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
    return manifest
