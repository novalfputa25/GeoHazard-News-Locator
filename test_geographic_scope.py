import tempfile
import unittest
from pathlib import Path

import geographic_scope as geo
from scripts import fix_geographic_scope as fix
from scripts import pilot_collect_official_geohazard as pilot


class GeographicScopeClassifierTest(unittest.TestCase):
    def test_indonesia_from_official_location_and_coordinate(self):
        result = geo.classify_location(
            "1 km BaratDaya TOMOHON-SULUT",
            1.31,
            124.83,
            "source_coordinate",
            "bmkg_gempa_terkini",
            "Gempa M5.3",
        )
        self.assertEqual(result["geographic_scope"], geo.INDONESIA)
        self.assertEqual(result["is_inside_indonesia"], "ya")
        self.assertFalse(result["requires_review"])

    def test_outside_from_foreign_marker_and_coordinate(self):
        result = geo.classify_location(
            "M 5.0 - 68 km WSW of San Juan del Sur, Nicaragua",
            11.2,
            -85.8,
            "source_coordinate",
            "usgs_m45",
            "Gempa di Indonesia",
        )
        self.assertEqual(result["geographic_scope"], geo.OUTSIDE_INDONESIA)
        self.assertEqual(result["is_inside_indonesia"], "tidak")

    def test_unknown_without_coordinate(self):
        result = geo.classify_location(
            "Pusat gempa berada di darat",
            "",
            "",
            "not_available",
            "bmkg_gempa_terkini",
            "Gempa M4",
        )
        self.assertEqual(result["geographic_scope"], geo.UNKNOWN)
        self.assertEqual(result["is_inside_indonesia"], "tidak_diketahui")
        self.assertTrue(result["requires_review"])

    def test_sea_is_unknown_without_national_boundary(self):
        result = geo.classify_location(
            "Pusat gempa berada di laut 13 km tenggara Bahodopi",
            -2.87,
            122.21,
            "source_coordinate",
            "bmkg_gempa_dirasakan",
            "Gempa M3.5",
        )
        self.assertEqual(result["geographic_scope"], geo.UNKNOWN)
        self.assertTrue(result["sea_marker"])

    def test_near_border_inside_toponym_but_outside_bbox_is_unknown(self):
        result = geo.classify_location(
            "153 km Tenggara OKSIBIL-PAPUAPGNGN",
            -5.45,
            141.9,
            "source_coordinate",
            "bmkg_gempa_terkini",
            "Gempa M6",
        )
        self.assertEqual(result["geographic_scope"], geo.UNKNOWN)
        self.assertIs(result["inside_pilot_bbox"], False)
        self.assertIn("papua", result["indonesia_toponyms"])

    def test_compass_timur_laut_is_not_sea_marker(self):
        result = geo.classify_location(
            "Pusat gempa berada di 20 km Timur Laut Kota Sorong",
            -0.72,
            131.38,
            "source_coordinate",
            "bmkg_gempa_dirasakan",
            "Gempa M3.7",
        )
        self.assertEqual(result["geographic_scope"], geo.INDONESIA)
        self.assertFalse(result["sea_marker"])

    def test_event_title_is_not_location_evidence(self):
        result = geo.classify_location(
            "M 5.0 - 68 km WSW of San Juan del Sur, Nicaragua",
            11.2,
            -85.8,
            "source_coordinate",
            "usgs_m45",
            "Gempa di Indonesia",
        )
        self.assertEqual(result["geographic_scope"], geo.OUTSIDE_INDONESIA)


@unittest.skipUnless(
    fix.latest_source_fix().is_dir(), "sumber FIX 02 tidak tersedia"
)
class GeographicScopeFixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = fix.latest_source_fix()
        cls.source_hashes = {
            path.name: pilot.sha256_file(path)
            for path in sorted((cls.source / "tables").glob("*.csv"))
        }
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp_dir.name) / "FIX-GEOGRAPHIC-SCOPE-TEST"
        cls.manifest = fix.write_fix(
            cls.source,
            cls.output,
            fix_id="FIX-GEOGRAPHIC-SCOPE-TEST",
            generated_at="2026-11-03T00:00:00+00:00",
        )
        cls.tables = fix.load_all_tables(cls.output)
        cls.locations = {
            row["event_id"]: row for row in cls.tables["event_location"]
        }
        cls.summary = pilot.read_csv(
            cls.output / "geographic_scope_summary.csv"
        )
        cls.summary_by_event = {
            row["event_id"]: row for row in cls.summary
        }

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_scope_counts_and_no_deleted_events(self):
        self.assertEqual(len(self.tables["event"]), 20)
        self.assertEqual(self.manifest["scope_counts_before"]["ya"], 19)
        self.assertEqual(self.manifest["scope_counts_before"]["tidak"], 1)
        self.assertEqual(self.manifest["scope_counts_after"]["ya"], 9)
        self.assertEqual(self.manifest["scope_counts_after"]["tidak"], 0)
        self.assertEqual(
            self.manifest["scope_counts_after"]["tidak_diketahui"], 11
        )
        self.assertEqual(self.manifest["counts"]["scope_changes"], 11)
        self.assertEqual(
            self.tables["event"][0]["event_id"],
            fix.load_all_tables(self.source)["event"][0]["event_id"],
        )

    def test_oksibil_is_unknown_not_forced_outside(self):
        row = self.locations["EVT-BMKG-72D9473D8378"]
        self.assertEqual(row["is_inside_indonesia"], "tidak_diketahui")
        self.assertIn("bbox_pilot", row["location_evidence"])
        self.assertIn(
            "Perlu verifikasi batas wilayah", row["location_notes"]
        )

    def test_source_coordinate_remains_unverified(self):
        for row in self.tables["event_location"]:
            with self.subTest(event=row["event_id"]):
                self.assertEqual(row["coordinate_status"], "source_coordinate")
                self.assertFalse(row["coordinate_verified_at"])
                self.assertFalse(row["coordinate_verified_by"])

    def test_fix02_relations_are_bit_identical(self):
        source_relations = fix.load_all_tables(self.source)["event_relation"]
        output_relations = self.tables["event_relation"]
        self.assertEqual(
            sorted(row["event_relation_id"] for row in source_relations),
            sorted(row["event_relation_id"] for row in output_relations),
        )
        self.assertTrue(
            fix.EXPECTED_RELATION_IDS.issubset(
                {row["event_relation_id"] for row in output_relations}
            )
        )
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.source, "event_relation")),
            pilot.sha256_file(fix.table_path(self.output, "event_relation")),
        )

    def test_category_and_event_tables_unchanged(self):
        self.assertTrue(
            self.manifest["checks"]["event_table_unchanged"]
        )
        self.assertTrue(
            self.manifest["checks"]["category_table_unchanged"]
        )
        self.assertTrue(
            self.manifest["checks"]["category_scope_unchanged"]
        )
        self.assertTrue(
            self.manifest["checks"]["event_relation_table_unchanged"]
        )
        self.assertTrue(self.manifest["checks"]["baseline_unchanged"])
        self.assertTrue(
            self.manifest["checks"]["raw_payload_files_unchanged"]
        )

    def test_category_scope_separate_from_geographic_scope(self):
        category = {
            row["event_id"]: row for row in self.tables["category"]
        }
        oksibil = self.locations["EVT-BMKG-72D9473D8378"]
        self.assertEqual(
            oksibil["is_inside_indonesia"], "tidak_diketahui"
        )
        self.assertEqual(category["EVT-BMKG-72D9473D8378"]["category_scope"], "in_scope")
        self.assertEqual(
            category["EVT-BMKG-72D9473D8378"]["category_name"], "Gempabumi"
        )

    def test_change_log_is_append_only_and_explains_each_change(self):
        source_change_log = fix.load_all_tables(self.source)["change_log"]
        output_change_log = self.tables["change_log"]
        new_rows = [
            row
            for row in output_change_log
            if row["changed_by"] == "system_fix_geographic_scope"
        ]
        self.assertEqual(len(new_rows), 11)
        self.assertEqual(
            len(output_change_log), len(source_change_log) + 11
        )
        self.assertEqual(output_change_log[: len(source_change_log)], source_change_log)
        for row in new_rows:
            with self.subTest(change=row["change_id"]):
                self.assertEqual(row["change_type"], "update")
                self.assertEqual(row["field_name"], "is_inside_indonesia")
                self.assertTrue(row["old_value"])
                self.assertTrue(row["new_value"])
                self.assertIn("basis=", row["change_reason"])
                self.assertIn("category_scope tidak diubah", row["change_reason"])

    def test_all_manifest_checks_pass(self):
        failed = [
            key
            for key, value in self.manifest["checks"].items()
            if not value
        ]
        self.assertEqual(failed, [])
        self.assertTrue(
            all(
                row["status"] in {"lulus", "perlu_review"}
                for row in self.manifest["validation"]
            )
        )

    def test_unknown_rows_have_evidence_and_review_flag(self):
        unknown = [
            row
            for row in self.summary
            if row["geographic_scope"] == "tidak_diketahui"
        ]
        self.assertEqual(len(unknown), 11)
        for row in unknown:
            with self.subTest(event=row["event_id"]):
                self.assertTrue(row["scope_basis"])
                self.assertTrue(row["scope_reason"])
                self.assertEqual(row["requires_review"], "True")

    def test_source_fix_is_not_mutated(self):
        after = {
            path.name: pilot.sha256_file(path)
            for path in sorted((self.source / "tables").glob("*.csv"))
        }
        self.assertEqual(self.source_hashes, after)

    def test_collector_scope_rule_accepts_fix_output(self):
        validation = pilot.validate(
            self.tables, pilot.load_register(), self.output
        )
        loc_rule = next(
            row for row in validation if row["rule_id"] == "R-LOC-05"
        )
        self.assertEqual(loc_rule["status"], "lulus")
        self.assertEqual(loc_rule["records_checked"], 20)


if __name__ == "__main__":
    unittest.main()
