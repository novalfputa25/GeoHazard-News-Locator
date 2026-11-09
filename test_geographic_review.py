import json
import tempfile
import unittest
from pathlib import Path

from scripts import fix_geographic_review as fix
from scripts import pilot_collect_official_geohazard as pilot


@unittest.skipUnless(
    fix.latest_source_fix().is_dir(), "sumber FIX 03 tidak tersedia"
)
class GeographicReviewFixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = fix.latest_source_fix()
        cls.source_hashes = {
            path.name: pilot.sha256_file(path)
            for path in sorted((cls.source / "tables").glob("*.csv"))
        }
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp_dir.name) / "FIX-GEOGRAPHIC-REVIEW-TEST"
        cls.manifest = fix.write_fix(
            cls.source,
            cls.output,
            fix_id="FIX-GEOGRAPHIC-REVIEW-TEST",
            generated_at="2026-11-03T00:00:00+00:00",
        )
        cls.tables = fix.load_all_tables(cls.output)
        cls.locations = {
            row["event_id"]: row for row in cls.tables["event_location"]
        }
        cls.reviews = {
            row["event_id"]: row
            for row in pilot.read_csv(cls.output / "geographic_review.csv")
        }
        cls.evidence = {
            row["event_id"]: row
            for row in json.loads(
                (cls.output / "geographic_review_evidence.json").read_text(
                    encoding="utf-8"
                )
            )
        }

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_all_eleven_unknown_events_reviewed_without_status_change(self):
        expected = {
            "EVT-BMKG-8102A3842AA3",
            "EVT-BMKG-9926ADFBE909",
            "EVT-BMKG-72D9473D8378",
            "EVT-BMKG-FFB357F335AE",
            "EVT-BMKG-8F1F74FF387A",
            "EVT-BMKG-9C6C2E535D8B",
            "EVT-BMKG-608A37F640B2",
            "EVT-BMKG-43C1A2818383",
            "EVT-BMKG-B2A5A39AE099",
            "EVT-BMKG-FC99150BA61F",
            "EVT-USGS-7000tusv",
        }
        self.assertEqual(set(self.reviews), expected)
        self.assertEqual(len(self.reviews), 11)
        for event_id, row in self.reviews.items():
            with self.subTest(event=event_id):
                self.assertEqual(row["old_is_inside_indonesia"], "tidak_diketahui")
                self.assertEqual(row["review_decision"], "tidak_diketahui")
                self.assertEqual(row["new_is_inside_indonesia"], "tidak_diketahui")
                self.assertEqual(row["status_changed"], "False")
                self.assertFalse(row["change_id"])
                self.assertEqual(row["manual_review"], "ya")

    def test_scope_changes_and_change_log_are_zero(self):
        self.assertEqual(
            self.manifest["scope_counts_before"],
            {"ya": 9, "tidak": 0, "tidak_diketahui": 11},
        )
        self.assertEqual(
            self.manifest["scope_counts_after"],
            {"ya": 9, "tidak": 0, "tidak_diketahui": 11},
        )
        self.assertEqual(
            self.manifest["review_decision_counts"],
            {"ya": 0, "tidak": 0, "tidak_diketahui": 11},
        )
        self.assertEqual(self.manifest["counts"]["status_changes"], 0)
        self.assertEqual(self.manifest["counts"]["remaining_unknown"], 11)
        source_changes = fix.load_all_tables(self.source)["change_log"]
        output_changes = self.tables["change_log"]
        self.assertEqual(output_changes, source_changes)
        self.assertFalse(
            any(
                row["changed_by"] == "system_fix_geographic_review"
                for row in output_changes
            )
        )
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.output, "change_log")),
            pilot.sha256_file(fix.table_path(self.source, "change_log")),
        )

    def test_evidence_covers_unlinked_supporting_bmkg_payloads(self):
        oksibil = self.reviews["EVT-BMKG-72D9473D8378"]
        self.assertEqual(oksibil["land_sea_evidence"], "darat")
        self.assertIn(
            "di darat 153 km tenggara Oksibil",
            oksibil["raw_location_statement"],
        )
        self.assertIn("III Boven Digoel", oksibil["raw_felt_statement"])

        ffb = self.reviews["EVT-BMKG-FFB357F335AE"]
        self.assertEqual(ffb["land_sea_evidence"], "laut")
        self.assertIn(
            "di laut 60 km Baratlaut Larat",
            ffb["raw_location_statement"],
        )

        gunungkidul = self.reviews["EVT-BMKG-608A37F640B2"]
        self.assertEqual(gunungkidul["land_sea_evidence"], "laut")
        self.assertEqual(
            gunungkidul["review_basis"],
            "episentrum_laut_tanpa_batas_nasional",
        )
        self.assertEqual(gunungkidul["review_confidence"], "high")
        self.assertIn(
            "di laut 137 km Selatan Gunungkidul",
            gunungkidul["raw_location_statement"],
        )

        for event_id in (
            "EVT-BMKG-72D9473D8378",
            "EVT-BMKG-FFB357F335AE",
            "EVT-BMKG-608A37F640B2",
        ):
            with self.subTest(event=event_id):
                raw_ids = self.reviews[event_id]["evidence_raw_payload_ids"]
                self.assertIn(
                    "RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264",
                    raw_ids,
                )
                self.assertEqual(len(self.evidence[event_id]["raw_records"]), 2)

    def test_review_evidence_is_complete_and_event_title_is_not_evidence(self):
        for event_id, row in self.reviews.items():
            with self.subTest(event=event_id):
                self.assertTrue(row["raw_location_statement"])
                self.assertTrue(row["evidence_document_ids"])
                self.assertTrue(row["evidence_raw_payload_ids"])
                self.assertTrue(row["review_basis"])
                self.assertTrue(row["review_rationale"])
                self.assertEqual(row["caveat"], fix.CAVEAT)
                self.assertFalse(
                    self.evidence[event_id][
                        "event_title_used_as_location_evidence"
                    ]
                )

    def test_no_change_to_event_location_or_other_tables(self):
        self.assertEqual(self.source_hashes, {
            path.name: pilot.sha256_file(path)
            for path in sorted((self.output / "tables").glob("*.csv"))
        })
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.output, "event_location")),
            "3632c2fa22a1c399a2b6d407b6e9d39a501ee4bea1b2b9bf71aeff8aa96b59e9",
        )
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.output, "event")),
            "dbfa6d732e5b66bd92adc783608e844b7b4c4ec471be3d0fd13db77cb51e4eff",
        )
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.output, "event_relation")),
            "f5b8c497a2ddae8b82351de385c219148a91716a7c9c94f888d8e8f7fb702eae",
        )

    def test_category_and_relations_are_preserved(self):
        categories = {
            row["event_id"]: row for row in self.tables["category"]
        }
        for event_id in self.reviews:
            with self.subTest(event=event_id):
                self.assertEqual(categories[event_id]["category_name"], "Gempabumi")
                self.assertEqual(categories[event_id]["category_scope"], "in_scope")
        self.assertEqual(len(self.tables["event_relation"]), 2)
        self.assertTrue(
            fix.EXPECTED_RELATION_IDS.issubset(
                {
                    row["event_relation_id"]
                    for row in self.tables["event_relation"]
                }
            )
        )

    def test_source_coordinate_remains_unverified(self):
        for row in self.tables["event_location"]:
            with self.subTest(event=row["event_id"]):
                self.assertEqual(row["coordinate_status"], "source_coordinate")
                self.assertFalse(row["coordinate_verified_at"])
                self.assertFalse(row["coordinate_verified_by"])

    def test_all_manifest_checks_and_validation_pass(self):
        failed = [
            key
            for key, value in self.manifest["checks"].items()
            if not value
        ]
        self.assertEqual(failed, [])
        self.assertTrue(self.manifest["checks"]["validation_no_failures"])
        self.assertTrue(
            all(
                row["status"] == "lulus"
                for row in self.manifest["validation"]
            )
        )
        self.assertEqual(
            [
                row["rule_id"]
                for row in self.manifest["validation"]
            ],
            ["R-GEO-07", "R-GEO-08", "R-GEO-09", "R-GEO-10", "R-GEO-11", "R-LOC-05"],
        )

    def test_collector_rule_accepts_fix_output(self):
        validation = pilot.validate(
            self.tables, pilot.load_register(), self.output
        )
        loc_rule = next(
            row for row in validation if row["rule_id"] == "R-LOC-05"
        )
        self.assertEqual(loc_rule["status"], "lulus")
        self.assertEqual(loc_rule["records_checked"], 20)

    def test_source_fix_is_not_mutated(self):
        after = {
            path.name: pilot.sha256_file(path)
            for path in sorted((self.source / "tables").glob("*.csv"))
        }
        self.assertEqual(self.source_hashes, after)


if __name__ == "__main__":
    unittest.main()
