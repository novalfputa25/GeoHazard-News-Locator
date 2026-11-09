import csv
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from geohazard_pipeline import runner
from geohazard_pipeline.db import import_run_dir, initialize_database


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def rss_feed(indexes):
    items = "".join(
        (
            f"<item><title>Gempa bumi uji {index}</title>"
            f"<link>https://example.test/artikel/{index}</link>"
            f"<guid>https://example.test/artikel/{index}</guid>"
            "<pubDate>Mon, 02 Nov 2026 10:00:00 +0000</pubDate>"
            "<description>Gempa bumi dan potensi tsunami.</description>"
            "</item>"
        )
        for index in indexes
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel><title>Uji</title>'
        "<link>https://example.test</link><description>Uji</description>"
        f"{items}</channel></rss>"
    ).encode("utf-8")


def feed_config(**overrides):
    config = {
        "id": "mongabay_indonesia",
        "nama": "Feed Uji",
        "url": "https://example.test/feed",
        "tipe": "rss",
        "bahasa": "id",
        "negara": "Indonesia",
        "max_items": None,
    }
    config.update(overrides)
    return config


class PipelineItemSelectionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _run(self, config, page_content, **kwargs):
        calls = []

        def fake_fetch(url, timeout=30):
            calls.append(url)
            query = parse_qs(urlsplit(url).query)
            page = int(query.get("page", ["1"])[0])
            return {
                "content": page_content(page),
                "http_status": 200,
                "content_type": "application/rss+xml",
                "retrieved_at": "2026-11-02T10:00:00+00:00",
                "error": "",
            }

        with patch.object(
            runner,
            "load_active_feed_configs",
            return_value=[config],
        ), patch.object(runner, "fetch_url", side_effect=fake_fetch):
            manifest = runner.run_pipeline(
                output_root=self.temp_root / "runs",
                run_id="RUN-TEST-ITEM-SELECTION",
                fetch_delay=0,
                **kwargs,
            )
        return manifest, calls

    def test_all_items_are_selected_when_no_limit_is_configured(self):
        manifest, calls = self._run(
            feed_config(),
            lambda page: rss_feed(range(25)),
        )
        source = manifest["sources"]["mongabay_indonesia"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(source["items_parsed"], 25)
        self.assertEqual(source["items_selected"], 25)
        self.assertEqual(source["items_imported"], 25)
        self.assertEqual(source["items_duplicates"], 0)
        self.assertEqual(source["stop_reason"], "")
        self.assertEqual(manifest["counts"]["document"], 25)

    def test_per_source_limit_is_applied_after_parsing(self):
        manifest, calls = self._run(
            feed_config(max_items=7),
            lambda page: rss_feed(range(25)),
        )
        source = manifest["sources"]["mongabay_indonesia"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(source["items_parsed"], 25)
        self.assertEqual(source["items_selected"], 7)
        self.assertEqual(source["items_imported"], 7)
        self.assertEqual(source["stop_reason"], "max_items")
        self.assertEqual(manifest["counts"]["document"], 7)

    def test_source_limit_overrides_global_limit(self):
        manifest, calls = self._run(
            feed_config(),
            lambda page: rss_feed(range(25)),
            max_items=5,
            max_items_by_source={"mongabay_indonesia": 9},
        )
        source = manifest["sources"]["mongabay_indonesia"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(source["items_selected"], 9)
        self.assertEqual(source["items_imported"], 9)
        self.assertEqual(source["max_items"], 9)

    def test_pagination_collects_pages_and_deduplicates_items(self):
        pages = {
            1: rss_feed(range(12)),
            2: rss_feed(range(10, 22)),
            3: rss_feed(range(10, 22)),
        }
        config = feed_config(
            url="https://example.test/feed?lang=id",
            pagination={
                "type": "query",
                "param": "page",
                "max_pages": 3,
            },
        )
        manifest, calls = self._run(config, lambda page: pages[page])
        source = manifest["sources"]["mongabay_indonesia"]
        self.assertEqual(
            calls,
            [
                "https://example.test/feed?lang=id",
                "https://example.test/feed?lang=id&page=2",
                "https://example.test/feed?lang=id&page=3",
            ],
        )
        self.assertEqual(source["pages_fetched"], 3)
        self.assertEqual(source["pages_succeeded"], 3)
        self.assertEqual(source["items_parsed"], 36)
        self.assertEqual(source["items_duplicates"], 14)
        self.assertEqual(source["items_selected"], 22)
        self.assertEqual(source["items_imported"], 22)
        self.assertEqual(source["stop_reason"], "no_new_items")
        self.assertEqual(manifest["counts"]["document"], 22)

        raw_rows = read_csv(
            Path(manifest["run_dir"]) / "tables" / "raw_payload.csv"
        )
        self.assertEqual(len(raw_rows), 3)
        self.assertTrue(
            any(row["raw_payload_path"].endswith("_p2.xml") for row in raw_rows)
        )
        self.assertTrue(
            any(row["raw_payload_path"].endswith("_p3.xml") for row in raw_rows)
        )
        self.assertTrue(
            any("page=2" in row["raw_payload_url"] for row in raw_rows)
        )

    def test_pagination_stops_when_limit_is_reached(self):
        config = feed_config(
            max_items=15,
            pagination={
                "type": "query",
                "param": "page",
                "max_pages": 5,
            },
        )
        manifest, calls = self._run(
            config,
            lambda page: rss_feed(range((page - 1) * 12, page * 12)),
        )
        source = manifest["sources"]["mongabay_indonesia"]
        self.assertEqual(len(calls), 2)
        self.assertEqual(source["pages_fetched"], 2)
        self.assertEqual(source["items_parsed"], 24)
        self.assertEqual(source["items_selected"], 15)
        self.assertEqual(source["items_imported"], 15)
        self.assertEqual(source["stop_reason"], "max_items")

    def test_selected_items_import_idempotently(self):
        manifest, _ = self._run(
            feed_config(max_items=10),
            lambda page: rss_feed(range(25)),
        )
        database = self.temp_root / "selection.db"
        initialize_database(database)
        first = import_run_dir(database, manifest["run_dir"], initialize=False)
        second = import_run_dir(database, manifest["run_dir"], initialize=False)
        self.assertEqual(first["foreign_key_check"], [])
        self.assertEqual(second["foreign_key_check"], [])
        with closing(sqlite3.connect(database)) as connection:
            document_count = connection.execute(
                "SELECT COUNT(*) FROM document"
            ).fetchone()[0]
        self.assertEqual(document_count, 10)


if __name__ == "__main__":
    unittest.main()
