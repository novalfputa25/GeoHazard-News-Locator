"""Read-only dashboard queries against the active GeoHazard SQLite database."""

import math
import re
import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from geohazard_pipeline.util import TARGET_CATEGORIES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "database" / "geohazard.db"

OTHER_CATEGORY = "Lainnya"
DISPLAY_CATEGORIES = tuple(TARGET_CATEGORIES) + (OTHER_CATEGORY,)
UNKNOWN_PROVINCE = "__unknown__"
UNKNOWN_PROVINCE_LABEL = "Tidak diketahui"
UNKNOWN_SOURCE_LABEL = "Tidak diketahui"

SOURCE_LABEL_SQL = """
COALESCE(
    NULLIF(d.document_source_label, ''),
    NULLIF(s.source_name, ''),
    NULLIF(d.document_publisher, ''),
    'Tidak diketahui'
)
"""

def _clean_region_name(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def _region_key(value):
    return _clean_region_name(value).casefold()

MONTH_NAMES = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
)


class DashboardDataError(RuntimeError):
    """Raised when dashboard data cannot be read safely."""


@dataclass(frozen=True)
class DashboardFilters:
    category: str = "all"
    date_from: str = ""
    date_to: str = ""
    province: str = "all"
    kabupaten: str = "all"
    granularity: str = "auto"

    def as_dict(self):
        return {
            "category": self.category,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "province": self.province,
            "kabupaten": self.kabupaten,
            "granularity": self.granularity,
        }


@dataclass(frozen=True)
class NewsSearchFilters:
    q: str = ""
    category: str = "all"
    date_from: str = ""
    date_to: str = ""
    source: str = "all"
    page: int = 1
    per_page: int = 10

    def as_dict(self):
        return {
            "q": self.q,
            "category": self.category,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "source": self.source,
            "page": self.page,
            "per_page": self.per_page,
        }


def _normalize_date(value, field_name):
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"{field_name} harus berformat YYYY-MM-DD") from exc


def parse_filters(params):
    category = str(params.get("category") or "all").strip() or "all"
    province = str(params.get("province") or "all").strip() or "all"
    kabupaten = str(
        params.get("kabupaten") or params.get("kabupaten_kota") or "all"
    ).strip() or "all"
    granularity = str(params.get("granularity") or "auto").strip() or "auto"
    date_from = _normalize_date(params.get("date_from"), "date_from")
    date_to = _normalize_date(params.get("date_to"), "date_to")

    if granularity not in {"auto", "day", "month"}:
        raise ValueError("granularity harus auto, day, atau month")
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from tidak boleh setelah date_to")

    return DashboardFilters(
        category=category,
        date_from=date_from,
        date_to=date_to,
        province=province,
        kabupaten=kabupaten,
        granularity=granularity,
    )


def _positive_int(value, field_name, default, maximum=None):
    text = str(value if value is not None else "").strip()
    if not text:
        return default
    try:
        number = int(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} harus bilangan bulat positif") from exc
    if number < 1:
        raise ValueError(f"{field_name} harus bilangan bulat positif")
    if maximum is not None:
        return min(number, maximum)
    return number


def parse_search_filters(params):
    q = str(params.get("q") or "").strip()
    category = str(params.get("category") or "all").strip() or "all"
    source = str(params.get("source") or "all").strip() or "all"
    date_from = _normalize_date(params.get("date_from"), "date_from")
    date_to = _normalize_date(params.get("date_to"), "date_to")
    page = _positive_int(params.get("page"), "page", 1)
    per_page = _positive_int(
        params.get("per_page"),
        "per_page",
        10,
        maximum=50,
    )

    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from tidak boleh setelah date_to")

    return NewsSearchFilters(
        q=q,
        category=category,
        date_from=date_from,
        date_to=date_to,
        source=source,
        page=page,
        per_page=per_page,
    )


def connect(db_path=None):
    path = Path(db_path or DEFAULT_DB_PATH)
    if not path.is_file():
        raise DashboardDataError(f"Database tidak ditemukan: {path}")

    uri = f"file:{quote(path.as_posix(), safe='/:')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _event_where(filters):
    clauses = ["1 = 1"]
    params = []

    if filters.category != "all":
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM category c "
            "WHERE c.event_id = e.event_id AND c.category_name = ?"
            ")"
        )
        params.append(filters.category)

    if filters.date_from:
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM event_time et "
            "WHERE et.event_id = e.event_id "
            "AND COALESCE(NULLIF(et.event_time, ''), "
            "NULLIF(et.event_time_start, '')) IS NOT NULL "
            "AND date(COALESCE(NULLIF(et.event_time, ''), "
            "NULLIF(et.event_time_start, ''))) >= date(?)"
            ")"
        )
        params.append(filters.date_from)

    if filters.date_to:
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM event_time et "
            "WHERE et.event_id = e.event_id "
            "AND COALESCE(NULLIF(et.event_time, ''), "
            "NULLIF(et.event_time_start, '')) IS NOT NULL "
            "AND date(COALESCE(NULLIF(et.event_time, ''), "
            "NULLIF(et.event_time_start, ''))) <= date(?)"
            ")"
        )
        params.append(filters.date_to)

    if filters.province == UNKNOWN_PROVINCE:
        clauses.append(
            "NOT EXISTS ("
            "SELECT 1 FROM event_location el "
            "WHERE el.event_id = e.event_id "
            "AND TRIM(COALESCE(el.admin_province, '')) <> ''"
            ")"
        )
    elif filters.province != "all":
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM event_location el "
            "WHERE el.event_id = e.event_id "
            "AND LOWER(TRIM(el.admin_province)) = LOWER(?)"
            ")"
        )
        params.append(filters.province)

    if filters.kabupaten != "all":
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM event_location el "
            "WHERE el.event_id = e.event_id "
            "AND LOWER(TRIM(el.admin_kabupaten_kota)) = LOWER(?)"
            ")"
        )
        params.append(filters.kabupaten)

    return " AND ".join(clauses), params


def _document_where(filters):
    clauses = [
        "d.document_status = 'active'",
        (
            "NOT EXISTS ("
            "SELECT 1 FROM document_duplicate dd "
            "WHERE dd.document_id = d.document_id"
            ")"
        ),
        (
            "EXISTS ("
            "SELECT 1 FROM document_relevance dr "
            "WHERE dr.document_id = d.document_id "
            "AND dr.relevance_status = 'relevan'"
            ")"
        ),
    ]
    params = []

    if filters.category != "all":
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM document_relevance dr "
            "WHERE dr.document_id = d.document_id "
            "AND dr.relevance_status = 'relevan' "
            "AND dr.relevance_category = ?"
            ")"
        )
        params.append(filters.category)

    if filters.date_from:
        clauses.append(
            "d.document_published_at IS NOT NULL "
            "AND d.document_published_at <> '' "
            "AND date(d.document_published_at) >= date(?)"
        )
        params.append(filters.date_from)

    if filters.date_to:
        clauses.append(
            "d.document_published_at IS NOT NULL "
            "AND d.document_published_at <> '' "
            "AND date(d.document_published_at) <= date(?)"
        )
        params.append(filters.date_to)

    if filters.province == UNKNOWN_PROVINCE:
        clauses.append(
            "NOT EXISTS ("
            "SELECT 1 FROM document_event_link l "
            "JOIN event_location el ON el.event_id = l.event_id "
            "WHERE l.document_id = d.document_id "
            "AND l.link_status = 'active' "
            "AND TRIM(COALESCE(el.admin_province, '')) <> ''"
            ")"
        )
    elif filters.province != "all":
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM document_event_link l "
            "JOIN event_location el ON el.event_id = l.event_id "
            "WHERE l.document_id = d.document_id "
            "AND l.link_status = 'active' "
            "AND LOWER(TRIM(el.admin_province)) = LOWER(?)"
            ")"
        )
        params.append(filters.province)

    if filters.kabupaten != "all":
        clauses.append(
            "EXISTS ("
            "SELECT 1 FROM document_event_link l "
            "JOIN event_location el ON el.event_id = l.event_id "
            "WHERE l.document_id = d.document_id "
            "AND l.link_status = 'active' "
            "AND LOWER(TRIM(el.admin_kabupaten_kota)) = LOWER(?)"
            ")"
        )
        params.append(filters.kabupaten)

    return " AND ".join(clauses), params


def _rows(connection, sql, params=()):
    try:
        return [dict(row) for row in connection.execute(sql, params)]
    except sqlite3.Error as exc:
        raise DashboardDataError(f"Query dashboard gagal: {exc}") from exc


def _one(connection, sql, params=()):
    rows = _rows(connection, sql, params)
    return rows[0] if rows else {}


def _event_stats(connection, event_where, event_params):
    row = _one(
        connection,
        f"""
        SELECT
            COUNT(*) AS total_events,
            COALESCE(SUM(CASE WHEN EXISTS (
                SELECT 1 FROM event_location el
                WHERE el.event_id = e.event_id
                AND (
                    (TRIM(COALESCE(el.admin_province, '')) <> '')
                    OR (el.latitude IS NOT NULL AND el.longitude IS NOT NULL)
                    OR (TRIM(COALESCE(el.location_name, '')) <> '')
                )
            ) THEN 1 ELSE 0 END), 0) AS events_with_location,
            COALESCE(SUM(CASE WHEN EXISTS (
                SELECT 1 FROM event_location el
                WHERE el.event_id = e.event_id
                AND TRIM(COALESCE(el.admin_province, '')) <> ''
            ) THEN 1 ELSE 0 END), 0) AS events_with_province,
            COALESCE(SUM(CASE WHEN EXISTS (
                SELECT 1 FROM event_location el
                WHERE el.event_id = e.event_id
                AND TRIM(COALESCE(el.admin_kabupaten_kota, '')) <> ''
            ) THEN 1 ELSE 0 END), 0) AS events_with_kabupaten_kota,
            COALESCE(SUM(CASE WHEN EXISTS (
                SELECT 1 FROM event_time et
                WHERE et.event_id = e.event_id
                AND COALESCE(NULLIF(et.event_time, ''),
                             NULLIF(et.event_time_start, '')) IS NOT NULL
            ) THEN 1 ELSE 0 END), 0) AS events_with_time
        FROM event e
        WHERE {event_where}
        """,
        event_params,
    )
    total = int(row.get("total_events") or 0)
    with_location = int(row.get("events_with_location") or 0)
    with_province = int(row.get("events_with_province") or 0)
    with_kabupaten = int(row.get("events_with_kabupaten_kota") or 0)
    return {
        "total_events": total,
        "events_with_location": with_location,
        "events_with_province": with_province,
        "events_without_province": max(total - with_province, 0),
        "events_with_kabupaten_kota": with_kabupaten,
        "events_without_kabupaten_kota": max(total - with_kabupaten, 0),
        "events_with_time": int(row.get("events_with_time") or 0),
    }


def _document_stats(connection, document_where, document_params):
    row = _one(
        connection,
        f"SELECT COUNT(*) AS total_documents FROM document d WHERE {document_where}",
        document_params,
    )
    return int(row.get("total_documents") or 0)


def _category_counts(connection, event_where, event_params, document_where, document_params):
    event_rows = _rows(
        connection,
        f"""
        SELECT c.category_name, COUNT(DISTINCT e.event_id) AS count
        FROM event e
        JOIN category c ON c.event_id = e.event_id
        WHERE {event_where}
        GROUP BY c.category_name
        """,
        event_params,
    )
    document_rows = _rows(
        connection,
        f"""
        SELECT dr.relevance_category AS category_name,
               COUNT(DISTINCT d.document_id) AS count
        FROM document d
        JOIN document_relevance dr ON dr.document_id = d.document_id
        WHERE {document_where}
          AND dr.relevance_status = 'relevan'
        GROUP BY dr.relevance_category
        """,
        document_params,
    )

    event_counts = {row["category_name"]: int(row["count"]) for row in event_rows}
    document_counts = {row["category_name"]: int(row["count"]) for row in document_rows}
    names = list(DISPLAY_CATEGORIES)
    for name in sorted(set(event_counts) | set(document_counts)):
        if name not in names:
            names.append(name)

    categories = [
        {
            "category": name,
            "event_count": event_counts.get(name, 0),
            "document_count": document_counts.get(name, 0),
        }
        for name in names
    ]
    with_data = sum(
        1
        for item in categories
        if item["event_count"] > 0 or item["document_count"] > 0
    )
    return categories, with_data, len(DISPLAY_CATEGORIES)


def _date_bounds(connection):
    event_row = _one(
        connection,
        """
        SELECT
            MIN(COALESCE(NULLIF(event_time, ''), NULLIF(event_time_start, ''))) AS min_time,
            MAX(COALESCE(NULLIF(event_time, ''), NULLIF(event_time_start, ''))) AS max_time
        FROM event_time
        """,
    )
    document_row = _one(
        connection,
        """
        SELECT
            MIN(d.document_published_at) AS min_time,
            MAX(d.document_published_at) AS max_time
        FROM document d
        JOIN document_relevance dr ON dr.document_id = d.document_id
        WHERE d.document_status = 'active'
          AND dr.relevance_status = 'relevan'
          AND d.document_published_at IS NOT NULL
          AND d.document_published_at <> ''
        """,
    )
    values = [
        value
        for value in (
            event_row.get("min_time"),
            event_row.get("max_time"),
            document_row.get("min_time"),
            document_row.get("max_time"),
        )
        if value
    ]
    if not values:
        return {"min": "", "max": ""}
    return {"min": min(values)[:10], "max": max(values)[:10]}


def _region_options(connection):
    rows = _rows(
        connection,
        """
        SELECT DISTINCT admin_province, admin_kabupaten_kota
        FROM event_location
        WHERE TRIM(COALESCE(admin_province, '')) <> ''
        ORDER BY admin_province, admin_kabupaten_kota
        """,
    )
    provinces = {}
    for row in rows:
        province = _clean_region_name(row["admin_province"])
        if not province:
            continue
        entry = provinces.setdefault(
            _region_key(province),
            {"label": province, "kabupaten": {}},
        )
        kabupaten = _clean_region_name(row["admin_kabupaten_kota"])
        if kabupaten:
            entry["kabupaten"].setdefault(
                _region_key(kabupaten),
                kabupaten,
            )

    ordered = sorted(
        provinces.values(),
        key=lambda item: item["label"].casefold(),
    )
    province_names = [item["label"] for item in ordered]
    kabupaten_by_province = {
        item["label"]: sorted(
            item["kabupaten"].values(),
            key=str.casefold,
        )
        for item in ordered
    }
    return {
        "provinces": province_names,
        "kabupaten_by_province": kabupaten_by_province,
    }


def _validate_region_filters(filters, region_options):
    if filters.kabupaten == "all":
        return None
    if filters.province == "all":
        return "kabupaten memerlukan province"
    if filters.province == UNKNOWN_PROVINCE:
        return "kabupaten tidak tersedia untuk province tidak diketahui"

    provinces = {
        _region_key(name): name for name in region_options["provinces"]
    }
    province = provinces.get(_region_key(filters.province))
    if not province:
        return "Kombinasi province dan kabupaten tidak valid"

    kabupaten_names = region_options["kabupaten_by_province"].get(province, [])
    if not any(
        _region_key(name) == _region_key(filters.kabupaten)
        for name in kabupaten_names
    ):
        return "Kombinasi province dan kabupaten tidak valid"
    return None


def _coordinate(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _map_markers(connection, event_where, event_params):
    rows = _rows(
        connection,
        f"""
        SELECT
            e.event_id,
            e.event_title,
            (
                SELECT COALESCE(
                    NULLIF(et.event_time, ''),
                    NULLIF(et.event_time_start, '')
                )
                FROM event_time et
                WHERE et.event_id = e.event_id
                ORDER BY et.event_time_id
                LIMIT 1
            ) AS event_time,
            el.event_location_id,
            el.location_name,
            el.admin_province,
            el.admin_kabupaten_kota,
            el.latitude,
            el.longitude,
            el.is_inside_indonesia,
            COALESCE((
                SELECT c.category_name
                FROM category c
                WHERE c.event_id = e.event_id
                ORDER BY
                    CASE c.category_rank WHEN 'primary' THEN 0 ELSE 1 END,
                    c.category_name
                LIMIT 1
            ), ?) AS category
        FROM event e
        JOIN event_location el ON el.event_id = e.event_id
        WHERE {event_where}
        ORDER BY e.event_id, el.event_location_id
        """,
        [OTHER_CATEGORY, *event_params],
    )

    markers_by_event = {}
    for row in rows:
        event_id = row["event_id"]
        if event_id in markers_by_event:
            continue
        latitude = _coordinate(row["latitude"])
        longitude = _coordinate(row["longitude"])
        if latitude is None or longitude is None:
            continue
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue
        markers_by_event[event_id] = {
            "event_id": event_id,
            "event_title": row["event_title"],
            "category": row["category"] or OTHER_CATEGORY,
            "event_time": row["event_time"] or "",
            "location_name": _clean_region_name(row["location_name"]),
            "province": _clean_region_name(row["admin_province"]),
            "kabupaten": _clean_region_name(row["admin_kabupaten_kota"]),
            "latitude": latitude,
            "longitude": longitude,
            "is_inside_indonesia": row["is_inside_indonesia"] or "",
            "document_count": 0,
            "documents": [],
        }

    if not markers_by_event:
        return [], {name: 0 for name in DISPLAY_CATEGORIES}

    event_ids = sorted(markers_by_event)
    placeholders = ",".join("?" for _ in event_ids)
    document_rows = _rows(
        connection,
        f"""
        SELECT
            l.event_id,
            d.document_id,
            d.document_title,
            COALESCE(
                NULLIF(d.document_source_label, ''),
                NULLIF(s.source_name, ''),
                NULLIF(d.document_publisher, ''),
                'Tidak diketahui'
            ) AS source,
            COALESCE(
                NULLIF(d.document_url, ''),
                NULLIF(d.document_url_canonical, '')
            ) AS url,
            d.document_published_at
        FROM document_event_link l
        JOIN document d ON d.document_id = l.document_id
        JOIN document_relevance dr ON dr.document_id = d.document_id
        LEFT JOIN source s ON s.source_id = d.document_source_id
        WHERE l.event_id IN ({placeholders})
          AND l.link_status = 'active'
          AND d.document_status = 'active'
          AND dr.relevance_status = 'relevan'
          AND NOT EXISTS (
              SELECT 1 FROM document_duplicate dd
              WHERE dd.document_id = d.document_id
          )
        ORDER BY
            l.event_id,
            (d.document_published_at IS NULL OR d.document_published_at = ''),
            d.document_published_at DESC,
            d.document_id
        """,
        event_ids,
    )

    seen_documents = set()
    for row in document_rows:
        key = (row["event_id"], row["document_id"])
        if key in seen_documents:
            continue
        seen_documents.add(key)
        marker = markers_by_event.get(row["event_id"])
        if not marker:
            continue
        marker["documents"].append(
            {
                "document_id": row["document_id"],
                "title": row["document_title"],
                "source": row["source"],
                "url": row["url"] or "",
                "published_at": row["document_published_at"] or "",
            }
        )

    marker_categories = {name: 0 for name in DISPLAY_CATEGORIES}
    markers = []
    for event_id in event_ids:
        marker = markers_by_event[event_id]
        marker["document_count"] = len(marker["documents"])
        category = marker["category"]
        marker_categories[category] = marker_categories.get(category, 0) + 1
        markers.append(marker)

    return markers, marker_categories


def _category_options(connection):
    rows = _rows(
        connection,
        """
        SELECT category_name FROM category
        UNION
        SELECT relevance_category AS category_name FROM document_relevance
        WHERE relevance_status = 'relevan'
        UNION
        SELECT category_name FROM document_classification
        ORDER BY category_name
        """,
    )
    names = list(DISPLAY_CATEGORIES)
    for row in rows:
        name = row["category_name"]
        if name and name not in names:
            names.append(name)
    return names


def _period_label(period, granularity):
    if granularity == "month":
        year, month = period.split("-")
        return f"{MONTH_NAMES[int(month) - 1]} {year}"
    parsed = datetime.strptime(period, "%Y-%m-%d").date()
    return f"{parsed.day} {MONTH_NAMES[parsed.month - 1]} {parsed.year}"


def _next_month(value):
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _periods(start, end, granularity):
    current = start
    if granularity == "month":
        current = date(current.year, current.month, 1)
        while current <= end:
            yield current.strftime("%Y-%m")
            current = _next_month(current)
        return

    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)


def _trend(connection, filters, event_where, event_params):
    rows = _rows(
        connection,
        f"""
        SELECT
            substr(
                COALESCE(NULLIF(et.event_time, ''), NULLIF(et.event_time_start, '')),
                1,
                10
            ) AS event_date,
            COUNT(DISTINCT e.event_id) AS count
        FROM event e
        JOIN event_time et ON et.event_id = e.event_id
        WHERE {event_where}
          AND COALESCE(NULLIF(et.event_time, ''),
                       NULLIF(et.event_time_start, '')) IS NOT NULL
        GROUP BY event_date
        ORDER BY event_date
        """,
        event_params,
    )
    if not rows:
        granularity = "month" if filters.granularity == "auto" else filters.granularity
        return {"granularity": granularity, "label": "", "points": []}

    counts = {row["event_date"]: int(row["count"]) for row in rows}
    start = datetime.strptime(min(counts), "%Y-%m-%d").date()
    end = datetime.strptime(max(counts), "%Y-%m-%d").date()
    granularity = filters.granularity
    if granularity == "auto":
        span_days = (end - start).days + 1
        granularity = "month" if span_days > 62 else "day"

    periods = []
    if granularity == "month":
        monthly = {}
        for event_date, count in counts.items():
            period = event_date[:7]
            monthly[period] = monthly.get(period, 0) + count
        for period in _periods(start, end, "month"):
            periods.append(
                {
                    "period": period,
                    "label": _period_label(period, "month"),
                    "count": monthly.get(period, 0),
                }
            )
    else:
        for period in _periods(start, end, "day"):
            periods.append(
                {
                    "period": period,
                    "label": _period_label(period, "day"),
                    "count": counts.get(period, 0),
                }
            )

    return {
        "granularity": granularity,
        "label": "Bulanan" if granularity == "month" else "Harian",
        "points": periods,
    }


def _regions(connection, event_where, event_params):
    rows = _rows(
        connection,
        f"""
        SELECT
            CASE
                WHEN el.admin_province IS NULL OR el.admin_province = ''
                THEN ?
                ELSE el.admin_province
            END AS province,
            COUNT(DISTINCT e.event_id) AS count
        FROM event e
        LEFT JOIN event_location el ON el.event_id = e.event_id
        WHERE {event_where}
        GROUP BY province
        ORDER BY count DESC, province
        """,
        [UNKNOWN_PROVINCE_LABEL, *event_params],
    )
    items = [
        {"province": row["province"], "count": int(row["count"])}
        for row in rows
    ]
    unknown = next(
        (item["count"] for item in items if item["province"] == UNKNOWN_PROVINCE_LABEL),
        0,
    )
    return {
        "items": items,
        "unknown": unknown,
        "known_total": sum(item["count"] for item in items) - unknown,
    }


def _latest_news(connection, document_where, document_params, limit=20):
    rows = _rows(
        connection,
        f"""
        SELECT
            d.document_id,
            d.document_title,
            COALESCE(
                NULLIF(d.document_source_label, ''),
                NULLIF(s.source_name, ''),
                NULLIF(d.document_publisher, ''),
                'Tidak diketahui'
            ) AS source,
            d.document_published_at,
            dr.relevance_category AS category,
            dr.relevance_status,
            COALESCE(
                NULLIF(d.document_url, ''),
                NULLIF(d.document_url_canonical, '')
            ) AS url
        FROM document d
        JOIN document_relevance dr ON dr.document_id = d.document_id
        LEFT JOIN source s ON s.source_id = d.document_source_id
        WHERE {document_where}
          AND dr.relevance_status = 'relevan'
        ORDER BY
            (d.document_published_at IS NULL OR d.document_published_at = ''),
            d.document_published_at DESC,
            d.document_id
        LIMIT ?
        """,
        [*document_params, limit],
    )
    return rows


def _escape_like(value):
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _search_where(filters):
    dashboard_filters = DashboardFilters(
        category=filters.category,
        date_from=filters.date_from,
        date_to=filters.date_to,
    )
    where, params = _document_where(dashboard_filters)
    clauses = [where]

    if filters.q:
        pattern = f"%{_escape_like(filters.q)}%"
        clauses.append(
            "("
            "d.document_title LIKE ? ESCAPE '\\' "
            "OR d.document_notes LIKE ? ESCAPE '\\' "
            "OR EXISTS ("
            "SELECT 1 FROM document_event_link l "
            "JOIN event e ON e.event_id = l.event_id "
            "WHERE l.document_id = d.document_id "
            "AND l.link_status = 'active' "
            "AND e.event_summary LIKE ? ESCAPE '\\'"
            ")"
            ")"
        )
        params.extend([pattern, pattern, pattern])

    if filters.source != "all":
        clauses.append(
            f"LOWER(TRIM({SOURCE_LABEL_SQL})) = LOWER(?)"
        )
        params.append(filters.source)

    return " AND ".join(clauses), params


def _search_source_options(connection):
    return _rows(
        connection,
        f"""
        SELECT
            {SOURCE_LABEL_SQL} AS source,
            COUNT(*) AS count
        FROM document d
        JOIN document_relevance dr ON dr.document_id = d.document_id
        LEFT JOIN source s ON s.source_id = d.document_source_id
        WHERE d.document_status = 'active'
          AND dr.relevance_status = 'relevan'
          AND NOT EXISTS (
              SELECT 1 FROM document_duplicate dd
              WHERE dd.document_id = d.document_id
          )
        GROUP BY source
        ORDER BY
            CASE WHEN source = ? THEN 1 ELSE 0 END,
            source
        """,
        (UNKNOWN_SOURCE_LABEL,),
    )


def _search_date_bounds(connection):
    row = _one(
        connection,
        """
        SELECT
            MIN(d.document_published_at) AS min_time,
            MAX(d.document_published_at) AS max_time
        FROM document d
        JOIN document_relevance dr ON dr.document_id = d.document_id
        WHERE d.document_status = 'active'
          AND dr.relevance_status = 'relevan'
          AND d.document_published_at IS NOT NULL
          AND d.document_published_at <> ''
          AND NOT EXISTS (
              SELECT 1 FROM document_duplicate dd
              WHERE dd.document_id = d.document_id
          )
        """,
    )
    return {
        "min": (row.get("min_time") or "")[:10],
        "max": (row.get("max_time") or "")[:10],
    }


def search_news(db_path=None, filters=None):
    filters = filters or NewsSearchFilters()
    started = time.perf_counter()

    with closing(connect(db_path)) as connection:
        where, params = _search_where(filters)
        total = int(
            _one(
                connection,
                f"""
                SELECT COUNT(*) AS total
                FROM document d
                JOIN document_relevance dr ON dr.document_id = d.document_id
                LEFT JOIN source s ON s.source_id = d.document_source_id
                WHERE {where}
                  AND dr.relevance_status = 'relevan'
                """,
                params,
            ).get("total")
            or 0
        )
        pages = max(1, math.ceil(total / filters.per_page)) if total else 0
        page = min(filters.page, pages) if pages else 1
        offset = (page - 1) * filters.per_page

        results = _rows(
            connection,
            f"""
            SELECT
                d.document_id,
                d.document_title,
                {SOURCE_LABEL_SQL} AS source,
                d.document_published_at,
                dr.relevance_category AS category,
                dr.relevance_status,
                dr.relevance_basis,
                COALESCE(
                    NULLIF(d.document_url, ''),
                    NULLIF(d.document_url_canonical, '')
                ) AS url,
                (
                    SELECT l.event_id
                    FROM document_event_link l
                    WHERE l.document_id = d.document_id
                      AND l.link_status = 'active'
                    ORDER BY l.is_primary DESC, l.event_id
                    LIMIT 1
                ) AS related_event_id
            FROM document d
            JOIN document_relevance dr ON dr.document_id = d.document_id
            LEFT JOIN source s ON s.source_id = d.document_source_id
            WHERE {where}
              AND dr.relevance_status = 'relevan'
            ORDER BY
                (d.document_published_at IS NULL OR d.document_published_at = ''),
                d.document_published_at DESC,
                d.document_id
            LIMIT ? OFFSET ?
            """,
            [*params, filters.per_page, offset],
        )
        options = {
            "categories": _category_options(connection),
            "sources": _search_source_options(connection),
            "date_bounds": _search_date_bounds(connection),
        }

    return {
        "query": filters.q,
        "filters": filters.as_dict(),
        "results": results,
        "pagination": {
            "page": page,
            "per_page": filters.per_page,
            "total": total,
            "pages": pages,
            "has_prev": page > 1,
            "has_next": page < pages,
        },
        "options": options,
        "meta": {
            "search_basis": (
                "Pencarian judul, catatan/teks dokumen tersimpan, dan ringkasan "
                "kejadian terkait; hanya dokumen aktif relevan non-duplikat."
            ),
            "time_basis": (
                "Filter tanggal memakai document_published_at, bukan event_time."
            ),
            "query_ms": round((time.perf_counter() - started) * 1000, 1),
        },
    }


def build_event_detail(db_path=None, event_id=None):
    event_id = str(event_id or "").strip()
    if not event_id:
        return None
    started = time.perf_counter()

    with closing(connect(db_path)) as connection:
        event = _one(
            connection,
            """
            SELECT
                e.*,
                s.source_name AS primary_source_name,
                s.source_institution AS primary_source_institution
            FROM event e
            LEFT JOIN source s ON s.source_id = e.event_primary_source_id
            WHERE e.event_id = ?
            """,
            (event_id,),
        )
        if not event:
            return None

        categories = _rows(
            connection,
            """
            SELECT category_name, category_rank, category_scope, category_basis
            FROM category
            WHERE event_id = ?
            ORDER BY
                CASE category_rank WHEN 'primary' THEN 0 ELSE 1 END,
                category_name
            """,
            (event_id,),
        )
        times = _rows(
            connection,
            """
            SELECT *
            FROM event_time
            WHERE event_id = ?
            ORDER BY
                CASE
                    WHEN COALESCE(NULLIF(event_time, ''),
                                  NULLIF(event_time_start, '')) IS NULL
                    THEN 1 ELSE 0
                END,
                event_time_id
            """,
            (event_id,),
        )
        locations = _rows(
            connection,
            """
            SELECT *
            FROM event_location
            WHERE event_id = ?
            ORDER BY event_location_id
            """,
            (event_id,),
        )
        attributes = _rows(
            connection,
            """
            SELECT ea.*, s.source_name, s.source_institution
            FROM event_attribute ea
            LEFT JOIN source s ON s.source_id = ea.attribute_source_id
            WHERE ea.event_id = ?
            ORDER BY ea.attribute_name, ea.event_attribute_id
            """,
            (event_id,),
        )
        supporting_news = _rows(
            connection,
            f"""
            SELECT
                d.document_id,
                d.document_title,
                {SOURCE_LABEL_SQL} AS source,
                d.document_published_at,
                dr.relevance_category AS category,
                dr.relevance_status,
                dr.relevance_basis,
                COALESCE(
                    NULLIF(d.document_url, ''),
                    NULLIF(d.document_url_canonical, '')
                ) AS url,
                l.relation_type,
                l.is_primary
            FROM document_event_link l
            JOIN document d ON d.document_id = l.document_id
            JOIN document_relevance dr ON dr.document_id = d.document_id
            LEFT JOIN source s ON s.source_id = d.document_source_id
            WHERE l.event_id = ?
              AND l.link_status = 'active'
              AND d.document_status = 'active'
              AND dr.relevance_status = 'relevan'
              AND NOT EXISTS (
                  SELECT 1 FROM document_duplicate dd
                  WHERE dd.document_id = d.document_id
              )
            ORDER BY
                (d.document_published_at IS NULL OR d.document_published_at = ''),
                d.document_published_at DESC,
                d.document_id
            """,
            (event_id,),
        )

    location_items = []
    for row in locations:
        location_items.append(
            {
                **row,
                "location_name": _clean_region_name(row.get("location_name")),
                "province": _clean_region_name(row.get("admin_province")),
                "kabupaten": _clean_region_name(row.get("admin_kabupaten_kota")),
                "kecamatan": _clean_region_name(row.get("admin_kecamatan")),
                "desa_kelurahan": _clean_region_name(
                    row.get("admin_desa_kelurahan")
                ),
                "latitude": _coordinate(row.get("latitude")),
                "longitude": _coordinate(row.get("longitude")),
            }
        )

    event["event_summary"] = str(event.get("event_summary") or "").strip()
    event["event_notes"] = str(event.get("event_notes") or "").strip()
    return {
        "event": event,
        "categories": categories,
        "primary_category": (
            categories[0]["category_name"] if categories else OTHER_CATEGORY
        ),
        "time": times[0] if times else None,
        "times": times,
        "locations": location_items,
        "attributes": attributes,
        "supporting_news": supporting_news,
        "meta": {
            "time_basis": (
                "Waktu kejadian memakai event_time; publication time berita "
                "tetap terpisah."
            ),
            "location_basis": (
                "Provinsi dan kabupaten/kota hanya dari kolom admin event_location; "
                "tidak ditebak dari koordinat."
            ),
            "news_basis": (
                "Berita pendukung hanya dokumen aktif relevan non-duplikat yang "
                "terhubung aktif ke event ini."
            ),
            "query_ms": round((time.perf_counter() - started) * 1000, 1),
        },
    }


def build_dashboard(db_path=None, filters=None, latest_limit=20):
    filters = filters or DashboardFilters()
    started = time.perf_counter()

    with closing(connect(db_path)) as connection:
        event_where, event_params = _event_where(filters)
        document_where, document_params = _document_where(filters)
        region_options = _region_options(connection)
        validation_error = _validate_region_filters(filters, region_options)
        if validation_error:
            raise ValueError(validation_error)

        event_stats = _event_stats(connection, event_where, event_params)
        total_documents = _document_stats(
            connection, document_where, document_params
        )
        categories, categories_with_data, monitored_categories = _category_counts(
            connection,
            event_where,
            event_params,
            document_where,
            document_params,
        )
        trend = _trend(connection, filters, event_where, event_params)
        regions = _regions(connection, event_where, event_params)
        latest_news = _latest_news(
            connection,
            document_where,
            document_params,
            max(1, min(int(latest_limit), 100)),
        )
        markers, marker_categories = _map_markers(
            connection,
            event_where,
            event_params,
        )
        options = {
            "categories": _category_options(connection),
            "provinces": region_options["provinces"],
            "kabupaten_by_province": region_options["kabupaten_by_province"],
            "date_bounds": _date_bounds(connection),
        }

    return {
        "filters": filters.as_dict(),
        "stats": {
            "total_documents": total_documents,
            "total_events": event_stats["total_events"],
            "total_categories": categories_with_data,
            "monitored_categories": monitored_categories,
            "events_with_location": event_stats["events_with_location"],
            "events_with_province": event_stats["events_with_province"],
            "events_without_province": event_stats["events_without_province"],
            "events_with_kabupaten_kota": event_stats[
                "events_with_kabupaten_kota"
            ],
            "events_without_kabupaten_kota": event_stats[
                "events_without_kabupaten_kota"
            ],
            "events_with_time": event_stats["events_with_time"],
        },
        "categories": categories,
        "trend": trend,
        "regions": regions,
        "latest_news": latest_news,
        "map": {
            "markers": markers,
            "stats": {
                "total_events": event_stats["total_events"],
                "events_with_coordinates": len(markers),
                "events_without_coordinates": max(
                    event_stats["total_events"] - len(markers), 0
                ),
                "marker_count": len(markers),
                "markers_outside_indonesia": sum(
                    1
                    for marker in markers
                    if marker["is_inside_indonesia"] == "tidak"
                ),
                "marker_categories": marker_categories,
            },
        },
        "options": options,
        "meta": {
            "document_basis": (
                "Dokumen aktif yang relevan; duplikat dikecualikan; "
                "status relevansi disimpan terpisah dari kategori."
            ),
            "event_basis": "Seluruh baris tabel event setelah filter.",
            "time_basis": "event_time untuk kejadian; document_published_at untuk berita.",
            "location_basis": (
                "Provinsi dan kabupaten/kota hanya dari admin_province dan "
                "admin_kabupaten_kota; koordinat tidak dipakai untuk menebak "
                "wilayah. Dokumen wilayah mengikuti document_event_link."
            ),
            "map_basis": (
                "Marker memakai satu koordinat event_location yang valid; "
                "event tanpa koordinat valid tetap dihitung di statistik."
            ),
            "query_ms": round((time.perf_counter() - started) * 1000, 1),
        },
    }
