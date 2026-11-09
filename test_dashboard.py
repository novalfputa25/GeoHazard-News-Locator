import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from dashboard.app import create_server
from dashboard.repository import (
    DEFAULT_DB_PATH,
    DashboardFilters,
    NewsSearchFilters,
    UNKNOWN_PROVINCE,
    build_dashboard,
    build_event_detail,
    connect,
    parse_filters,
    parse_search_filters,
    search_news,
)


class DashboardRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_data = build_dashboard()

    def test_main_stats_come_from_active_database(self):
        stats = self.all_data["stats"]
        self.assertEqual(stats["total_documents"], 84)
        self.assertEqual(stats["total_events"], 75)
        self.assertEqual(stats["events_with_location"], 75)
        self.assertEqual(stats["events_with_province"], 31)
        self.assertEqual(stats["events_without_province"], 44)
        self.assertEqual(stats["events_with_time"], 75)
        self.assertEqual(stats["monitored_categories"], 9)
        self.assertEqual(len(self.all_data["categories"]), 9)
        self.assertEqual(
            sum(item["event_count"] for item in self.all_data["categories"]),
            stats["total_events"],
        )
        self.assertEqual(
            sum(point["count"] for point in self.all_data["trend"]["points"]),
            stats["total_events"],
        )

    def test_database_counts_match_direct_queries(self):
        with closing(connect(DEFAULT_DB_PATH)) as connection:
            documents = connection.execute(
                """
                SELECT COUNT(*) FROM document d
                JOIN document_relevance dr ON dr.document_id = d.document_id
                WHERE d.document_status = 'active'
                  AND dr.relevance_status = 'relevan'
                  AND NOT EXISTS (
                      SELECT 1 FROM document_duplicate dd
                      WHERE dd.document_id = d.document_id
                  )
                """
            ).fetchone()[0]
            events = connection.execute("SELECT COUNT(*) FROM event").fetchone()[0]
            times = connection.execute(
                """
                SELECT COUNT(DISTINCT event_id) FROM event_time
                WHERE COALESCE(NULLIF(event_time, ''),
                               NULLIF(event_time_start, '')) IS NOT NULL
                """
            ).fetchone()[0]
        self.assertEqual(self.all_data["stats"]["total_documents"], documents)
        self.assertEqual(self.all_data["stats"]["total_events"], events)
        self.assertEqual(self.all_data["stats"]["events_with_time"], times)

    def test_category_filter_updates_every_component(self):
        data = build_dashboard(filters=DashboardFilters(category="Gempabumi"))
        self.assertEqual(data["stats"]["total_events"], 68)
        self.assertEqual(data["stats"]["total_documents"], 75)
        self.assertEqual(data["stats"]["total_categories"], 1)
        self.assertEqual(
            sum(item["event_count"] for item in data["categories"]),
            68,
        )
        self.assertEqual(
            sum(point["count"] for point in data["trend"]["points"]),
            68,
        )
        self.assertTrue(
            all(row["category"] == "Gempabumi" for row in data["latest_news"])
        )
        self.assertEqual(
            next(
                item["event_count"]
                for item in data["categories"]
                if item["category"] == "Gempabumi"
            ),
            68,
        )

    def test_province_filter_and_unknown_location(self):
        data = build_dashboard(filters=DashboardFilters(province="Jawa Barat"))
        self.assertEqual(data["stats"]["total_events"], 7)
        self.assertEqual(data["stats"]["events_with_province"], 7)
        self.assertEqual(data["stats"]["events_without_province"], 0)
        self.assertEqual(
            [(item["province"], item["count"]) for item in data["regions"]["items"]],
            [("Jawa Barat", 7)],
        )

        unknown = build_dashboard(filters=DashboardFilters(province=UNKNOWN_PROVINCE))
        self.assertEqual(unknown["stats"]["total_events"], 44)
        self.assertEqual(unknown["stats"]["events_with_province"], 0)
        self.assertEqual(unknown["stats"]["events_without_province"], 44)
        self.assertEqual(unknown["regions"]["known_total"], 0)
        self.assertEqual(unknown["regions"]["unknown"], 44)

    def test_date_filter_uses_event_time_and_publish_time(self):
        data = build_dashboard(
            filters=DashboardFilters(
                date_from="2026-10-01",
                date_to="2026-10-31",
            )
        )
        self.assertEqual(data["stats"]["total_events"], 64)
        self.assertEqual(data["stats"]["total_documents"], 46)
        self.assertEqual(data["trend"]["granularity"], "day")
        self.assertEqual(len(data["trend"]["points"]), 31)
        self.assertEqual(
            sum(point["count"] for point in data["trend"]["points"]),
            64,
        )
        for point in data["trend"]["points"]:
            self.assertGreaterEqual(point["period"], "2026-10-01")
            self.assertLessEqual(point["period"], "2026-10-31")
        for row in data["latest_news"]:
            published = row["document_published_at"][:10]
            self.assertGreaterEqual(published, "2026-10-01")
            self.assertLessEqual(published, "2026-10-31")

    def test_latest_news_only_contains_relevant_documents(self):
        data = build_dashboard(latest_limit=100)
        self.assertTrue(data["latest_news"])
        self.assertTrue(
            all(row["relevance_status"] == "relevan" for row in data["latest_news"])
        )
        titles = " ".join(row["document_title"] for row in data["latest_news"])
        for irrelevant in (
            "Monyet Ekor Panjang",
            "Hujan Lebat disertai Petir",
            "Persib Bandung",
            "Konservasi Mangrove Clungup",
        ):
            self.assertNotIn(irrelevant, titles)
        self.assertTrue(
            any("Gempa" in row["document_title"] for row in data["latest_news"])
        )

    def test_relevance_table_covers_active_documents(self):
        with closing(connect(DEFAULT_DB_PATH)) as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM document WHERE document_status = 'active'"
            ).fetchone()[0]
            relevance = connection.execute(
                "SELECT COUNT(*) FROM document_relevance"
            ).fetchone()[0]
            statuses = {
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT relevance_status FROM document_relevance"
                )
            }
        self.assertEqual(relevance, total)
        self.assertTrue(statuses <= {"relevan", "tidak_relevan", "perlu_review"})

    def test_eight_main_categories_are_always_listed(self):
        names = [item["category"] for item in self.all_data["categories"]]
        self.assertEqual(names[:8], [
            "Gunungapi",
            "Gempabumi",
            "Tsunami",
            "Gerakan Tanah/Tanah Longsor",
            "Likuefaksi",
            "Abrasi dan Akresi",
            "Penurunan Muka Tanah",
            "Semburan Gas dan Lumpur",
        ])
        self.assertIn("Lainnya", names)

    def test_empty_database_returns_honest_zeroes(self):
        schema_path = Path(DEFAULT_DB_PATH).parents[1] / "database" / "schema.sql"
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "empty.db"
            connection = sqlite3.connect(db_path)
            connection.executescript(schema_path.read_text(encoding="utf-8"))
            connection.close()

            data = build_dashboard(db_path=db_path)
            self.assertEqual(data["stats"]["total_documents"], 0)
            self.assertEqual(data["stats"]["total_events"], 0)
            self.assertEqual(data["stats"]["events_with_location"], 0)
            self.assertEqual(data["stats"]["events_with_time"], 0)
            self.assertEqual(data["stats"]["total_categories"], 0)
            self.assertEqual(len(data["categories"]), 9)
            self.assertEqual(data["trend"]["points"], [])
            self.assertEqual(data["latest_news"], [])


    def test_region_options_include_province_and_kabupaten_catalog(self):
        options = self.all_data["options"]
        self.assertEqual(len(options["provinces"]), 15)
        self.assertEqual(
            options["provinces"],
            sorted(options["provinces"], key=str.casefold),
        )
        self.assertEqual(
            options["kabupaten_by_province"]["Jawa Barat"],
            ["Kabupaten Garut", "Kabupaten Sukabumi", "Kota Bogor"],
        )
        self.assertEqual(options["kabupaten_by_province"]["Banten"], [])
        self.assertEqual(
            sum(
                len(names)
                for names in options["kabupaten_by_province"].values()
            ),
            14,
        )

    def test_kabupaten_stats_are_honest(self):
        stats = self.all_data["stats"]
        self.assertEqual(stats["events_with_kabupaten_kota"], 21)
        self.assertEqual(stats["events_without_kabupaten_kota"], 54)

        jawa_barat = build_dashboard(
            filters=DashboardFilters(province="Jawa Barat")
        )
        self.assertEqual(
            jawa_barat["stats"]["events_with_kabupaten_kota"], 6
        )
        self.assertEqual(
            jawa_barat["stats"]["events_without_kabupaten_kota"], 1
        )

    def test_kota_bogor_filter_updates_every_component(self):
        data = build_dashboard(
            filters=DashboardFilters(
                province="Jawa Barat",
                kabupaten="Kota Bogor",
            )
        )
        self.assertEqual(data["stats"]["total_events"], 3)
        self.assertEqual(data["stats"]["total_documents"], 3)
        self.assertEqual(data["stats"]["events_with_kabupaten_kota"], 3)
        self.assertEqual(
            [(item["province"], item["count"]) for item in data["regions"]["items"]],
            [("Jawa Barat", 3)],
        )
        self.assertEqual(
            sum(item["event_count"] for item in data["categories"]),
            3,
        )
        self.assertEqual(
            sum(point["count"] for point in data["trend"]["points"]),
            3,
        )
        self.assertEqual(len(data["latest_news"]), 3)
        self.assertTrue(
            all(
                row["relevance_status"] == "relevan"
                for row in data["latest_news"]
            )
        )

    def test_sukabumi_and_garut_filters_are_distinct(self):
        sukabumi = build_dashboard(
            filters=DashboardFilters(
                province="Jawa Barat",
                kabupaten="Kabupaten Sukabumi",
            )
        )
        garut = build_dashboard(
            filters=DashboardFilters(
                province="Jawa Barat",
                kabupaten="Kabupaten Garut",
            )
        )
        self.assertEqual(sukabumi["stats"]["total_events"], 2)
        self.assertEqual(sukabumi["stats"]["total_documents"], 2)
        self.assertEqual(garut["stats"]["total_events"], 1)
        self.assertEqual(garut["stats"]["total_documents"], 1)
        self.assertNotEqual(
            {row["document_id"] for row in sukabumi["latest_news"]},
            {row["document_id"] for row in garut["latest_news"]},
        )

    def test_province_without_kabupaten_still_returns_events(self):
        banten = build_dashboard(filters=DashboardFilters(province="Banten"))
        self.assertEqual(banten["stats"]["total_events"], 1)
        self.assertEqual(banten["stats"]["total_documents"], 1)
        self.assertEqual(banten["stats"]["events_with_kabupaten_kota"], 0)
        self.assertEqual(banten["stats"]["events_without_kabupaten_kota"], 1)
        self.assertEqual(
            banten["options"]["kabupaten_by_province"]["Banten"],
            [],
        )

        nusa_tenggara_barat = build_dashboard(
            filters=DashboardFilters(province="Nusa Tenggara Barat")
        )
        self.assertEqual(nusa_tenggara_barat["stats"]["total_events"], 1)
        self.assertEqual(
            nusa_tenggara_barat["options"]["kabupaten_by_province"][
                "Nusa Tenggara Barat"
            ],
            [],
        )

    def test_kabupaten_filter_combines_with_category_and_date(self):
        bogor_quake = build_dashboard(
            filters=DashboardFilters(
                category="Gempabumi",
                province="Jawa Barat",
                kabupaten="Kota Bogor",
            )
        )
        self.assertEqual(bogor_quake["stats"]["total_events"], 3)
        self.assertEqual(bogor_quake["stats"]["total_documents"], 3)

        bogor_october = build_dashboard(
            filters=DashboardFilters(
                province="Jawa Barat",
                kabupaten="Kota Bogor",
                date_from="2026-10-01",
                date_to="2026-10-31",
            )
        )
        self.assertEqual(bogor_october["stats"]["total_events"], 3)
        self.assertEqual(bogor_october["stats"]["total_documents"], 3)

        jabar_volcano = build_dashboard(
            filters=DashboardFilters(
                category="Gunungapi",
                province="Jawa Barat",
            )
        )
        self.assertEqual(jabar_volcano["stats"]["total_events"], 0)
        self.assertEqual(jabar_volcano["stats"]["total_documents"], 0)
        self.assertEqual(jabar_volcano["latest_news"], [])

    def test_unknown_province_with_kabupaten_is_rejected(self):
        with self.assertRaises(ValueError):
            build_dashboard(
                filters=DashboardFilters(
                    province=UNKNOWN_PROVINCE,
                    kabupaten="Kota Bogor",
                )
            )

    def test_kabupaten_documents_follow_event_links(self):
        data = build_dashboard(
            filters=DashboardFilters(
                province="Jawa Barat",
                kabupaten="Kota Bogor",
            )
        )
        with closing(connect(DEFAULT_DB_PATH)) as connection:
            linked = connection.execute(
                """
                SELECT COUNT(DISTINCT d.document_id)
                FROM document d
                JOIN document_relevance dr ON dr.document_id = d.document_id
                JOIN document_event_link l ON l.document_id = d.document_id
                JOIN event_location el ON el.event_id = l.event_id
                WHERE d.document_status = 'active'
                  AND dr.relevance_status = 'relevan'
                  AND l.link_status = 'active'
                  AND el.admin_kabupaten_kota = 'Kota Bogor'
                  AND NOT EXISTS (
                      SELECT 1 FROM document_duplicate dd
                      WHERE dd.document_id = d.document_id
                  )
                """
            ).fetchone()[0]
        self.assertEqual(data["stats"]["total_documents"], linked)

    def test_parse_filters_accepts_kabupaten_aliases(self):
        filters = parse_filters(
            {
                "province": "Jawa Barat",
                "kabupaten": "Kota Bogor",
            }
        )
        self.assertEqual(filters.province, "Jawa Barat")
        self.assertEqual(filters.kabupaten, "Kota Bogor")

        alias = parse_filters(
            {
                "province": "Jawa Barat",
                "kabupaten_kota": "Kabupaten Sukabumi",
            }
        )
        self.assertEqual(alias.kabupaten, "Kabupaten Sukabumi")


class DashboardMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_data = build_dashboard()
        cls.map_data = cls.all_data["map"]
        cls.markers = cls.map_data["markers"]

    def _dashboard_for_coordinates(self, latitude, longitude):
        schema_path = Path(DEFAULT_DB_PATH).parents[1] / "database" / "schema.sql"
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "coords.db"
            connection = sqlite3.connect(db_path)
            connection.executescript(schema_path.read_text(encoding="utf-8"))
            connection.execute(
                """
                INSERT INTO event (
                    event_id, event_title, event_status,
                    event_verification_status, event_verification_level
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "EVT-TEST-COORDS",
                    "Kejadian uji koordinat",
                    "active",
                    "unverified",
                    "single_source",
                ),
            )
            connection.execute(
                """
                INSERT INTO event_location (
                    event_location_id, event_id, latitude, longitude,
                    is_inside_indonesia
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "LOC-TEST-COORDS",
                    "EVT-TEST-COORDS",
                    latitude,
                    longitude,
                    "tidak_diketahui",
                ),
            )
            connection.commit()
            connection.close()
            return build_dashboard(db_path=db_path)

    def test_map_markers_are_unique_and_have_valid_coordinates(self):
        ids = [marker["event_id"] for marker in self.markers]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(self.markers)
        for marker in self.markers:
            self.assertGreaterEqual(marker["latitude"], -90)
            self.assertLessEqual(marker["latitude"], 90)
            self.assertGreaterEqual(marker["longitude"], -180)
            self.assertLessEqual(marker["longitude"], 180)

    def test_map_stats_match_event_and_marker_counts(self):
        stats = self.map_data["stats"]
        self.assertEqual(stats["total_events"], 75)
        self.assertEqual(stats["events_with_coordinates"], 70)
        self.assertEqual(stats["events_without_coordinates"], 5)
        self.assertEqual(stats["marker_count"], 70)
        self.assertEqual(stats["markers_outside_indonesia"], 10)
        self.assertEqual(sum(stats["marker_categories"].values()), 70)
        self.assertEqual(stats["marker_categories"]["Gempabumi"], 66)
        self.assertEqual(stats["marker_categories"]["Lainnya"], 4)
        self.assertEqual(len(stats["marker_categories"]), 9)

    def test_events_without_coordinates_are_not_markers(self):
        ids = {marker["event_id"] for marker in self.markers}
        self.assertNotIn("EVT-LEGACY-95B7C1A7AA99", ids)
        self.assertNotIn("EVT-LEGACY-D2202EEA70E1", ids)
        self.assertNotIn("EVT-LEGACY-4E3E437E1577", ids)
        self.assertNotIn("EVT-LEGACY-68BCFA0712E1", ids)
        self.assertNotIn("EVT-LEGACY-EA332A1AF033", ids)

    def test_out_of_range_coordinates_are_ignored(self):
        data = self._dashboard_for_coordinates(999, 200)
        self.assertEqual(data["stats"]["total_events"], 1)
        self.assertEqual(data["map"]["markers"], [])
        self.assertEqual(data["map"]["stats"]["events_with_coordinates"], 0)
        self.assertEqual(data["map"]["stats"]["events_without_coordinates"], 1)

    def test_non_numeric_coordinates_are_ignored(self):
        data = self._dashboard_for_coordinates("bukan-angka", "bukan-angka")
        self.assertEqual(data["stats"]["total_events"], 1)
        self.assertEqual(data["map"]["markers"], [])
        self.assertEqual(data["map"]["stats"]["marker_count"], 0)

    def test_map_markers_include_relevant_supporting_documents(self):
        known = next(
            marker
            for marker in self.markers
            if marker["event_id"] == "EVT-LEGACY-5E8944F8DBE0"
        )
        self.assertEqual(known["document_count"], 1)
        self.assertEqual(len(known["documents"]), 1)
        self.assertTrue(known["documents"][0]["title"])
        self.assertTrue(known["documents"][0]["url"].startswith("http"))

    def test_markers_without_documents_stay_honest(self):
        without_documents = [
            marker for marker in self.markers if not marker["documents"]
        ]
        self.assertEqual(len(without_documents), 4)
        self.assertTrue(
            all(marker["document_count"] == 0 for marker in without_documents)
        )

    def test_map_markers_do_not_invent_unknown_region(self):
        marker = next(
            marker
            for marker in self.markers
            if marker["event_id"] == "EVT-BMKG-003786C08B87"
        )
        self.assertEqual(marker["province"], "")
        self.assertEqual(marker["kabupaten"], "")

    def test_jawa_barat_map_filter(self):
        data = build_dashboard(
            filters=DashboardFilters(province="Jawa Barat")
        )
        self.assertEqual(data["stats"]["total_events"], 7)
        self.assertEqual(data["map"]["stats"]["marker_count"], 6)
        self.assertEqual(data["map"]["stats"]["events_without_coordinates"], 1)
        self.assertTrue(
            all(
                marker["province"] == "Jawa Barat"
                for marker in data["map"]["markers"]
            )
        )

    def test_kota_bogor_map_filter(self):
        data = build_dashboard(
            filters=DashboardFilters(
                province="Jawa Barat",
                kabupaten="Kota Bogor",
            )
        )
        self.assertEqual(data["stats"]["total_events"], 3)
        self.assertEqual(data["map"]["stats"]["marker_count"], 3)
        self.assertTrue(
            all(
                marker["kabupaten"] == "Kota Bogor"
                for marker in data["map"]["markers"]
            )
        )

    def test_banten_map_filter(self):
        data = build_dashboard(filters=DashboardFilters(province="Banten"))
        self.assertEqual(data["stats"]["total_events"], 1)
        self.assertEqual(data["map"]["stats"]["marker_count"], 1)
        self.assertEqual(data["map"]["markers"][0]["province"], "Banten")

    def test_category_without_coordinates_returns_empty_map(self):
        data = build_dashboard(
            filters=DashboardFilters(category="Gunungapi")
        )
        self.assertEqual(data["stats"]["total_events"], 2)
        self.assertEqual(data["map"]["markers"], [])
        self.assertEqual(data["map"]["stats"]["marker_count"], 0)
        self.assertEqual(
            sum(data["map"]["stats"]["marker_categories"].values()),
            0,
        )

    def test_date_filter_limits_map_markers(self):
        data = build_dashboard(
            filters=DashboardFilters(
                date_from="2026-10-01",
                date_to="2026-10-31",
            )
        )
        self.assertEqual(data["map"]["stats"]["total_events"], 64)
        self.assertEqual(data["map"]["stats"]["marker_count"], 59)
        for marker in data["map"]["markers"]:
            self.assertTrue(marker["event_time"])
            self.assertGreaterEqual(marker["event_time"][:10], "2026-10-01")
            self.assertLessEqual(marker["event_time"][:10], "2026-10-31")

    def test_unknown_province_map_filter(self):
        data = build_dashboard(
            filters=DashboardFilters(province=UNKNOWN_PROVINCE)
        )
        self.assertEqual(data["stats"]["total_events"], 44)
        self.assertEqual(data["map"]["stats"]["marker_count"], 41)
        self.assertEqual(data["map"]["stats"]["events_without_coordinates"], 3)
        self.assertEqual(data["map"]["stats"]["markers_outside_indonesia"], 10)
        self.assertTrue(
            all(not marker["province"] for marker in data["map"]["markers"])
        )

    def test_invalid_province_kabupaten_combination_raises(self):
        with self.assertRaises(ValueError):
            build_dashboard(
                filters=DashboardFilters(
                    province="Banten",
                    kabupaten="Kota Bogor",
                )
            )

    def test_kabupaten_without_province_raises(self):
        with self.assertRaises(ValueError):
            build_dashboard(
                filters=DashboardFilters(kabupaten="Kota Bogor")
            )


class DashboardSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_data = search_news(filters=NewsSearchFilters(per_page=100))

    def test_search_returns_only_relevant_documents(self):
        self.assertEqual(self.all_data["pagination"]["total"], 84)
        self.assertEqual(len(self.all_data["results"]), 84)
        self.assertTrue(
            all(
                row["relevance_status"] == "relevan"
                for row in self.all_data["results"]
            )
        )

    def test_search_matches_title(self):
        data = search_news(
            filters=NewsSearchFilters(q="Ruteng", per_page=100)
        )
        self.assertEqual(data["pagination"]["total"], 6)
        self.assertTrue(
            any("Ruteng" in row["document_title"] for row in data["results"])
        )

    def test_search_matches_stored_content_and_linked_event_summary(self):
        data = search_news(
            filters=NewsSearchFilters(q="magnitudo", per_page=100)
        )
        self.assertEqual(data["pagination"]["total"], 29)
        self.assertTrue(
            any(
                "magnitudo" not in row["document_title"].casefold()
                for row in data["results"]
            )
        )

    def test_search_category_filter(self):
        data = search_news(
            filters=NewsSearchFilters(category="Gunungapi", per_page=100)
        )
        self.assertEqual(data["pagination"]["total"], 5)
        self.assertTrue(
            all(row["category"] == "Gunungapi" for row in data["results"])
        )

    def test_search_source_filter(self):
        data = search_news(
            filters=NewsSearchFilters(source="ANTARA", per_page=100)
        )
        self.assertEqual(data["pagination"]["total"], 1)
        self.assertEqual(data["results"][0]["source"], "ANTARA")

    def test_search_date_filter_uses_publication_time(self):
        data = search_news(
            filters=NewsSearchFilters(
                date_from="2026-10-01",
                date_to="2026-10-31",
                per_page=100,
            )
        )
        self.assertEqual(data["pagination"]["total"], 46)
        for row in data["results"]:
            published = row["document_published_at"][:10]
            self.assertGreaterEqual(published, "2026-10-01")
            self.assertLessEqual(published, "2026-10-31")

    def test_search_excludes_irrelevant_documents(self):
        data = search_news(
            filters=NewsSearchFilters(
                q="Monyet Ekor Panjang",
                per_page=100,
            )
        )
        self.assertEqual(data["pagination"]["total"], 0)
        self.assertEqual(data["results"], [])

    def test_search_pagination_and_page_clamping(self):
        data = search_news(filters=NewsSearchFilters(page=2, per_page=5))
        self.assertEqual(data["pagination"]["total"], 84)
        self.assertEqual(data["pagination"]["pages"], 17)
        self.assertEqual(data["pagination"]["page"], 2)
        self.assertEqual(len(data["results"]), 5)
        self.assertTrue(data["pagination"]["has_prev"])
        self.assertTrue(data["pagination"]["has_next"])

        last_page = search_news(
            filters=NewsSearchFilters(page=999, per_page=10)
        )
        self.assertEqual(last_page["pagination"]["page"], 9)
        self.assertEqual(len(last_page["results"]), 4)
        self.assertFalse(last_page["pagination"]["has_next"])

    def test_search_source_options_and_date_bounds(self):
        sources = {
            item["source"]: item["count"]
            for item in self.all_data["options"]["sources"]
        }
        self.assertEqual(sum(sources.values()), 84)
        self.assertEqual(sources["BMKG"], 29)
        self.assertEqual(sources["ANTARA"], 1)
        self.assertEqual(
            self.all_data["options"]["date_bounds"],
            {"min": "2026-09-06", "max": "2026-10-19"},
        )

    def test_parse_search_filters_validates_and_clamps(self):
        filters = parse_search_filters(
            {
                "q": "  Gempa  ",
                "category": "Gempabumi",
                "source": "BMKG",
                "page": "2",
                "per_page": "999",
            }
        )
        self.assertEqual(filters.q, "Gempa")
        self.assertEqual(filters.category, "Gempabumi")
        self.assertEqual(filters.source, "BMKG")
        self.assertEqual(filters.page, 2)
        self.assertEqual(filters.per_page, 50)

        with self.assertRaises(ValueError):
            parse_search_filters({"page": "0"})
        with self.assertRaises(ValueError):
            parse_search_filters({"date_from": "2026-10-31", "date_to": "2026-10-01"})


class EventDetailTest(unittest.TestCase):
    def test_event_detail_includes_core_data_and_supporting_news(self):
        data = build_event_detail(event_id="EVT-LEGACY-5E8944F8DBE0")
        self.assertIsNotNone(data)
        event = data["event"]
        self.assertIn("Ruteng", event["event_title"])
        self.assertEqual(data["primary_category"], "Gempabumi")
        self.assertIsNotNone(data["time"])
        self.assertTrue(data["time"]["event_time"])
        self.assertTrue(data["locations"])
        self.assertEqual(
            data["locations"][0]["province"],
            "Nusa Tenggara Timur",
        )
        self.assertIsInstance(data["locations"][0]["latitude"], float)
        self.assertEqual(len(data["supporting_news"]), 1)
        news = data["supporting_news"][0]
        self.assertEqual(news["relevance_status"], "relevan")
        self.assertTrue(news["url"].startswith("http"))
        self.assertTrue(news["document_published_at"])

    def test_event_detail_stays_honest_without_supporting_news(self):
        data = build_event_detail(event_id="EVT-GDACS-DR1018545")
        self.assertIsNotNone(data)
        self.assertEqual(data["supporting_news"], [])
        self.assertEqual(data["locations"][0]["province"], "")
        self.assertEqual(data["locations"][0]["kabupaten"], "")
        self.assertIsNotNone(data["locations"][0]["latitude"])
        self.assertTrue(data["attributes"])
        self.assertTrue(data["event"]["event_summary"])

    def test_unknown_event_detail_returns_none(self):
        self.assertIsNone(build_event_detail(event_id="EVT-TIDAK-ADA"))
        self.assertIsNone(build_event_detail(event_id=""))


class DashboardHttpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_dashboard_page_and_api(self):
        with urlopen(f"{self.base_url}/", timeout=10) as response:
            html = response.read().decode("utf-8")
        self.assertIn("GeoHazard News Locator", html)
        self.assertIn("Kategori", html)

        with urlopen(
            f"{self.base_url}/api/dashboard?category=Gempabumi",
            timeout=10,
        ) as response:
            self.assertEqual(response.status, 200)
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["stats"]["total_events"], 68)
        self.assertEqual(payload["filters"]["category"], "Gempabumi")

        for path, content_type in (
            ("/static/app.js", "application/javascript"),
            ("/static/styles.css", "text/css"),
        ):
            with urlopen(f"{self.base_url}{path}", timeout=10) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(content_type, response.headers["Content-Type"])
                self.assertTrue(response.read())


    def test_kabupaten_filter_api_and_aliases(self):
        with urlopen(f"{self.base_url}/", timeout=10) as response:
            html = response.read().decode("utf-8")
        self.assertIn('id="kabupatenFilter"', html)
        self.assertIn('id="filterNotice"', html)

        with urlopen(
            f"{self.base_url}/api/dashboard?"
            "province=Jawa%20Barat&kabupaten=Kota%20Bogor",
            timeout=10,
        ) as response:
            self.assertEqual(response.status, 200)
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["stats"]["total_events"], 3)
        self.assertEqual(payload["stats"]["total_documents"], 3)
        self.assertEqual(payload["filters"]["province"], "Jawa Barat")
        self.assertEqual(payload["filters"]["kabupaten"], "Kota Bogor")

        with urlopen(
            f"{self.base_url}/api/dashboard?"
            "province=Jawa%20Barat&kabupaten_kota=Kabupaten%20Sukabumi",
            timeout=10,
        ) as response:
            alias = json.loads(response.read().decode("utf-8"))
        self.assertEqual(alias["stats"]["total_events"], 2)
        self.assertEqual(alias["filters"]["kabupaten"], "Kabupaten Sukabumi")

    def test_map_page_api_and_frontend_contract(self):
        with urlopen(f"{self.base_url}/", timeout=10) as response:
            html = response.read().decode("utf-8")
        self.assertIn("Peta Persebaran Bahaya Geologi Indonesia", html)
        self.assertIn('id="mapCanvas"', html)
        self.assertIn('id="mapStats"', html)
        self.assertIn('id="mapLegend"', html)
        self.assertIn("/static/vendor/leaflet/leaflet.js", html)
        self.assertIn(
            "/static/vendor/leaflet.markercluster/leaflet.markercluster.js",
            html,
        )

        with urlopen(f"{self.base_url}/api/dashboard", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["map"]["stats"]["marker_count"], 70)
        self.assertEqual(
            payload["map"]["stats"]["events_without_coordinates"],
            5,
        )
        self.assertTrue(payload["map"]["markers"])
        marker = payload["map"]["markers"][0]
        for key in (
            "event_id",
            "event_title",
            "category",
            "event_time",
            "province",
            "kabupaten",
            "latitude",
            "longitude",
            "document_count",
            "documents",
        ):
            self.assertIn(key, marker)

        with urlopen(f"{self.base_url}/static/app.js", timeout=10) as response:
            app_js = response.read().decode("utf-8")
        self.assertIn("Waktu kejadian belum diketahui", app_js)
        self.assertIn("Kabupaten/kota belum diketahui", app_js)

    def test_map_vendor_assets_are_served(self):
        for path, content_type in (
            (
                "/static/vendor/leaflet/leaflet.js",
                "application/javascript",
            ),
            ("/static/vendor/leaflet/leaflet.css", "text/css"),
            (
                "/static/vendor/leaflet.markercluster/leaflet.markercluster.js",
                "application/javascript",
            ),
            (
                "/static/vendor/leaflet.markercluster/MarkerCluster.css",
                "text/css",
            ),
        ):
            with urlopen(f"{self.base_url}{path}", timeout=10) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(content_type, response.headers["Content-Type"])
                self.assertTrue(response.read())

    def test_map_api_uses_region_filters(self):
        with urlopen(
            f"{self.base_url}/api/dashboard?"
            "province=Jawa%20Barat&kabupaten=Kota%20Bogor",
            timeout=10,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["map"]["stats"]["marker_count"], 3)
        self.assertEqual(payload["map"]["stats"]["total_events"], 3)
        self.assertTrue(
            all(
                marker["kabupaten"] == "Kota Bogor"
                for marker in payload["map"]["markers"]
            )
        )

    def test_invalid_region_combination_returns_400(self):
        for query in (
            "province=Banten&kabupaten=Kota%20Bogor",
            "kabupaten=Kota%20Bogor",
            "province=__unknown__&kabupaten=Kota%20Bogor",
        ):
            with self.assertRaises(HTTPError) as context:
                urlopen(f"{self.base_url}/api/dashboard?{query}", timeout=10)
            self.assertEqual(context.exception.code, 400)

    def test_invalid_filter_returns_400(self):
        with self.assertRaises(HTTPError) as context:
            urlopen(
                f"{self.base_url}/api/dashboard?date_from=2026-13-01",
                timeout=10,
            )
        self.assertEqual(context.exception.code, 400)

    def test_search_page_and_api_contract(self):
        with urlopen(f"{self.base_url}/", timeout=10) as response:
            html = response.read().decode("utf-8")
        self.assertIn('id="newsSearchForm"', html)
        self.assertIn('id="newsQuery"', html)
        self.assertIn('id="newsCategoryFilter"', html)
        self.assertIn('id="newsSourceFilter"', html)
        self.assertIn('id="searchResultsBody"', html)
        self.assertIn('id="searchError"', html)
        self.assertIn('id="searchPagination"', html)

        with urlopen(
            f"{self.base_url}/api/search?q=Gempa&per_page=5&page=2",
            timeout=10,
        ) as response:
            self.assertEqual(response.status, 200)
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["pagination"]["total"], 63)
        self.assertEqual(payload["pagination"]["page"], 2)
        self.assertEqual(len(payload["results"]), 5)
        self.assertTrue(
            all(
                row["relevance_status"] == "relevan"
                for row in payload["results"]
            )
        )
        self.assertTrue(payload["options"]["sources"])

    def test_search_invalid_filters_return_400(self):
        for query in (
            "date_from=2026-13-01",
            "date_from=2026-10-31&date_to=2026-10-01",
            "page=0",
            "per_page=0",
        ):
            with self.assertRaises(HTTPError) as context:
                urlopen(
                    f"{self.base_url}/api/search?{query}",
                    timeout=10,
                )
            self.assertEqual(context.exception.code, 400)

    def test_event_detail_page_and_api(self):
        event_id = "EVT-LEGACY-5E8944F8DBE0"
        with urlopen(
            f"{self.base_url}/event/{event_id}?province=Jawa%20Barat",
            timeout=10,
        ) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
            html = response.read().decode("utf-8")
        self.assertIn('id="eventTitle"', html)
        self.assertIn('id="supportingNewsBody"', html)
        self.assertIn("Belum ada berita relevan untuk kejadian ini.", html)
        self.assertIn("/static/event.js", html)

        with urlopen(
            f"{self.base_url}/api/events/{event_id}",
            timeout=10,
        ) as response:
            self.assertEqual(response.status, 200)
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["event"]["event_id"], event_id)
        self.assertEqual(payload["primary_category"], "Gempabumi")
        self.assertTrue(payload["locations"])
        self.assertTrue(payload["supporting_news"])
        self.assertEqual(
            payload["supporting_news"][0]["relevance_status"],
            "relevan",
        )

        with self.assertRaises(HTTPError) as context:
            urlopen(f"{self.base_url}/api/events/EVT-TIDAK-ADA", timeout=10)
        self.assertEqual(context.exception.code, 404)

    def test_fix10_frontend_contract(self):
        with urlopen(
            f"{self.base_url}/static/app.js",
            timeout=10,
        ) as response:
            app_js = response.read().decode("utf-8")
        self.assertIn("Lihat Detail Kejadian", app_js)
        self.assertNotIn("Lihat detail lengkap", app_js)
        self.assertIn("/api/search?", app_js)
        self.assertIn("newsSearchForm", app_js)
        self.assertIn("/event/${encodeURIComponent(marker.event_id)}", app_js)
        self.assertIn("const detailQuery = buildQuery();", app_js)
        self.assertIn("showSearchError", app_js)
        self.assertIn("window.location.hash", app_js)

        with urlopen(
            f"{self.base_url}/static/event.js",
            timeout=10,
        ) as response:
            self.assertEqual(response.status, 200)
            event_js = response.read().decode("utf-8")
        self.assertIn("/api/events/", event_js)
        self.assertIn("Waktu kejadian belum diketahui", event_js)


if __name__ == "__main__":
    unittest.main(verbosity=2)
