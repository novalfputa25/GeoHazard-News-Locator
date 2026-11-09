"""Shared helpers for the unified pipeline."""

import csv
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = ROOT / "docs" / "MASTER_SOURCE_REGISTER.csv"
BASELINE_PATH = ROOT / "data" / "geohazard_news_final_20261101T150501Z.csv"
BASELINE_SHA256 = "be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06"
SCHEMA_VERSION = "1.0.0"

TARGET_CATEGORIES = (
    "Gunungapi",
    "Gempabumi",
    "Tsunami",
    "Gerakan Tanah/Tanah Longsor",
    "Likuefaksi",
    "Abrasi dan Akresi",
    "Penurunan Muka Tanah",
    "Semburan Gas dan Lumpur",
)

SCOPE_IN = "in_scope"
SCOPE_OUT = "out_of_scope"
SCOPE_UNCLASSIFIED = "unclassified"

ROLE_TO_SOURCE_TYPE = {
    "sumber_utama_resmi": "official",
    "internasional_pendukung": "official",
    "berita_pendukung": "news",
}


def utc_now():
    return datetime.now(timezone.utc)


def iso_utc(value=None):
    value = value or utc_now()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_id(prefix, value, length=16):
    return f"{prefix}-{sha256_text(value)[:length].upper()}"


def strip_html(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_datetime(value):
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError, OverflowError):
            parsed = None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_time(value):
    parsed = parse_datetime(value)
    return parsed.isoformat() if parsed else ""


def parse_iso_duration_hours(value):
    text = str(value or "").strip()
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", text)
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours + minutes / 60 + seconds / 3600


def timezone_name(value):
    text = str(value or "").strip()
    if not text:
        return "Etc/UTC"
    try:
        ZoneInfo(text)
        return text
    except Exception:
        return "Etc/UTC"


def category_scope(category_name, title="", content=""):
    if category_name in TARGET_CATEGORIES:
        return SCOPE_IN
    haystack = f"{title} {content}".lower()
    out_markers = (
        "cuaca ekstrem",
        "kebakaran hutan",
        "karhutla",
        "banjir",
        "kekeringan",
        "angin puting beliung",
        "gelombang tinggi",
    )
    if any(marker in haystack for marker in out_markers):
        return SCOPE_OUT
    return SCOPE_UNCLASSIFIED


def source_type_from_role(role):
    return ROLE_TO_SOURCE_TYPE.get(role, "unknown")


def source_role_to_document_role(role):
    return {
        "sumber_utama_resmi": "primary_official",
        "internasional_pendukung": "supporting_official",
        "berita_pendukung": "news_support",
    }.get(role, "unknown")


def normalize_registry_status(value):
    text = str(value or "").strip().upper()
    if text in {
        "TERVERIFIKASI_AKTIF",
        "TERVERIFIKASI_MANUAL",
        "PERLU_IZIN",
        "BELUM_TERSEDIA",
        "TIDAK_SESUAI",
    }:
        return text
    return "BELUM_TERSEDIA"


def normalize_robots(value):
    text = str(value or "").strip().lower()
    if not text:
        return "not_checked"
    if text.startswith(("dilarang", "disallow")):
        return "disallowed"
    if "diizinkan" in text or text.startswith("allow"):
        return "allowed"
    if "tidak ditemukan" in text or "404" in text:
        return "not_found"
    if "tidak_terbaca" in text or "tidak terbaca" in text or "ssl" in text:
        return "unreadable"
    return "not_checked"


def load_register(path=REGISTER_PATH):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return {
            row["source_id"]: row
            for row in csv.DictReader(handle)
            if row.get("source_id")
        }


def load_active_feed_configs(max_items=None):
    from feeds import FEEDS

    configs = []
    for feed in FEEDS:
        if not feed.get("aktif"):
            continue
        config = dict(feed)
        config["source_id"] = feed["id"]
        if "max_items" not in config and max_items is not None:
            config["max_items"] = max_items
        configs.append(config)
    return configs


def registry_to_source_row(register_row, feed_config, http_status, retrieved_at):
    source_type = source_type_from_role(register_row.get("peran", ""))
    data_type = (
        "event_feed"
        if source_type == "official" and feed_config.get("tipe") in ("bmkg_xml", "rss", "atom", "api")
        else "article"
    )
    if source_type == "official" and feed_config.get("tipe") == "rss":
        # USGS/GDACS RSS feeds are event feeds, while ANTARA/Mongabay RSS feeds are articles.
        if feed_config["source_id"] in {"usgs_m45", "gdacs_all"}:
            data_type = "event_feed"
    return {
        "source_id": feed_config["source_id"],
        "source_name": register_row.get("nama_sumber", feed_config.get("nama", "")),
        "source_institution": register_row.get("institusi", ""),
        "source_country": (
            "Indonesia"
            if register_row.get("peran") == "sumber_utama_resmi"
            else "internasional"
        ),
        "source_language": feed_config.get("bahasa", ""),
        "source_type": source_type,
        "source_role": source_role_to_document_role(register_row.get("peran", "")),
        "source_data_type": data_type,
        "source_url": register_row.get("url", ""),
        "source_feed_url": feed_config.get("url", ""),
        "source_registry_status": normalize_registry_status(
            register_row.get("status_sumber", "")
        ),
        "source_license_status": "unverified",
        "source_license": "belum_diverifikasi",
        "source_terms_url": "",
        "source_last_tested_at": retrieved_at,
        "source_http_status": str(http_status),
        "source_robots_status": normalize_robots(register_row.get("robots", "")),
        "source_notes": (
            f"{register_row.get('catatan', '')} Pipeline hanya memakai sumber "
            "aktif; lisensi/redistribusi belum diverifikasi."
        ).strip(),
    }


def event_identity_for_bmkg(item):
    event_id = "EVT-BMKG-" + sha256_text(item["event_key"])[:12].upper()
    return event_id, ""


def event_identity_for_usgs(item):
    return f"EVT-USGS-{item['native_id']}", item["native_id"]


def event_identity_for_gdacs(item):
    native = (
        item.get("native_id")
        or item.get("external_id")
        or f"{item.get('event_type', '')}{item.get('event_id', '')}"
    )
    native = str(native).strip()
    return f"EVT-GDACS-{native.upper()}", native


def document_identity(source_id, external_id, canonical_url):
    document_id = "DOC-" + sha256_text(f"{source_id}|{external_id}")[:16]
    return document_id, canonical_url


def json_dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
