#!/usr/bin/env python3
"""Pilot pengumpulan data kejadian resmi geohazard dengan provenance."""

import csv
import hashlib
import html
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

try:
    import requests
except ImportError:  # pragma: no cover - hanya dibutuhkan saat fetch sumber
    requests = None
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import dataset_baseline
import geographic_scope as geo

PILOT_ROOT = ROOT / "data" / "pilot"
RUNS_DIR = PILOT_ROOT / "runs"
REGISTER_PATH = ROOT / "docs" / "MASTER_SOURCE_REGISTER.csv"
DICTIONARY_PATH = ROOT / "docs" / "PROVENANCE_FIELD_DICTIONARY.csv"
SCHEMA_VERSION = "1.0.0"
MAX_ITEMS_PER_SOURCE = None
DELAY_SECONDS = 1.2
TIMEOUT_SECONDS = 30
# Bbox pilot untuk fetch/sanity check, bukan batas wilayah nasional.
INDONESIA_BBOX = (-11.0, 6.0, 95.0, 141.0)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "GeoHazard-News-Locator-Pilot/1.0"
    ),
    "Accept": (
        "application/atom+xml, application/xml, text/xml, "
        "application/rss+xml, */*"
    ),
}
SOURCE_CONFIG = [
    {
        "source_id": "bmkg_autogempa",
        "source_url": "https://data.bmkg.go.id/",
        "role": "primary_official",
        "language": "id",
        "country": "Indonesia",
        "parser": "bmkg",
        "priority": 0,
        "max_items": None,
    },
    {
        "source_id": "bmkg_gempa_terkini",
        "source_url": "https://data.bmkg.go.id/",
        "role": "primary_official",
        "language": "id",
        "country": "Indonesia",
        "parser": "bmkg",
        "priority": 1,
        "max_items": None,
    },
    {
        "source_id": "bmkg_gempa_dirasakan",
        "source_url": "https://data.bmkg.go.id/",
        "role": "primary_official",
        "language": "id",
        "country": "Indonesia",
        "parser": "bmkg",
        "priority": 2,
        "max_items": None,
    },
    {
        "source_id": "usgs_m45",
        "source_url": "https://earthquake.usgs.gov/earthquakes/",
        "role": "supporting_official",
        "language": "en",
        "country": "internasional",
        "parser": "usgs",
        "priority": 3,
        "max_items": None,
    },
]
KEY_FIELDS = {
    "source": "source_id",
    "raw_payload": "raw_payload_id",
    "document": "document_id",
    "event": "event_id",
    "event_time": "event_time_id",
    "location_mention": "location_mention_id",
    "event_location": "event_location_id",
    "category": "category_assignment_id",
    "document_event_link": "link_id",
    "event_assertion": "assertion_id",
    "event_relation": "event_relation_id",
    "verification": "verification_id",
    "change_log": "change_id",
    "event_attribute": "event_attribute_id",
}
ENTITY_ORDER = [
    "source",
    "raw_payload",
    "document",
    "event",
    "event_time",
    "location_mention",
    "event_location",
    "category",
    "document_event_link",
    "event_assertion",
    "event_relation",
    "verification",
    "change_log",
    "event_attribute",
]
ALLOWED_CATEGORIES = {
    "Gunungapi",
    "Gempabumi",
    "Tsunami",
    "Gerakan Tanah/Tanah Longsor",
    "Likuefaksi",
    "Abrasi dan Akresi",
    "Penurunan Muka Tanah",
    "Semburan Gas dan Lumpur",
    "Lainnya",
}
TSUNAMI_POTENTIAL_VALUES = {"positive", "negative", "unknown"}
TSUNAMI_UNKNOWN_PATTERNS = (
    r"\b(?:tidak|belum)\s+(?:tersedia|diketahui|jelas|dipastikan|diperoleh)\b[^.!?;]{0,60}\btsunami\b",
    r"\btsunami\b[^.!?;]{0,60}\b(?:tidak|belum)\s+(?:diketahui|tersedia|jelas|dipastikan)\b",
    r"\b(?:tidak|belum)\s+ada\s+(?:informasi|laporan|data|peringatan|warning|alert|pengumuman)\b[^.!?;]{0,60}\btsunami\b",
    r"\b(?:no|not|without)\b[^.!?;]{0,40}\b(?:information|data|reports?|details?|confirmation|confirmed|warning|alert)\b[^.!?;]{0,40}\btsunami\b",
    r"\b(?:no|without)\b[^.!?;]{0,20}\btsunami\b[^.!?;]{0,20}\b(?:warning|alert|advisory|watch)\b",
    r"\b(?:unknown|unavailable|not available|no information|no data)\b[^.!?;]{0,60}\btsunami\b",
    r"\btsunami\b[^.!?;]{0,60}\b(?:unknown|unavailable|not available|no information|no data|no reports?|unconfirmed|not confirmed)\b",
)
TSUNAMI_NEGATIVE_PATTERNS = (
    r"\b(?:tidak|bukan|tanpa)\b[^.!?;]{0,60}\b(?:berpotensi|potensi|menimbulkan|menyebabkan|mengancam|bahaya|ancaman|terjadi|terdeteksi|ditemukan|menghasilkan|generated?|cause)\b[^.!?;]{0,40}\btsunami\b",
    r"\b(?:tidak|bukan|tanpa|no|not|without|zero)\b[^.!?;]{0,40}\btsunami\b",
    r"\btsunami\b[^.!?;]{0,60}\b(?:tidak|bukan|tanpa|no|not|without|zero|none|negative|absent|not expected|not generated|not observed)\b",
    r"\b(?:no|not|without|zero|none)\b[^.!?;]{0,40}\b(?:potential|threat|risk)\b[^.!?;]{0,40}\btsunami\b",
)
TSUNAMI_POSITIVE_PATTERNS = (
    r"\b(?:berpotensi|potensi|potensial|menimbulkan|menyebabkan|mengancam|terdeteksi|terjadi|observed|issued|possible|possibly|potential|threat|risk|warning|alert|advisory|watch|waspada|peringatan|expected|may|could|can)\b[^.!?;]{0,60}\btsunami\b",
    r"\btsunami\b[^.!?;]{0,60}\b(?:warning|alert|advisory|watch|waspada|peringatan|terdeteksi|terjadi|observed|issued|possible|potensial|potential|threat|risk|expected)\b",
    r"\btsunami\b[^.!?;]{0,30}\b(?:may|could|can)\s+occur\b",
)


def utc_now():
    return datetime.now(timezone.utc)


def iso_utc(value=None):
    return (value or utc_now()).astimezone(timezone.utc).isoformat()


def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_dictionary():
    fields = defaultdict(list)
    for row in read_csv(DICTIONARY_PATH):
        fields[row["entity"]].append(row["field_name"])
    return dict(fields)


def load_register():
    return {row["source_id"]: row for row in read_csv(REGISTER_PATH)}


def empty_row(fields):
    return {field: "" for field in fields}


def parse_iso(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_usgs_time(value):
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return None
    return parsed.replace(tzinfo=timezone.utc)


def normalize_robots(value):
    text = (value or "").lower()
    if "dilarang" in text or "disallowed" in text:
        return "disallowed"
    if "tidak_terbaca" in text or "ssl" in text or "httperror" in text:
        return "unreadable"
    if "tidak ditemukan" in text or "404" in text:
        return "not_found"
    if "diizinkan" in text or "allowed" in text:
        return "allowed"
    return "not_checked"


def strip_summary(value):
    text = html.unescape(value or "")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def summary_field(value, label):
    pattern = rf"<dt>{re.escape(label)}</dt><dd>(.*?)</dd>"
    match = re.search(pattern, value or "", flags=re.I | re.S)
    return strip_summary(match.group(1)) if match else ""


def is_inside_bbox(lat, lon):
    """Cek bbox pilot; bukan penentuan geographic scope Indonesia."""
    south, north, west, east = INDONESIA_BBOX
    return south <= lat <= north and west <= lon <= east


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def choose_run_id():
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    base = f"PILOT-{stamp}"
    candidate = base
    number = 2
    while (RUNS_DIR / candidate).exists():
        candidate = f"{base}-{number:02d}"
        number += 1
    return candidate


def make_run_dir(run_id):
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "raw").mkdir()
    (run_dir / "tables").mkdir()
    return run_dir


def fetch_source(config, register):
    source_id = config["source_id"]
    feed_url = register[source_id]["url"]
    retrieved_at = iso_utc()
    if requests is None:
        return {
            "config": config,
            "feed_url": feed_url,
            "retrieved_at": retrieved_at,
            "http_status": "",
            "content_type": "",
            "content": b"",
            "error": "Modul requests tidak terpasang.",
        }
    try:
        response = requests.get(
            feed_url,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        return {
            "config": config,
            "feed_url": feed_url,
            "retrieved_at": retrieved_at,
            "http_status": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "content": response.content,
            "error": "",
        }
    except requests.RequestException as exc:
        return {
            "config": config,
            "feed_url": feed_url,
            "retrieved_at": retrieved_at,
            "http_status": "",
            "content_type": "",
            "content": b"",
            "error": str(exc),
        }


def parse_bmkg_items(content, config):
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return [], f"XML tidak valid: {exc}"
    items = []
    for gempa in root.iter("gempa"):
        data = {
            child.tag: (child.text or "").strip()
            for child in gempa
            if child.tag != "point"
        }
        coordinates = (gempa.findtext("point/coordinates") or "").strip()
        parts = [part.strip() for part in coordinates.split(",")]
        if len(parts) != 2:
            continue
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            magnitude = float(data.get("Magnitude", ""))
        except ValueError:
            continue
        event_time = parse_iso(data.get("DateTime", ""))
        if event_time is None:
            continue
        external_id = (
            f"{config['source_id']}|{event_time.isoformat()}|"
            f"{lat:.4f}|{lon:.4f}|{magnitude:.1f}"
        )
        items.append(
            {
                "source_id": config["source_id"],
                "priority": config["priority"],
                "external_id": external_id,
                "title": (
                    f"Gempa M{magnitude:g} - "
                    f"{data.get('Wilayah', 'Wilayah tidak tercantum')}"
                ),
                "event_time": event_time,
                "event_time_evidence": (
                    f"DateTime={data.get('DateTime', '')}; "
                    f"Tanggal={data.get('Tanggal', '')}; "
                    f"Jam={data.get('Jam', '')}"
                ),
                "lat": lat,
                "lon": lon,
                "magnitude": magnitude,
                "magnitude_text": data.get("Magnitude", ""),
                "depth_text": data.get("Kedalaman", ""),
                "location_name": data.get("Wilayah", ""),
                "category_original": "Gempa Bumi",
                "extra": {
                    "potensi": data.get("Potensi", ""),
                    "dirasakan": data.get("Dirasakan", ""),
                    "shakemap": data.get("Shakemap", ""),
                },
                "event_key": (
                    f"BMKG|{event_time.isoformat()}|{lat:.2f}|"
                    f"{lon:.2f}|{magnitude:.1f}"
                ),
            }
        )
    return items, ""


def parse_usgs_items(content):
    namespace = {
        "atom": "http://www.w3.org/2005/Atom",
        "georss": "http://www.georss.org/georss",
    }
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return [], 0, f"Atom tidak valid: {exc}"
    items = []
    total_entries = 0
    for entry in root.findall("atom:entry", namespace):
        total_entries += 1
        point = (
            entry.findtext("georss:point", default="", namespaces=namespace) or ""
        ).strip()
        parts = point.split()
        if len(parts) != 2:
            continue
        try:
            lat = float(parts[0])
            lon = float(parts[1])
        except ValueError:
            continue
        if not is_inside_bbox(lat, lon):
            continue
        title = (
            entry.findtext("atom:title", default="", namespaces=namespace) or ""
        ).strip()
        native_id = (
            entry.findtext("atom:id", default="", namespaces=namespace) or ""
        ).strip()
        native_id = native_id.rsplit(":", 1)[-1]
        link_element = entry.find("atom:link[@rel='alternate']", namespace)
        link = link_element.get("href", "") if link_element is not None else ""
        summary = (
            entry.findtext("atom:summary", default="", namespaces=namespace) or ""
        )
        event_time = parse_usgs_time(summary_field(summary, "Time"))
        if event_time is None:
            continue
        magnitude_match = re.search(r"M\s+([0-9.]+)", title)
        if magnitude_match is None:
            continue
        magnitude = float(magnitude_match.group(1))
        depth_text = summary_field(summary, "Depth")
        location_name = title.split(" - ", 1)[1] if " - " in title else title
        updated = parse_iso(
            entry.findtext("atom:updated", default="", namespaces=namespace)
        )
        items.append(
            {
                "source_id": "usgs_m45",
                "priority": 3,
                "external_id": native_id,
                "native_id": native_id,
                "title": title,
                "event_time": event_time,
                "event_time_evidence": (
                    f"summary Time: {event_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                ),
                "lat": lat,
                "lon": lon,
                "magnitude": magnitude,
                "magnitude_text": magnitude_match.group(1),
                "depth_text": depth_text,
                "location_name": location_name,
                "category_original": "Earthquake",
                "updated_at": updated,
                "document_url": link,
                "extra": {},
                "event_key": f"USGS|{native_id}",
            }
        )
    return items, total_entries, ""


def build_source_row(register_row, config, http_status, retrieval_time):
    return {
        "source_id": config["source_id"],
        "source_name": register_row["nama_sumber"],
        "source_institution": register_row["institusi"],
        "source_country": config["country"],
        "source_language": config["language"],
        "source_type": "official",
        "source_role": config["role"],
        "source_data_type": "event_feed",
        "source_url": config["source_url"],
        "source_feed_url": register_row["url"],
        "source_registry_status": register_row["status_sumber"],
        "source_license_status": "unverified",
        "source_license": "belum_diverifikasi",
        "source_terms_url": "",
        "source_last_tested_at": retrieval_time,
        "source_http_status": http_status,
        "source_robots_status": normalize_robots(register_row["robots"]),
        "source_notes": (
            f"{register_row['catatan']} Pilot internal; lisensi belum "
            "diverifikasi; satu GET per sumber."
        ).strip(),
    }


def build_raw_row(source_id, feed_url, fetch, run_dir, run_id):
    content = fetch["content"]
    digest = sha256_bytes(content)
    raw_id = (
        f"RAW-{source_id}-{run_id.replace('PILOT-', '')}-{digest[:8]}"
    )
    extension = "atom" if source_id == "usgs_m45" else "xml"
    path = run_dir / "raw" / f"{source_id}.{extension}"
    if content:
        with open(path, "xb") as handle:
            handle.write(content)
    relative_path = (
        str(path.relative_to(ROOT)).replace("\\", "/") if content else ""
    )
    return {
        "raw_payload_id": raw_id,
        "raw_payload_source_id": source_id,
        "raw_payload_url": feed_url,
        "raw_payload_retrieved_at": fetch["retrieved_at"],
        "raw_payload_http_status": fetch["http_status"],
        "raw_payload_content_type": fetch["content_type"],
        "raw_payload_sha256": digest,
        "raw_payload_size_bytes": len(content),
        "raw_payload_path": relative_path,
        "raw_payload_status": "stored" if content else "missing",
        "raw_payload_notes": (
            "Snapshot respons mentah pilot; tidak ditimpa."
            if content
            else f"Respons kosong/gagal: {fetch['error']}"
        ),
    }


def event_identity(item):
    if item["source_id"] == "usgs_m45":
        return f"EVT-USGS-{item['native_id']}", item["native_id"]
    event_id = "EVT-BMKG-" + sha256_text(item["event_key"])[:12].upper()
    return event_id, ""


def document_identity(item, feed_url):
    if item["source_id"] == "usgs_m45":
        canonical = item["document_url"]
    else:
        canonical = f"{feed_url}#record={quote(item['external_id'], safe='')}"
    document_id = (
        "DOC-" + sha256_text(f"{item['source_id']}|{item['external_id']}")[:16]
    )
    return document_id, canonical


def build_document(item, fetch, raw_row, run_id, dictionary):
    document_id, canonical = document_identity(item, fetch["feed_url"])
    register = item["register_row"]
    doc = empty_row(dictionary["document"])
    doc.update(
        {
            "document_id": document_id,
            "document_type": "official_event_record",
            "document_source_id": item["source_id"],
            "document_source_label": register["nama_sumber"],
            "document_source_identity_status": "registered",
            "document_source_type": "official",
            "document_source_role": item["role"],
            "document_url": canonical,
            "document_url_canonical": canonical,
            "document_title": item["title"],
            "document_publisher": register["institusi"],
            "document_language": item["language"],
            "document_external_id": item["external_id"],
            "document_content_hash": sha256_text(
                json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
            ),
            "document_raw_payload_id": raw_row["raw_payload_id"],
            "document_retrieved_at": fetch["retrieved_at"],
            "document_updated_at": (
                item["updated_at"].isoformat() if item.get("updated_at") else ""
            ),
            "document_run_id": run_id,
            "document_status": "available",
            "document_provenance_status": "complete",
            "document_notes": (
                "Record resmi dari feed XML BMKG; tidak ada halaman kejadian "
                "permanen per item, sehingga URL memakai feed dan fragmen record."
                if item["source_id"] != "usgs_m45"
                else "Entry Atom resmi USGS; waktu kejadian diambil dari summary."
            ),
        }
    )
    return doc


def build_event_group(items, dictionary):
    items = sorted(
        items, key=lambda value: (value["priority"], value["retrieved_at"])
    )
    primary = items[0]
    event_id, native_id = event_identity(primary)
    event = empty_row(dictionary["event"])
    event.update(
        {
            "event_id": event_id,
            "event_source_native_id": native_id,
            "event_primary_source_id": primary["source_id"],
            "event_title": primary["title"],
            "event_status": "confirmed",
            "event_verification_status": "official",
            "event_verification_level": "official",
            "event_last_updated_at": (
                primary["updated_at"].isoformat()
                if primary.get("updated_at")
                else ""
            ),
            "event_notes": (
                (
                    "Dideduplikasi dari beberapa feed BMKG: "
                    + ", ".join(sorted({item["source_id"] for item in items}))
                    if len(items) > 1
                    else "Rekaman resmi BMKG; bukan sumber independen."
                )
                if primary["source_id"] != "usgs_m45"
                else "Rekaman resmi USGS; sumber internasional pendukung, "
                "bukan sumber resmi Indonesia."
            ),
        }
    )
    time_row = empty_row(dictionary["event_time"])
    time_row.update(
        {
            "event_time_id": "TIME-" + sha256_text(event_id)[:12].upper(),
            "event_id": event_id,
            "event_time": primary["event_time"].isoformat(),
            "event_time_precision": "second",
            "event_time_kind": "actual",
            "event_time_status": "extracted",
            "event_time_basis": "official_field",
            "event_time_evidence": primary["event_time_evidence"],
            "event_time_timezone": "Etc/UTC",
            "event_time_confidence": "high",
        }
    )
    location_row = empty_row(dictionary["event_location"])
    scope = geo.classify_location(
        location_name=primary["location_name"],
        latitude=primary["lat"],
        longitude=primary["lon"],
        coordinate_status="source_coordinate",
        source_id=primary["source_id"],
        event_title=primary["title"],
    )
    scope_note = (
        "Perlu verifikasi batas wilayah untuk geographic scope; bbox pilot "
        "bukan batas nasional."
        if scope["geographic_scope"] == geo.UNKNOWN
        else (
            "Geographic scope luar Indonesia berdasarkan penanda wilayah "
            "asing dan koordinat di luar bbox pilot; batas nasional belum "
            "diverifikasi."
            if scope["geographic_scope"] == geo.OUTSIDE_INDONESIA
            else (
                "Geographic scope Indonesia berdasarkan toponimi resmi dan "
                "koordinat di dalam bbox pilot; koordinat sumber belum "
                "diverifikasi."
            )
        )
    )
    location_row.update(
        {
            "event_location_id": "LOCE-" + sha256_text(event_id)[:12].upper(),
            "event_id": event_id,
            "location_name": primary["location_name"],
            "location_role": "epicenter",
            "latitude": f"{primary['lat']:.4f}",
            "longitude": f"{primary['lon']:.4f}",
            "coordinate_source": "source_api",
            "coordinate_status": "source_coordinate",
            "coordinate_precision": "point",
            "coordinate_confidence": "high",
            "is_inside_indonesia": scope["is_inside_indonesia"],
            "location_evidence": (
                f"{primary['source_id']} field lokasi/koordinat; "
                f"{primary['event_time_evidence']}; "
                f"geographic_scope={scope['geographic_scope']}; "
                f"scope_basis={scope['scope_basis']}"
            ),
            "location_notes": (
                "Koordinat berasal dari field sumber; belum diverifikasi "
                f"manual. {scope_note}"
            ),
        }
    )
    category_row = empty_row(dictionary["category"])
    category_row.update(
        {
            "category_assignment_id": (
                "CAT-" + sha256_text(event_id)[:12].upper()
            ),
            "event_id": event_id,
            "category_name": "Gempabumi",
            "category_rank": "primary",
            "category_scope": "in_scope",
            "category_basis": "official_metadata",
            "category_confidence": "high",
            "category_review_status": "not_reviewed",
            "category_original": primary["category_original"],
            "category_notes": (
                "Kategori dari jenis feed gempa resmi; tsunami tetap atribut "
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


def build_link(item, event_id, is_primary, dictionary):
    link = empty_row(dictionary["document_event_link"])
    link.update(
        {
            "link_id": "LINK-"
            + sha256_text(f"{item['document_id']}|{event_id}")[:12].upper(),
            "document_id": item["document_id"],
            "event_id": event_id,
            "relation_type": "reports",
            "relation_direction": "document_to_event",
            "relevance": "primary" if is_primary == "ya" else "supporting",
            "is_primary": is_primary,
            "relation_confidence": "high",
            "relation_evidence": (
                f"Record feed {item['source_id']} memuat parameter kejadian."
            ),
            "event_count_mentioned": "1",
            "link_status": "active",
            "link_created_at": item["retrieved_at"],
            "link_created_by": "system_pilot_collector",
        }
    )
    return link


def build_assertions(item, event_id, dictionary):
    values = [
        ("event_time", item["event_time"].isoformat(), item["event_time_evidence"]),
        ("latitude", f"{item['lat']:.4f}", "Field koordinat sumber"),
        ("longitude", f"{item['lon']:.4f}", "Field koordinat sumber"),
        ("location_name", item["location_name"], "Field lokasi sumber"),
        ("category", "Gempabumi", "Jenis record feed gempa"),
        ("magnitude", item["magnitude_text"], "Field magnitudo sumber"),
        ("depth", item["depth_text"], "Field kedalaman sumber"),
    ]
    rows = []
    for field_name, value, evidence in values:
        if not value:
            continue
        row = empty_row(dictionary["event_assertion"])
        row.update(
            {
                "assertion_id": "AST-"
                + sha256_text(
                    f"{event_id}|{field_name}|{item['source_id']}"
                )[:16].upper(),
                "event_id": event_id,
                "document_id": item["document_id"],
                "source_id": item["source_id"],
                "field_name": field_name,
                "asserted_value": str(value),
                "assertion_status": "accepted",
                "assertion_confidence": "high",
                "assertion_evidence": evidence,
                "asserted_at": item["retrieved_at"],
                "assertion_notes": (
                    "Nilai dari dokumen primer event; belum direview manual."
                ),
            }
        )
        rows.append(row)
    return rows


def classify_tsunami_potential(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    if not text or not re.search(r"\btsunami\b", text):
        return "unknown"
    if any(re.search(pattern, text) for pattern in TSUNAMI_UNKNOWN_PATTERNS):
        return "unknown"
    if any(re.search(pattern, text) for pattern in TSUNAMI_NEGATIVE_PATTERNS):
        return "negative"
    if any(re.search(pattern, text) for pattern in TSUNAMI_POSITIVE_PATTERNS):
        return "positive"
    return "unknown"


def tsunami_potential_specs(value):
    raw_text = str(value or "")
    text = raw_text.strip()
    status = classify_tsunami_potential(text)
    specs = []
    if text:
        specs.append(
            (
                "bmkg_potential_text",
                raw_text,
                "",
                "Nilai mentah field Potensi BMKG; bukan event tsunami terpisah.",
                "high",
            )
        )
    if status in {"positive", "negative"}:
        confidence = "high"
        notes = (
            "Status tiga keadaan dari field Potensi BMKG; nilai mentah "
            "dipertahankan di bmkg_potential_text; bukan event tsunami terpisah."
        )
    elif text:
        confidence = "low"
        notes = (
            "Field Potensi BMKG tidak menyatakan status tsunami secara eksplisit; "
            "nilai mentah dipertahankan di bmkg_potential_text; bukan event tsunami."
        )
    else:
        confidence = "unknown"
        notes = (
            "Sumber tidak menyatakan potensi tsunami secara eksplisit; status "
            "unknown; bukan event tsunami terpisah."
        )
    specs.append(
        ("tsunami_potential_status", status, "", notes, confidence)
    )
    return specs


def build_attribute_row(dictionary, event_id, source_id, spec):
    name, value, unit, notes, confidence = spec
    if not value:
        return None
    row = empty_row(dictionary["event_attribute"])
    row.update(
        {
            "event_attribute_id": "EATTR-"
            + sha256_text(f"{event_id}|{name}")[:16].upper(),
            "event_id": event_id,
            "attribute_name": name,
            "attribute_value": str(value),
            "attribute_unit": unit,
            "attribute_source_id": source_id,
            "attribute_confidence": confidence,
            "attribute_notes": notes,
        }
    )
    return row


def build_attributes(item, event_id, dictionary):
    specs = [
        (
            "magnitude",
            item["magnitude_text"],
            "M",
            "Field magnitudo sumber.",
            "high",
        ),
    ]
    depth_match = re.search(
        r"(-?\d+(?:[.,]\d+)?)\s*(km|mi)\b", item["depth_text"], re.IGNORECASE
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
    elif item["depth_text"]:
        specs.append(
            (
                "depth",
                item["depth_text"],
                "",
                "Field kedalaman sumber.",
                "high",
            )
        )
    extra = item.get("extra", {})
    specs.extend(tsunami_potential_specs(extra.get("potensi", "")))
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
            (
                "shakemap_file",
                extra["shakemap"],
                "",
                "Field Shakemap BMKG.",
                "high",
            )
        )
    rows = []
    for spec in specs:
        row = build_attribute_row(
            dictionary, event_id, item["source_id"], spec
        )
        if row is not None:
            rows.append(row)
    return rows


def build_verification(event, primary, dictionary):
    row = empty_row(dictionary["verification"])
    row.update(
        {
            "verification_id": (
                "VER-" + sha256_text(event["event_id"])[:12].upper()
            ),
            "target_type": "event",
            "target_id": event["event_id"],
            "verification_status": "official",
            "verification_level": "official",
            "verification_basis": (
                "Rekaman resmi feed BMKG."
                if primary["source_id"] != "usgs_m45"
                else "Rekaman resmi feed USGS; sumber internasional pendukung."
            ),
            "verification_source_count": "1",
            "verification_method": "official_record",
            "verification_notes": (
                "Verifikasi otomatis terhadap rekaman resmi; belum ada review manual."
            ),
        }
    )
    return row


def build_change_logs(tables, fields, changed_at):
    rows = []
    for entity in ENTITY_ORDER:
        if entity == "change_log":
            continue
        key = KEY_FIELDS[entity]
        for target in tables[entity]:
            target_id = target[key]
            row = empty_row(fields["change_log"])
            row.update(
                {
                    "change_id": "CHG-"
                    + sha256_text(f"{entity}|{target_id}")[:16].upper(),
                    "target_type": entity,
                    "target_id": target_id,
                    "change_type": "create",
                    "changed_at": changed_at,
                    "changed_by": "system_pilot_collector",
                    "change_reason": (
                        "Pembuatan record pilot dari sumber resmi aktif."
                    ),
                    "schema_version": SCHEMA_VERSION,
                    "manual_review": "tidak",
                }
            )
            rows.append(row)
    return rows


def validate(tables, register, run_dir):
    results = []

    def add(rule_id, severity, entity, checked, failures, note=""):
        if failures:
            if severity == "P0":
                status = "gagal"
            elif severity == "P1":
                status = "perlu_review"
            else:
                status = "lulus_dengan_catatan"
            detail = f"{len(failures)} pelanggaran; contoh: " + " | ".join(
                failures[:5]
            )
        else:
            status = "lulus"
            detail = note or f"{checked} record diperiksa; tidak ada pelanggaran."
        results.append(
            {
                "rule_id": rule_id,
                "severity": severity,
                "entity": entity,
                "records_checked": checked,
                "status": status,
                "detail": detail,
                "record_refs": " | ".join(failures[:10]),
            }
        )

    sources = tables["source"]
    source_ids = [row["source_id"] for row in sources]
    failures = [
        sid for sid in source_ids if sid not in register or source_ids.count(sid) > 1
    ]
    add("R-SRC-01", "P0", "source", len(sources), failures)
    failures = [
        f"{row['source_id']}: tidak berasal dari register"
        for row in sources
        if not row["source_id"] or row["source_id"] not in register
    ]
    add("R-SRC-02", "P0", "source", len(sources), failures)
    failures = [
        f"{row['source_id']}: {row['source_registry_status']}"
        for row in sources
        if row["source_registry_status"]
        in {"PERLU_IZIN", "BELUM_TERSEDIA", "TIDAK_SESUAI"}
    ]
    add("R-SRC-03", "P0", "source", len(sources), failures)
    failures = [
        f"{row['source_id']}: tipe/peran/data_type tidak konsisten"
        for row in sources
        if row["source_type"] != "official"
        or row["source_data_type"] != "event_feed"
        or (
            row["source_role"] == "primary_official"
            and row["source_type"] != "official"
        )
    ]
    add("R-SRC-04", "P1", "source", len(sources), failures)
    failures = [
        f"{row['source_id']}: klaim lisensi/robots tidak sah"
        for row in sources
        if (row["source_license_status"] == "verified" and not row["source_license"])
        or row["source_robots_status"] == "disallowed"
    ]
    add(
        "R-SRC-05",
        "P0",
        "source",
        len(sources),
        failures,
        "Lisensi belum diverifikasi; robots BMKG tidak terbaca dan tidak dianggap izin.",
    )

    raw_rows = tables["raw_payload"]
    failures = []
    for row in raw_rows:
        if not all(
            [
                row["raw_payload_id"],
                row["raw_payload_source_id"],
                row["raw_payload_url"],
                row["raw_payload_retrieved_at"],
            ]
        ):
            failures.append(f"{row['raw_payload_id']}: metadata wajib kosong")
        if row["raw_payload_source_id"] not in register:
            failures.append(f"{row['raw_payload_id']}: source tidak terdaftar")
    add("R-RAW-01", "P0", "raw_payload", len(raw_rows), failures)
    failures = []
    for row in raw_rows:
        digest = row["raw_payload_sha256"]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            failures.append(f"{row['raw_payload_id']}: hash tidak sah")
            continue
        path = ROOT / row["raw_payload_path"]
        if not path.is_file():
            failures.append(f"{row['raw_payload_id']}: file tidak ada")
        elif sha256_file(path) != digest:
            failures.append(f"{row['raw_payload_id']}: hash file tidak cocok")
    add("R-RAW-02", "P0", "raw_payload", len(raw_rows), failures)
    failures = [
        f"{row['raw_payload_id']}: retrieved_at bukan ISO"
        for row in raw_rows
        if parse_iso(row["raw_payload_retrieved_at"]) is None
    ]
    add("R-RAW-03", "P1", "raw_payload", len(raw_rows), failures)
    failures = [
        f"{row['raw_payload_id']}: stored tanpa file"
        for row in raw_rows
        if row["raw_payload_status"] == "stored"
        and not (ROOT / row["raw_payload_path"]).is_file()
    ]
    add("R-RAW-04", "P1", "raw_payload", len(raw_rows), failures)

    documents = tables["document"]
    doc_ids = [row["document_id"] for row in documents]
    add(
        "R-DOC-01",
        "P0",
        "document",
        len(documents),
        [doc_id for doc_id in doc_ids if doc_ids.count(doc_id) > 1],
    )
    failures = [
        f"{row['document_id']}: judul/URL kosong"
        for row in documents
        if not row["document_title"]
        or (not row["document_url"] and not row["document_external_id"])
    ]
    add("R-DOC-02", "P1", "document", len(documents), failures)
    failures = []
    for row in documents:
        if row["document_source_id"] not in register:
            failures.append(f"{row['document_id']}: source tidak valid")
        if row["document_source_identity_status"] != "registered":
            failures.append(f"{row['document_id']}: identitas sumber bukan registered")
        if row["document_source_type"] != "official":
            failures.append(f"{row['document_id']}: tipe bukan official")
    add("R-DOC-03", "P0", "document", len(documents), failures)
    failures = []
    for row in documents:
        if row["document_provenance_status"] == "complete":
            required = [
                row["document_source_id"],
                row["document_raw_payload_id"],
                row["document_run_id"],
                row["document_retrieved_at"],
            ]
            if not all(required):
                failures.append(f"{row['document_id']}: provenance tidak lengkap")
    add("R-DOC-04", "P1", "document", len(documents), failures)

    events = tables["event"]
    event_ids = [row["event_id"] for row in events]
    add(
        "R-EVT-01",
        "P0",
        "event",
        len(events),
        [event_id for event_id in event_ids if event_ids.count(event_id) > 1],
    )
    failures = [
        f"{row['event_id']}: source/judul tidak valid"
        for row in events
        if row["event_primary_source_id"] not in register
        or not row["event_title"]
    ]
    add("R-EVT-02", "P1", "event", len(events), failures)
    failures = [
        f"{row['event_id']}: confirmed tanpa dasar resmi"
        for row in events
        if row["event_status"] == "confirmed"
        and row["event_verification_status"] not in {"official", "corroborated"}
    ]
    add("R-EVT-03", "P0", "event", len(events), failures)
    failures = [
        f"{row['event_id']}: official dari sumber tidak resmi"
        for row in events
        if row["event_verification_status"] == "official"
        and row["event_primary_source_id"]
        not in {
            "bmkg_autogempa",
            "bmkg_gempa_terkini",
            "bmkg_gempa_dirasakan",
            "usgs_m45",
        }
    ]
    add(
        "R-EVT-04",
        "P1",
        "event",
        len(events),
        failures,
        "Official USGS dicatat sebagai rekaman resmi ilmiah internasional.",
    )
    attribute_values = defaultdict(set)
    raw_text_by_event = {}
    status_rows_by_event = defaultdict(list)
    failures = []
    for row in tables["event_attribute"]:
        attribute_values[(row["event_id"], row["attribute_name"])].add(
            row["attribute_value"]
        )
        if not row["attribute_source_id"]:
            failures.append(
                f"{row['event_attribute_id']}: atribut tanpa sumber"
            )
        if row["attribute_name"] == "tsunami_potential":
            failures.append(
                f"{row['event_attribute_id']}: tsunami_potential ambigu; "
                "gunakan bmkg_potential_text dan tsunami_potential_status"
            )
        elif row["attribute_name"] == "bmkg_potential_text":
            raw_text_by_event[row["event_id"]] = row["attribute_value"]
        elif row["attribute_name"] == "tsunami_potential_status":
            status_rows_by_event[row["event_id"]].append(row)
    failures.extend(
        f"{event_id}|{name}: nilai ganda tanpa resolusi"
        for (event_id, name), values in attribute_values.items()
        if len(values) > 1
    )
    for event_id, rows in status_rows_by_event.items():
        if len(rows) > 1:
            failures.append(
                f"{event_id}: tsunami_potential_status lebih dari satu"
            )
        expected = classify_tsunami_potential(
            raw_text_by_event.get(event_id, "")
        )
        for row in rows:
            status = row["attribute_value"]
            if status not in TSUNAMI_POTENTIAL_VALUES:
                failures.append(
                    f"{row['event_attribute_id']}: status tsunami tidak valid"
                )
            elif status != expected:
                failures.append(
                    f"{row['event_attribute_id']}: status tsunami tidak sesuai "
                    "nilai mentah"
                )
            if status in {"positive", "negative"} and event_id not in (
                raw_text_by_event
            ):
                failures.append(
                    f"{row['event_attribute_id']}: status eksplisit tanpa "
                    "nilai mentah"
                )
    for event_id in raw_text_by_event:
        if event_id not in status_rows_by_event:
            failures.append(
                f"{event_id}: bmkg_potential_text tanpa "
                "tsunami_potential_status"
            )
    add(
        "R-EVT-05",
        "P1",
        "event_attribute",
        len(tables["event_attribute"]),
        failures,
    )

    times = tables["event_time"]
    failures = [
        f"{row['event_time_id']}: basis/bukti kosong"
        for row in times
        if row["event_time"]
        and (not row["event_time_basis"] or not row["event_time_evidence"])
    ]
    add("R-TIME-01", "P0", "event_time", len(times), failures)
    failures = [
        f"{row['event_time_id']}: basis/status tidak sesuai"
        for row in times
        if (
            row["event_time"]
            and row["event_time_basis"]
            not in {"official_field", "official_document"}
        )
        or (
            not row["event_time"]
            and row["event_time_status"]
            not in {"unknown", "not_applicable", "manual_review"}
        )
    ]
    add("R-TIME-02", "P0", "event_time", len(times), failures)
    failures = []
    for row in times:
        parsed = parse_iso(row["event_time"])
        if parsed is None:
            failures.append(f"{row['event_time_id']}: waktu bukan ISO")
            continue
        if row["event_time_precision"] in {"second", "minute", "hour"} and not row[
            "event_time_timezone"
        ]:
            failures.append(f"{row['event_time_id']}: zona waktu kosong")
    add("R-TIME-03", "P1", "event_time", len(times), failures)
    failures = [
        f"{row['event_time_id']}: {row['event_time_kind']} diperlakukan actual"
        for row in times
        if row["event_time_kind"] in {"nowcast", "forecast", "estimated"}
        and row["event_time_status"] == "actual"
    ]
    add("R-TIME-04", "P1", "event_time", len(times), failures)
    failures = [
        f"{row['event_time_id']}: kandidat tidak manual_review"
        for row in times
        if row.get("event_time_candidate_text")
        and row["event_time_status"] != "manual_review"
    ]
    add("R-TIME-05", "P1", "event_time", len(times), failures)
    failures = []
    for row in times:
        zone = row["event_time_timezone"]
        if not zone:
            continue
        try:
            ZoneInfo(zone)
        except Exception:
            failures.append(
                f"{row['event_time_id']}: zona bukan IANA ({zone})"
            )
    add("R-TIME-06", "P2", "event_time", len(times), failures)

    locations = tables["event_location"]
    failures = []
    for row in locations:
        if bool(row["latitude"]) != bool(row["longitude"]):
            failures.append(f"{row['event_location_id']}: lat/lon tidak lengkap")
            continue
        if row["latitude"]:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                failures.append(f"{row['event_location_id']}: koordinat luar rentang")
    add("R-LOC-01", "P0", "event_location", len(locations), failures)
    failures = []
    for row in locations:
        if row["latitude"] and row["longitude"]:
            if not all(
                [
                    row["coordinate_source"],
                    row["coordinate_status"],
                    row["coordinate_precision"],
                    row["coordinate_confidence"],
                ]
            ):
                failures.append(f"{row['event_location_id']}: metadata kosong")
            if row["coordinate_status"] not in {
                "source_coordinate",
                "reported_coordinate",
                "approximate",
                "verified",
                "unknown",
            }:
                failures.append(f"{row['event_location_id']}: status tidak dikenal")
            if row["coordinate_status"] == "verified" and (
                not row["coordinate_verified_at"]
                or not row["coordinate_verified_by"]
            ):
                failures.append(
                    f"{row['event_location_id']}: verified tanpa bukti"
                )
    add("R-LOC-02", "P0", "event_location", len(locations), failures)
    mentions = tables["location_mention"]
    failures = [
        f"{row['location_mention_id']}: dokumen/teks tidak valid"
        for row in mentions
        if row["document_id"] not in doc_ids or not row["mention_text"]
    ]
    add("R-LOC-03", "P1", "location_mention", len(mentions), failures)
    failures = [
        f"{row['location_mention_id']}: role/status/bukti tidak konsisten"
        for row in mentions
        if not row["mention_role"]
        or row["mention_status"]
        not in {
            "normalized",
            "verified",
            "manual_review",
            "ambiguous",
            "rejected",
        }
        or not row["mention_evidence"]
    ]
    add("R-LOC-04", "P1", "location_mention", len(mentions), failures)
    failures = []
    event_by_id = {row["event_id"]: row for row in tables["event"]}
    for row in locations:
        event = event_by_id.get(row["event_id"], {})
        scope = geo.classify_location(
            location_name=row["location_name"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            coordinate_status=row["coordinate_status"],
            source_id=event.get("event_primary_source_id", ""),
            event_title=event.get("event_title", ""),
        )
        if row["is_inside_indonesia"] != scope["is_inside_indonesia"]:
            failures.append(
                f"{row['event_location_id']}: geographic scope tidak "
                f"sesuai bukti ({scope['scope_basis']})"
            )
    add("R-LOC-05", "P1", "event_location", len(locations), failures)
    failures = [
        f"{row['event_location_id']}: source_coordinate ditandai verified"
        for row in locations
        if row["coordinate_status"] != "verified"
        and row["coordinate_verified_at"]
    ]
    add("R-LOC-06", "P1", "event_location", len(locations), failures)
    failures = [
        f"{row['event_location_id']}: verified tanpa bukti"
        for row in locations
        if row["coordinate_status"] == "verified"
        and (not row["coordinate_verified_at"] or not row["coordinate_verified_by"])
    ]
    add("R-LOC-07", "P0", "event_location", len(locations), failures)

    categories = tables["category"]
    failures = [
        f"{row['category_assignment_id']}: kategori/event tidak valid"
        for row in categories
        if row["category_name"] not in ALLOWED_CATEGORIES
        or row["event_id"] not in event_ids
    ]
    for event_id in event_ids:
        primaries = [
            row
            for row in categories
            if row["event_id"] == event_id and row["category_rank"] == "primary"
        ]
        if len(primaries) != 1:
            failures.append(f"{event_id}: kategori primary {len(primaries)}")
    add("R-CAT-01", "P0", "category", len(categories), failures)
    failures = [
        f"{row['category_assignment_id']}: scope tidak konsisten"
        for row in categories
        if row["category_name"] != "Lainnya"
        and row["category_scope"] != "in_scope"
    ]
    add("R-CAT-02", "P0", "category", len(categories), failures)
    failures = [
        f"{row['category_assignment_id']}: basis/original kosong"
        for row in categories
        if not row["category_basis"] or not row["category_original"]
    ]
    add("R-CAT-03", "P1", "category", len(categories), failures)
    failures = [
        f"{row['category_assignment_id']}: review changed tanpa jejak"
        for row in categories
        if row["category_review_status"] == "changed"
        and (
            not row["category_reviewed_by"]
            or not row["category_reviewed_at"]
            or not row["category_notes"]
        )
    ]
    add("R-CAT-04", "P1", "category", len(categories), failures)

    links = tables["document_event_link"]
    link_ids = [row["link_id"] for row in links]
    failures = [
        f"{link_id}: link_id duplikat"
        for link_id in link_ids
        if link_ids.count(link_id) > 1
    ]
    for row in links:
        if row["document_id"] not in doc_ids or row["event_id"] not in event_ids:
            failures.append(f"{row['link_id']}: FK tidak valid")
    add("R-LINK-01", "P0", "document_event_link", len(links), failures)
    primary_by_event = Counter(
        row["event_id"] for row in links if row["is_primary"] == "ya"
    )
    failures = [
        f"{event_id}: primary {count}"
        for event_id, count in primary_by_event.items()
        if count > 1
    ]
    add("R-LINK-02", "P1", "document_event_link", len(links), failures)
    failures = []
    for row in links:
        try:
            if int(row["event_count_mentioned"]) < 1:
                failures.append(f"{row['link_id']}: event_count < 1")
        except ValueError:
            failures.append(f"{row['link_id']}: event_count bukan integer")
    add("R-LINK-03", "P1", "document_event_link", len(links), failures)
    failures = [
        f"{row['link_id']}: relasi nonaktif dijadikan bukti"
        for row in links
        if row["link_status"] in {"superseded", "rejected", "inactive"}
        and row["is_primary"] == "ya"
    ]
    add("R-LINK-04", "P1", "document_event_link", len(links), failures)
    duplicate_keys = Counter(
        (row["document_id"], row["event_id"], row["relation_type"]) for row in links
    )
    failures = [
        str(key) for key, count in duplicate_keys.items() if count > 1
    ]
    add("R-LINK-05", "P2", "document_event_link", len(links), failures)

    assertions = tables["event_assertion"]
    assertion_ids = [row["assertion_id"] for row in assertions]
    failures = [
        f"{assertion_id}: assertion_id duplikat"
        for assertion_id in assertion_ids
        if assertion_ids.count(assertion_id) > 1
    ]
    failures.extend(
        f"{row['assertion_id']}: event/field tidak valid"
        for row in assertions
        if row["event_id"] not in event_ids
        or row["field_name"]
        not in {
            "event_time",
            "latitude",
            "longitude",
            "location_name",
            "category",
            "magnitude",
            "depth",
            "event_status",
            "other",
        }
    )
    add("R-AST-01", "P0", "event_assertion", len(assertions), failures)
    failures = [
        f"{row['assertion_id']}: nilai/bukti kosong"
        for row in assertions
        if not row["asserted_value"] or not row["assertion_evidence"]
    ]
    add("R-AST-02", "P1", "event_assertion", len(assertions), failures)
    accepted = defaultdict(set)
    for row in assertions:
        if row["assertion_status"] == "accepted":
            accepted[(row["event_id"], row["field_name"])].add(
                row["asserted_value"]
            )
    failures = [
        f"{event}|{field}: nilai ganda"
        for (event, field), values in accepted.items()
        if len(values) > 1
        and field in {"event_time", "latitude", "longitude", "category"}
    ]
    add("R-AST-03", "P1", "event_assertion", len(assertions), failures)

    verifications = tables["verification"]
    event_source = {
        row["event_id"]: row["event_primary_source_id"] for row in events
    }
    failures = [
        f"{row['verification_id']}: target/metadata tidak valid"
        for row in verifications
        if row["target_type"] != "event"
        or row["target_id"] not in event_ids
        or not all(
            [
                row["verification_status"],
                row["verification_level"],
                row["verification_method"],
                row["verification_basis"],
            ]
        )
    ]
    add("R-VER-01", "P0", "verification", len(verifications), failures)
    failures = [
        f"{row['verification_id']}: official tanpa sumber resmi"
        for row in verifications
        if row["verification_status"] == "official"
        and event_source.get(row["target_id"])
        not in {
            "bmkg_autogempa",
            "bmkg_gempa_terkini",
            "bmkg_gempa_dirasakan",
            "usgs_m45",
        }
    ]
    add("R-VER-02", "P1", "verification", len(verifications), failures)
    failures = [
        f"{row['verification_id']}: corroborated < 2 sumber"
        for row in verifications
        if row["verification_status"] == "corroborated"
        and int(row["verification_source_count"]) < 2
    ]
    add("R-VER-03", "P1", "verification", len(verifications), failures)
    failures = [
        f"{row['verification_id']}: manual/reject tanpa jejak"
        for row in verifications
        if row["verification_status"]
        in {"manual_verified", "rejected", "retracted"}
        and (
            not row["verified_at"]
            or not row["verified_by"]
            or (
                row["verification_status"] in {"rejected", "retracted"}
                and not row["verification_notes"]
            )
        )
    ]
    add("R-VER-04", "P1", "verification", len(verifications), failures)

    changes = tables["change_log"]
    change_ids = [row["change_id"] for row in changes]
    failures = [
        f"{change_id}: change_id duplikat"
        for change_id in change_ids
        if change_ids.count(change_id) > 1
    ]
    failures.extend(
        f"{row['change_id']}: metadata wajib kosong"
        for row in changes
        if not all(
            [
                row["target_type"],
                row["target_id"],
                row["change_type"],
                row["changed_at"],
                row["changed_by"],
                row["change_reason"],
                row["schema_version"],
            ]
        )
    )
    add("R-CHG-01", "P0", "change_log", len(changes), failures)
    failures = [
        f"{row['change_id']}: create memuat nilai lama/baru"
        for row in changes
        if row["change_type"] == "create"
        and (row["old_value"] or row["new_value"])
    ]
    add("R-CHG-02", "P1", "change_log", len(changes), failures)
    failures = [
        f"{row['change_id']}: manual_review tidak sah"
        for row in changes
        if row["manual_review"] not in {"ya", "tidak"}
    ]
    create_targets = Counter(
        (row["target_type"], row["target_id"])
        for row in changes
        if row["change_type"] == "create"
    )
    failures.extend(
        f"{target}: create ganda tanpa jejak"
        for target, count in create_targets.items()
        if count > 1
    )
    add("R-CHG-03", "P0", "change_log", len(changes), failures)

    failures = []
    usgs_native = [
        row["event_source_native_id"]
        for row in events
        if row["event_source_native_id"]
    ]
    for native_id in set(usgs_native):
        if usgs_native.count(native_id) > 1:
            failures.append(f"native_id ganda: {native_id}")
    add("R-DUP-02", "P1", "event", len(events), failures)

    not_evaluated = [
        ("R-LEG-01", "legacy", "Tidak ada record legacy pada pilot."),
        ("R-LEG-02", "legacy", "Tidak ada record legacy pada pilot."),
        ("R-LEG-03", "legacy", "Tidak ada record legacy pada pilot."),
        ("R-LEG-04", "legacy", "Tidak ada record legacy pada pilot."),
        ("R-REL-01", "event_relation", "Tidak ada relasi event pada pilot."),
        ("R-REL-02", "event_relation", "Tidak ada relasi event pada pilot."),
        ("R-REL-03", "event_relation", "Tidak ada relasi event pada pilot."),
        ("R-DUP-01", "document", "Tidak ada URL kanonik duplikat pada pilot."),
    ]
    for rule_id, entity, reason in not_evaluated:
        results.append(
            {
                "rule_id": rule_id,
                "severity": "",
                "entity": entity,
                "records_checked": 0,
                "status": "tidak_dievaluasi",
                "detail": reason,
                "record_refs": "",
            }
        )
    return results


def quality_gates(validation_rows, baseline_after, sources):
    by_rule = {row["rule_id"]: row for row in validation_rows}

    def make_gate(gate_id, title, rule_ids, note):
        failed = [
            rule_id
            for rule_id in rule_ids
            if by_rule.get(rule_id, {}).get("status") == "gagal"
        ]
        review = [
            rule_id
            for rule_id in rule_ids
            if by_rule.get(rule_id, {}).get("status") == "perlu_review"
        ]
        if failed:
            status = "gagal"
        elif review:
            status = "lulus_dengan_catatan"
        else:
            status = "lulus"
        return {
            "gate_id": gate_id,
            "gate": title,
            "status": status,
            "rules_checked": ";".join(rule_ids),
            "notes": note,
            "failed_rules": ";".join(failed),
            "review_rules": ";".join(review),
        }

    gates = [
        make_gate(
            "G0",
            "Baseline",
            [],
            (
                "Baseline hash dan ukuran tidak berubah."
                if baseline_after["sha256"] == dataset_baseline.DATASET_SHA256
                else "Baseline berubah."
            ),
        ),
        make_gate(
            "G1",
            "Sumber",
            ["R-SRC-01", "R-SRC-02", "R-SRC-03", "R-SRC-04", "R-SRC-05"],
            "Hanya sumber resmi aktif; lisensi belum diverifikasi.",
        ),
        make_gate(
            "G2",
            "Payload",
            ["R-RAW-01", "R-RAW-02", "R-RAW-03", "R-RAW-04"],
            "Payload mentah tersimpan dengan hash dan run.",
        ),
        make_gate(
            "G3",
            "Dokumen",
            ["R-DOC-01", "R-DOC-02", "R-DOC-03", "R-DOC-04"],
            "Dokumen memakai ID stabil dan sumber terdaftar.",
        ),
        make_gate(
            "G4",
            "Kejadian",
            ["R-EVT-01", "R-EVT-02", "R-EVT-03", "R-EVT-04", "R-EVT-05"],
            "Event terpisah dari dokumen; duplikat lintas sumber belum digabung.",
        ),
        make_gate(
            "G5",
            "Waktu",
            [
                "R-TIME-01",
                "R-TIME-02",
                "R-TIME-03",
                "R-TIME-04",
                "R-TIME-05",
                "R-TIME-06",
            ],
            "Waktu berasal dari field resmi, bukan published_at.",
        ),
        make_gate(
            "G6",
            "Lokasi",
            [
                "R-LOC-01",
                "R-LOC-02",
                "R-LOC-03",
                "R-LOC-04",
                "R-LOC-05",
                "R-LOC-06",
                "R-LOC-07",
            ],
            "Koordinat berstatus source_coordinate, bukan verified.",
        ),
        make_gate(
            "G7",
            "Kategori",
            ["R-CAT-01", "R-CAT-02", "R-CAT-03", "R-CAT-04"],
            "Hanya Gempabumi yang tercakup pada pilot.",
        ),
        make_gate(
            "G8",
            "Klaim dan verifikasi",
            [
                "R-AST-01",
                "R-AST-02",
                "R-AST-03",
                "R-VER-01",
                "R-VER-02",
                "R-VER-03",
                "R-VER-04",
            ],
            "Klaim dan verifikasi mengikuti rekaman resmi.",
        ),
        make_gate(
            "G9",
            "Legacy dan deduplikasi",
            [
                "R-LINK-01",
                "R-LINK-02",
                "R-LINK-03",
                "R-LINK-04",
                "R-DUP-02",
                "R-CHG-03",
            ],
            "Tidak ada data legacy; duplikat lintas sumber hanya ditandai.",
        ),
    ]
    if baseline_after["sha256"] != dataset_baseline.DATASET_SHA256:
        gates[0]["status"] = "gagal"
    if any(row["source_license_status"] != "verified" for row in sources):
        gate = gates[1]
        if gate["status"] == "lulus":
            gate["status"] = "lulus_dengan_catatan"
        gate["notes"] += " Lisensi/izin redistribusi belum diverifikasi."
    gates.append(
        {
            "gate_id": "G10",
            "gate": "Rilis",
            "status": "tidak_dievaluasi",
            "rules_checked": "",
            "notes": "Pilot internal, bukan rilis; belum ada persetujuan editorial.",
            "failed_rules": "",
            "review_rules": "",
        }
    )
    return gates


def duplicate_candidates(events, locations, times):
    location_by_event = {row["event_id"]: row for row in locations}
    time_by_event = {row["event_id"]: row for row in times}
    bmkg = [
        row for row in events if row["event_primary_source_id"].startswith("bmkg_")
    ]
    usgs = [row for row in events if row["event_primary_source_id"] == "usgs_m45"]
    rows = []
    for left in bmkg:
        left_loc = location_by_event[left["event_id"]]
        left_time = time_by_event[left["event_id"]]
        for right in usgs:
            right_loc = location_by_event[right["event_id"]]
            right_time = time_by_event[right["event_id"]]
            distance = haversine_km(
                float(left_loc["latitude"]),
                float(left_loc["longitude"]),
                float(right_loc["latitude"]),
                float(right_loc["longitude"]),
            )
            time_diff = abs(
                (
                    parse_iso(left_time["event_time"])
                    - parse_iso(right_time["event_time"])
                ).total_seconds()
            )
            if distance <= 150 and time_diff <= 300:
                rows.append(
                    {
                        "bmkg_event_id": left["event_id"],
                        "usgs_event_id": right["event_id"],
                        "bmkg_source_id": left["event_primary_source_id"],
                        "time_diff_seconds": f"{time_diff:.0f}",
                        "distance_km": f"{distance:.1f}",
                        "bmkg_title": left["event_title"],
                        "usgs_title": right["event_title"],
                        "recommended_action": "review_manual_tidak_digabung",
                        "reason": (
                            "Waktu dan lokasi berdekatan; event tetap dipisah "
                            "sampai review manual."
                        ),
                    }
                )
    return rows


def category_gap_rows(event_count):
    rows = [
        (
            "Gempabumi",
            "tercakup_pilot",
            event_count,
            "bmkg_autogempa; bmkg_gempa_terkini; bmkg_gempa_dirasakan; usgs_m45",
            "TERVERIFIKASI_AKTIF",
            "Feed resmi aktif dan berhasil dinormalisasi.",
            "Perluas snapshot dan review duplikat lintas sumber.",
        ),
        (
            "Tsunami",
            "atribut_potensi_saja",
            0,
            "bmkg_autogempa; bmkg_gempa_terkini",
            "TERVERIFIKASI_AKTIF",
            "Tidak ada feed kejadian tsunami mandiri; Potensi BMKG bukan event terpisah.",
            "Cari feed peringatan tsunami resmi sebelum menambah event.",
        ),
        (
            "Gunungapi",
            "tidak_tercakup_pilot",
            0,
            "pvmbg_*; magma_*",
            "PERLU_IZIN",
            "Sumber resmi memerlukan izin tertulis; robots melarang akses.",
            "Selesaikan izin dan lisensi PVMBG/Badan Geologi.",
        ),
        (
            "Gerakan Tanah/Tanah Longsor",
            "tidak_tercakup_pilot",
            0,
            "portalmbg_field_reports; bnpb_gis_tanahlongsor_2022",
            "PERLU_IZIN",
            "Portal MBG memerlukan izin; layer BNPB 2022 statis.",
            "Selesaikan izin Portal MBG; jangan pakai layer statis sebagai event.",
        ),
        (
            "Likuefaksi",
            "tidak_tercakup_pilot",
            0,
            "bnpb_gis_likuefaksi; geologi_likuefaksi_atlas",
            "BELUM_TERSEDIA",
            "Hanya peta risiko/publikasi; tidak ada feed kejadian.",
            "Riset katalog kejadian resmi; peta risiko bukan event.",
        ),
        (
            "Abrasi dan Akresi",
            "tidak_tercakup_pilot",
            0,
            "bnpb_gis_abrasi; bpisdkp_abrasi",
            "BELUM_TERSEDIA",
            "Peta kerentanan 521 dan halaman KKP 404; tidak ada feed kejadian.",
            "Riset sumber resmi dan bukti kejadian.",
        ),
        (
            "Penurunan Muka Tanah",
            "tidak_tercakup_pilot",
            0,
            "geologi_patgtl; big_atlas_kebencanaan",
            "TERVERIFIKASI_MANUAL",
            "Publikasi/peta tematik, bukan feed kejadian.",
            "Riset katalog penurunan muka tanah resmi.",
        ),
        (
            "Semburan Gas dan Lumpur",
            "tidak_tercakup_pilot",
            0,
            "bpls_sda",
            "TERVERIFIKASI_MANUAL",
            "Halaman informasi manual; tidak ada API/katalog kejadian.",
            "Riset sumber kejadian khusus dan izin.",
        ),
    ]
    return [
        {
            "kategori": category,
            "status_pilot": status,
            "jumlah_event_pilot": str(count),
            "source_id": source,
            "status_sumber": source_status,
            "alasan": reason,
            "langkah_berikutnya": next_step,
        }
        for category, status, count, source, source_status, reason, next_step in rows
    ]


def main():
    dictionary = load_dictionary()
    register = load_register()
    baseline_before = dataset_baseline.verify_dataset()
    run_id = choose_run_id()
    run_dir = make_run_dir(run_id)
    started_at = iso_utc()
    tables = {entity: [] for entity in ENTITY_ORDER}
    feed_results = {}
    items = []
    issues = []

    for index, config in enumerate(SOURCE_CONFIG):
        if index:
            time.sleep(DELAY_SECONDS)
        source_id = config["source_id"]
        register_row = register[source_id]
        fetch = fetch_source(config, register)
        raw_row = build_raw_row(
            source_id, fetch["feed_url"], fetch, run_dir, run_id
        )
        tables["raw_payload"].append(raw_row)
        tables["source"].append(
            build_source_row(
                register_row,
                config,
                fetch["http_status"],
                fetch["retrieved_at"],
            )
        )
        if fetch["error"] or fetch["http_status"] != 200 or not fetch["content"]:
            issues.append(
                {
                    "issue_id": f"NET-{source_id}",
                    "severity": "P1",
                    "area": "akses_sumber",
                    "source_id": source_id,
                    "description": (
                        f"Fetch gagal: HTTP {fetch['http_status']}; "
                        f"{fetch['error']}"
                    ),
                    "impact": "Sumber tidak menghasilkan dokumen pada pilot.",
                    "action": "Periksa konektivitas/TLS; jangan matikan verifikasi.",
                }
            )
            feed_results[source_id] = {
                "items_parsed": 0,
                "items_selected": 0,
                "http_status": fetch["http_status"],
                "error": fetch["error"] or f"HTTP {fetch['http_status']}",
            }
            continue
        if config["parser"] == "bmkg":
            parsed_items, error = parse_bmkg_items(fetch["content"], config)
            total_entries = len(parsed_items)
        else:
            parsed_items, total_entries, error = parse_usgs_items(
                fetch["content"]
            )
        max_items = config.get("max_items", MAX_ITEMS_PER_SOURCE)
        selected_items = (
            parsed_items
            if max_items is None
            else parsed_items[: int(max_items)]
        )
        for item in selected_items:
            item["register_row"] = register_row
            item["role"] = config["role"]
            item["language"] = config["language"]
            item["retrieved_at"] = fetch["retrieved_at"]
            item["raw_payload_id"] = raw_row["raw_payload_id"]
            item["document_id"], item["canonical_url"] = document_identity(
                item, fetch["feed_url"]
            )
            item["event_id"], item["event_source_native_id"] = event_identity(
                item
            )
        items.extend(selected_items)
        feed_results[source_id] = {
            "items_parsed": total_entries,
            "items_selected": len(selected_items),
            "http_status": fetch["http_status"],
            "error": error,
        }
        if error:
            issues.append(
                {
                    "issue_id": f"PARSE-{source_id}",
                    "severity": "P1",
                    "area": "parsing",
                    "source_id": source_id,
                    "description": error,
                    "impact": "Sebagian/semua item tidak masuk pilot.",
                    "action": "Periksa format payload mentah.",
                }
            )

    raw_by_id = {
        row["raw_payload_id"]: row for row in tables["raw_payload"]
    }
    for item in items:
        raw_row = raw_by_id[item["raw_payload_id"]]
        item["document_row"] = build_document(
            item,
            {
                "feed_url": register[item["source_id"]]["url"],
                "retrieved_at": item["retrieved_at"],
            },
            raw_row,
            run_id,
            dictionary,
        )
        tables["document"].append(item["document_row"])

    grouped = defaultdict(list)
    for item in items:
        grouped[item["event_key"]].append(item)

    for group_items in grouped.values():
        group = build_event_group(group_items, dictionary)
        event_id = group["event"]["event_id"]
        primary = group["primary"]
        tables["event"].append(group["event"])
        tables["event_time"].append(group["event_time"])
        tables["event_location"].append(group["event_location"])
        tables["category"].append(group["category"])
        mention = empty_row(dictionary["location_mention"])
        mention.update(
            {
                "location_mention_id": "LOCM-"
                + sha256_text(
                    f"{primary['document_id']}|{event_id}"
                )[:12].upper(),
                "document_id": primary["document_id"],
                "linked_event_id": event_id,
                "mention_text": primary["location_name"],
                "mention_normalized": primary["location_name"],
                "mention_role": "event_location",
                "mention_status": "normalized",
                "mention_confidence": "medium",
                "mention_evidence": (
                    f"Judul/lokasi record {primary['source_id']}"
                ),
                "mention_notes": (
                    "Normalisasi teks; belum verifikasi lapangan."
                ),
            }
        )
        tables["location_mention"].append(mention)
        for item in group["items"]:
            tables["document_event_link"].append(
                build_link(
                    item,
                    event_id,
                    "ya" if item is primary else "tidak",
                    dictionary,
                )
            )
        tables["event_assertion"].extend(
            build_assertions(primary, event_id, dictionary)
        )
        tables["event_attribute"].extend(
            build_attributes(primary, event_id, dictionary)
        )
        tables["verification"].append(
            build_verification(group["event"], primary, dictionary)
        )

    finished_at = iso_utc()
    tables["change_log"] = build_change_logs(
        tables, dictionary, finished_at
    )

    for entity in ENTITY_ORDER:
        write_csv(
            run_dir / "tables" / f"{entity}.csv",
            tables[entity],
            dictionary[entity],
        )

    duplicates = duplicate_candidates(
        tables["event"], tables["event_location"], tables["event_time"]
    )
    duplicate_fields = [
        "bmkg_event_id",
        "usgs_event_id",
        "bmkg_source_id",
        "time_diff_seconds",
        "distance_km",
        "bmkg_title",
        "usgs_title",
        "recommended_action",
        "reason",
    ]
    write_csv(
        run_dir / "pilot_duplicate_candidates.csv",
        duplicates,
        duplicate_fields,
    )

    doc_by_source = Counter(
        row["document_source_id"] for row in tables["document"]
    )
    event_by_source = Counter(
        row["event_primary_source_id"] for row in tables["event"]
    )
    document_source = {
        row["document_id"]: row["document_source_id"]
        for row in tables["document"]
    }
    link_by_source = Counter(
        document_source[row["document_id"]]
        for row in tables["document_event_link"]
    )
    source_summary = []
    for config in SOURCE_CONFIG:
        source_id = config["source_id"]
        info = feed_results.get(source_id, {})
        source_summary.append(
            {
                "source_id": source_id,
                "documents": str(doc_by_source[source_id]),
                "events_primary": str(event_by_source[source_id]),
                "events_mentioned": str(link_by_source[source_id]),
                "items_parsed": str(info.get("items_parsed", 0)),
                "items_selected": str(info.get("items_selected", 0)),
                "http_status": str(
                    info.get("http_status", register[source_id]["http_status"])
                ),
                "error": info.get("error", ""),
                "notes": (
                    "Feed hanya memuat satu gempa terbaru."
                    if source_id == "bmkg_autogempa"
                    else (
                        f"Batas {config.get('max_items', MAX_ITEMS_PER_SOURCE)} item per sumber."
                        if config.get("max_items", MAX_ITEMS_PER_SOURCE)
                        is not None
                        else "Tanpa batas item per sumber; seluruh item terbaru diambil."
                    )
                ),
            }
        )
    source_summary_fields = [
        "source_id",
        "documents",
        "events_primary",
        "events_mentioned",
        "items_parsed",
        "items_selected",
        "http_status",
        "error",
        "notes",
    ]
    write_csv(
        run_dir / "pilot_source_summary.csv",
        source_summary,
        source_summary_fields,
    )

    gaps = category_gap_rows(len(tables["event"]))
    gap_fields = [
        "kategori",
        "status_pilot",
        "jumlah_event_pilot",
        "source_id",
        "status_sumber",
        "alasan",
        "langkah_berikutnya",
    ]
    write_csv(run_dir / "pilot_category_gaps.csv", gaps, gap_fields)

    issues.extend(
        [
            {
                "issue_id": "LIC-01",
                "severity": "P1",
                "area": "lisensi",
                "source_id": "semua",
                "description": "Lisensi/izin redistribusi belum diverifikasi.",
                "impact": "Pilot tidak boleh dipromosikan sebagai rilis publik.",
                "action": "Selesaikan lisensi sebelum publikasi/redistribusi.",
            },
            {
                "issue_id": "ROB-01",
                "severity": "P1",
                "area": "robots",
                "source_id": (
                    "bmkg_autogempa; bmkg_gempa_terkini; bmkg_gempa_dirasakan"
                ),
                "description": "robots.txt BMKG tidak terbaca (SSL/HTTPError).",
                "impact": "Status robots tidak dapat dianggap izin.",
                "action": "Gunakan laju rendah; jangan klaim izin dari robots.",
            },
            {
                "issue_id": "URL-01",
                "severity": "P2",
                "area": "dokumen",
                "source_id": (
                    "bmkg_autogempa; bmkg_gempa_terkini; bmkg_gempa_dirasakan"
                ),
                "description": (
                    "BMKG tidak menyediakan URL halaman stabil per record; "
                    "URL dokumen memakai feed dan fragmen record."
                ),
                "impact": "Tautan dokumen tidak dapat dibuka per record.",
                "action": "Simpan raw payload dan ID eksternal sebagai bukti.",
            },
            {
                "issue_id": "WIN-01",
                "severity": "P2",
                "area": "cakupan",
                "source_id": "bmkg_autogempa; bmkg_gempa_terkini; bmkg_gempa_dirasakan",
                "description": "Feed BMKG adalah jendela terbatas, bukan arsip.",
                "impact": "Pilot tidak mewakili riwayat penuh.",
                "action": "Rancang snapshot berkala dan retensi yang sah.",
            },
            {
                "issue_id": "DUP-01",
                "severity": "P2",
                "area": "deduplikasi",
                "source_id": "bmkg_*; usgs_m45",
                "description": (
                    f"{len(duplicates)} pasangan BMKG-USGS berdekatan waktu/lokasi."
                ),
                "impact": "Event fisik yang sama dapat terhitung dua kali.",
                "action": "Review manual; jangan gabung otomatis.",
            },
            {
                "issue_id": "GAP-01",
                "severity": "P1",
                "area": "cakupan",
                "source_id": "semua",
                "description": "Hanya Gempabumi yang tercakup pada pilot.",
                "impact": "Klaim 8 kategori lengkap tidak boleh dilakukan.",
                "action": "Selesaikan izin/sumber untuk 7 kategori lainnya.",
            },
        ]
    )
    issue_fields = [
        "issue_id",
        "severity",
        "area",
        "source_id",
        "description",
        "impact",
        "action",
    ]
    write_csv(run_dir / "pilot_issues.csv", issues, issue_fields)

    validation_rows = validate(tables, register, run_dir)
    validation_fields = [
        "rule_id",
        "severity",
        "entity",
        "records_checked",
        "status",
        "detail",
        "record_refs",
    ]
    write_csv(
        run_dir / "pilot_validation_results.csv",
        validation_rows,
        validation_fields,
    )

    baseline_after = dataset_baseline.verify_dataset()
    gates = quality_gates(
        validation_rows, baseline_after, tables["source"]
    )
    gate_fields = [
        "gate_id",
        "gate",
        "status",
        "rules_checked",
        "notes",
        "failed_rules",
        "review_rules",
    ]
    write_csv(run_dir / "pilot_quality_gates.csv", gates, gate_fields)

    validation_counts = Counter(row["status"] for row in validation_rows)
    p0_failures = [
        row["rule_id"]
        for row in validation_rows
        if row["severity"] == "P0" and row["status"] == "gagal"
    ]
    category_counts = Counter(
        row["category_name"] for row in tables["category"]
    )
    summary = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "schema_version": SCHEMA_VERSION,
        "baseline": {
            "path": dataset_baseline.DATASET_RELATIVE_PATH,
            "sha256": baseline_after["sha256"],
            "rows": baseline_after["rows"],
            "columns": baseline_after["columns"],
            "unchanged": baseline_after["sha256"]
            == dataset_baseline.DATASET_SHA256,
        },
        "sources": [row["source_id"] for row in tables["source"]],
        "counts": {
            entity: len(tables[entity]) for entity in ENTITY_ORDER
        },
        "documents_by_source": dict(doc_by_source),
        "events_by_primary_source": dict(event_by_source),
        "categories": dict(category_counts),
        "duplicate_candidates": len(duplicates),
        "validation": {
            "counts": dict(validation_counts),
            "p0_failures": p0_failures,
        },
        "quality_gates": {
            row["gate_id"]: row["status"] for row in gates
        },
        "scope": {
            "covered": ["Gempabumi"],
            "not_covered": [
                "Gunungapi",
                "Tsunami",
                "Gerakan Tanah/Tanah Longsor",
                "Likuefaksi",
                "Abrasi dan Akresi",
                "Penurunan Muka Tanah",
                "Semburan Gas dan Lumpur",
            ],
            "note": "Pilot tidak boleh diklaim lengkap 8 kategori.",
        },
        "limits": {
            "max_items_per_source": {
                config["source_id"]: config.get(
                    "max_items", MAX_ITEMS_PER_SOURCE
                )
                for config in SOURCE_CONFIG
            },
            "delay_seconds": DELAY_SECONDS,
            "timeout_seconds": TIMEOUT_SECONDS,
            "indonesia_bbox": list(INDONESIA_BBOX),
            "network_client": "python-requests",
            "tls_verification": True,
        },
    }
    summary_path = run_dir / "pilot_summary.json"
    write_json(summary_path, summary)

    output_paths = []
    for entity in ENTITY_ORDER:
        output_paths.append(run_dir / "tables" / f"{entity}.csv")
    output_paths.extend(
        [
            run_dir / "pilot_duplicate_candidates.csv",
            run_dir / "pilot_source_summary.csv",
            run_dir / "pilot_category_gaps.csv",
            run_dir / "pilot_issues.csv",
            run_dir / "pilot_validation_results.csv",
            run_dir / "pilot_quality_gates.csv",
            summary_path,
        ]
    )
    manifest = {
        "run_id": run_id,
        "script": str(Path(__file__).resolve().relative_to(ROOT)).replace(
            "\\", "/"
        ),
        "started_at": started_at,
        "finished_at": finished_at,
        "schema_version": SCHEMA_VERSION,
        "baseline": summary["baseline"],
        "limits": summary["limits"],
        "sources": [row["source_id"] for row in tables["source"]],
        "counts": summary["counts"],
        "outputs": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in output_paths
        ],
        "notes": [
            "Raw payload bersifat immutable per run.",
            "Tidak ada database, dashboard, atau perubahan baseline.",
            "Pilot ini bukan rilis publik dan belum lolos lisensi.",
        ],
    }
    write_json(run_dir / "manifest.json", manifest)
    write_json(
        PILOT_ROOT / "LATEST.json",
        {
            "latest_run_id": run_id,
            "manifest": str(
                (run_dir / "manifest.json").relative_to(ROOT)
            ).replace("\\", "/"),
            "updated_at": finished_at,
            "note": "Pointer ke run pilot terbaru; raw run lama tidak ditimpa.",
        },
    )

    print(f"RUN_ID={run_id}")
    print(f"RUN_DIR={run_dir}")
    print(f"DOCUMENTS={len(tables['document'])}")
    print(f"EVENTS={len(tables['event'])}")
    print(f"DUPLICATE_CANDIDATES={len(duplicates)}")
    print(f"VALIDATION={dict(validation_counts)}")
    print(f"QUALITY_GATES={summary['quality_gates']}")
    print(f"BASELINE_UNCHANGED={summary['baseline']['unchanged']}")
    if p0_failures or not summary["baseline"]["unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
