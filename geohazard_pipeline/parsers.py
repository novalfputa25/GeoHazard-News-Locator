"""Parsers for the active official feeds, GDACS, and news RSS feeds."""

import re
from urllib.parse import quote

import feedparser

from category_detector import detect_category_detail
from scripts import pilot_collect_official_geohazard as pilot

from .util import normalize_time, parse_datetime, strip_html

INDONESIA_BBOX = (-11.0, 6.0, 95.0, 141.0)

GDACS_EVENT_TYPES = {
    "EQ": "Gempabumi",
    "VO": "Gunungapi",
    "TC": "Cuaca Ekstrem",
    "FL": "Lainnya",
    "DR": "Lainnya",
    "WF": "Lainnya",
}


def _inside_bbox(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return False
    south, north, west, east = INDONESIA_BBOX
    return south <= lat <= north and west <= lon <= east


def parse_bmkg(content, config):
    items, error = pilot.parse_bmkg_items(content, config)
    for item in items:
        item["category_original"] = "Gempabumi"
        item["feed_type"] = "bmkg_xml"
        item["published_at"] = None
        item["updated_at"] = None
        item["canonical_url"] = (
            f"{config['url']}#record={quote(item['external_id'], safe='')}"
        )
    return items, error


def parse_usgs(content, config):
    items, total, error = pilot.parse_usgs_items(content)
    for item in items:
        item["category_original"] = "Gempabumi"
        item["feed_type"] = "atom"
        item["published_at"] = item.get("updated_at")
        item["canonical_url"] = item.get("document_url", "")
    return items, total, error


def parse_gdacs(content, config):
    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        return [], f"RSS tidak valid: {feed.bozo_exception}"
    items = []
    for entry in feed.entries:
        event_type = str(entry.get("gdacs_eventtype", "")).upper()
        if not event_type:
            continue
        country = str(entry.get("gdacs_country", ""))
        lat = entry.get("geo_lat") or ""
        lon = entry.get("geo_long") or ""
        if "indonesia" not in country.lower() and not _inside_bbox(lat, lon):
            continue
        event_time = parse_datetime(entry.get("gdacs_fromdate")) or parse_datetime(
            entry.get("published")
        )
        if event_time is None:
            continue
        published = parse_datetime(entry.get("published"))
        updated = parse_datetime(entry.get("gdacs_datemodified")) or published
        severity = entry.get("gdacs_severity")
        magnitude = ""
        if isinstance(severity, dict):
            magnitude = str(severity.get("value", "") or "")
        summary = strip_html(
            entry.get("summary")
            or entry.get("description")
            or entry.get("gdacs_description")
            or ""
        )
        title = strip_html(entry.get("title", "")) or f"GDACS {event_type}"
        native = f"{event_type}{entry.get('gdacs_eventid', '')}"
        url = entry.get("link", "") or entry.get("id", "")
        items.append(
            {
                "source_id": config["source_id"],
                "priority": config.get("priority", 3),
                "external_id": native,
                "native_id": native,
                "title": title,
                "event_time": event_time,
                "event_time_evidence": (
                    f"gdacs:fromdate={entry.get('gdacs_fromdate', '')}"
                ),
                "lat": lat,
                "lon": lon,
                "magnitude": magnitude,
                "magnitude_text": magnitude,
                "depth_text": "",
                "location_name": country or title,
                "category_original": GDACS_EVENT_TYPES.get(event_type, "Lainnya"),
                "updated_at": updated,
                "published_at": published,
                "document_url": url,
                "canonical_url": url,
                "feed_type": "rss",
                "event_key": f"GDACS|{native}",
                "extra": {
                    "event_type": event_type,
                    "country": country,
                    "alert_level": entry.get("gdacs_alertlevel", ""),
                    "summary": summary,
                },
            }
        )
    return items, ""


def parse_news_rss(content, config):
    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        return [], f"RSS tidak valid: {feed.bozo_exception}"
    items = []
    for entry in feed.entries:
        title = strip_html(entry.get("title", ""))
        link = entry.get("link", "") or entry.get("id", "")
        external_id = entry.get("id") or entry.get("guid") or link
        summary = ""
        content_value = entry.get("content")
        if isinstance(content_value, list) and content_value:
            summary = content_value[0].get("value", "")
        summary = summary or entry.get("summary") or entry.get("description") or ""
        summary = strip_html(summary)
        published = parse_datetime(entry.get("published")) or parse_datetime(
            entry.get("updated")
        )
        updated = parse_datetime(entry.get("updated")) or published
        category, basis = detect_category_detail(title, summary)
        items.append(
            {
                "source_id": config["source_id"],
                "priority": config.get("priority", 9),
                "external_id": external_id,
                "native_id": "",
                "title": title,
                "event_time": None,
                "event_time_evidence": "",
                "lat": "",
                "lon": "",
                "magnitude": "",
                "magnitude_text": "",
                "depth_text": "",
                "location_name": "",
                "category_original": category,
                "category_basis": basis,
                "updated_at": updated,
                "published_at": published,
                "document_url": link,
                "canonical_url": link,
                "feed_type": "rss",
                "event_key": "",
                "extra": {"summary": summary},
            }
        )
    return items, ""


def parse_source(source_id, content, config):
    if config.get("parser") == "bmkg":
        return parse_bmkg(content, config)
    if source_id == "usgs_m45":
        items, _total, error = parse_usgs(content, config)
        return items, error
    if source_id == "gdacs_all":
        return parse_gdacs(content, config)
    return parse_news_rss(content, config)
