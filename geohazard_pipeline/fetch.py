"""HTTP fetching and immutable raw snapshot storage."""

import mimetypes
from datetime import datetime, timezone
from pathlib import Path

import requests

from .util import ROOT, iso_utc, sha256_bytes

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "GeoHazard-News-Locator/1.0"
    ),
    "Accept": (
        "application/rss+xml, application/atom+xml, application/xml, "
        "text/xml, */*"
    ),
}

EXTENSIONS = {
    "bmkg_xml": "xml",
    "rss": "xml",
    "atom": "atom",
    "api": "json",
}


def fetch_url(url, timeout=30):
    retrieved_at = iso_utc()
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        return {
            "content": response.content,
            "http_status": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "retrieved_at": retrieved_at,
            "error": "" if response.status_code == 200 else f"HTTP {response.status_code}",
        }
    except requests.RequestException as exc:
        return {
            "content": b"",
            "http_status": 0,
            "content_type": "",
            "retrieved_at": retrieved_at,
            "error": str(exc)[:500],
        }


def read_offline_payload(raw_dir, source_id, page_number=1):
    raw_dir = Path(raw_dir)
    stem = source_id if page_number == 1 else f"{source_id}_p{page_number}"
    candidates = [
        raw_dir / f"{stem}.xml",
        raw_dir / f"{stem}.atom",
        raw_dir / f"{stem}.json",
        raw_dir / f"{stem}.rss",
    ]
    for candidate in candidates:
        if candidate.is_file():
            content = candidate.read_bytes()
            content_type = mimetypes.guess_type(candidate.name)[0] or ""
            return {
                "content": content,
                "http_status": 200,
                "content_type": content_type,
                "retrieved_at": iso_utc(
                    datetime.fromtimestamp(candidate.stat().st_mtime, timezone.utc)
                ),
                "error": "",
                "path": candidate,
            }
    return None


def save_raw(run_dir, source_id, feed_type, content, digest, page_number=1):
    extension = EXTENSIONS.get(feed_type, "bin")
    raw_dir = Path(run_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stem = source_id if page_number == 1 else f"{source_id}_p{page_number}"
    path = raw_dir / f"{stem}.{extension}"
    if path.exists():
        if sha256_bytes(path.read_bytes()) == digest:
            return path
        index = 2
        while True:
            candidate = raw_dir / f"{stem}_{index}.{extension}"
            if not candidate.exists():
                path = candidate
                break
            if sha256_bytes(candidate.read_bytes()) == digest:
                return candidate
            index += 1
    with open(path, "xb") as handle:
        handle.write(content)
    return path


def raw_payload_row(source_id, feed_url, fetch, run_dir, run_id, page_number=1):
    content = fetch["content"]
    digest = sha256_bytes(content)
    path = (
        save_raw(
            run_dir,
            source_id,
            fetch.get("feed_type", ""),
            content,
            digest,
            page_number,
        )
        if content
        else None
    )
    if not path:
        relative_path = ""
    else:
        try:
            relative_path = str(path.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            relative_path = str(path).replace("\\", "/")
    page_suffix = "" if page_number == 1 else f"-p{page_number}"
    raw_id = (
        f"RAW-{source_id}-{run_id.replace('RUN-', '')}"
        f"{page_suffix}-{digest[:8]}"
    )
    return {
        "raw_payload_id": raw_id,
        "raw_payload_source_id": source_id,
        "raw_payload_url": feed_url,
        "raw_payload_retrieved_at": fetch["retrieved_at"],
        "raw_payload_http_status": str(fetch["http_status"]),
        "raw_payload_content_type": fetch.get("content_type", ""),
        "raw_payload_sha256": digest,
        "raw_payload_size_bytes": str(len(content)),
        "raw_payload_path": relative_path,
        "raw_payload_status": "stored" if content else "missing",
        "raw_payload_notes": (
            "Snapshot mentah immutable; tidak ditimpa."
            if content
            else f"Respons kosong/gagal: {fetch.get('error', '')}"
        ),
    }
