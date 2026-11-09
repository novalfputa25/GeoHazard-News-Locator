import tempfile
import unittest
from pathlib import Path

import dataset_baseline
from scripts import fix_event_relation_candidates as fix
from scripts import pilot_collect_official_geohazard as pilot

EXPECTED_PAIRS = {
    "Tomohon": {
        "bmkg_event_id": "EVT-BMKG-5989CC896238",
        "usgs_event_id": "EVT-USGS-7000tuuy",
        "time_diff_seconds": 4,
        "distance_km": 22.232,
        "bmkg_magnitude": 5.3,
        "usgs_magnitude": 5.1,
        "bmkg_depth_km": 148.0,
        "usgs_depth_km": 196.65,
    },
    "Tanimbar": {
        "bmkg_event_id": "EVT-BMKG-8102A3842AA3",
        "usgs_event_id": "EVT-USGS-7000tusv",
        "time_diff_seconds": 1,
        "distance_km": 22.043,
        "bmkg_magnitude": 5.5,
        "usgs_magnitude": 5.1,
        "bmkg_depth_km": 130.0,
        "usgs_depth_km": 93.55,
    },
}


def read_table(base, name):
    return pilot.read_csv(fix.table_path(base, name))


@unittest.skipUnless(
    fix.latest_tsunami_fix().is_dir(), "FIX 01 sumber tidak tersedia"
)
class CandidatePairTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = fix.latest_tsunami_fix()
        cls.tables = fix.load_tables(cls.source)
        cls.pairs = fix.candidate_pairs(cls.tables)
        cls.pairs_by_label = {row["pair_label"]: row for row in cls.pairs}

    def test_exactly_two_expected_candidate_pairs(self):
        self.assertEqual(set(self.pairs_by_label), set(EXPECTED_PAIRS))
        self.assertEqual(len(self.pairs), 2)

    def test_pair_metrics_match_source_payload(self):
        for label, expected in EXPECTED_PAIRS.items():
            with self.subTest(label=label):
                pair = self.pairs_by_label[label]
                self.assertEqual(
                    pair["bmkg_event_id"], expected["bmkg_event_id"]
                )
                self.assertEqual(
                    pair["usgs_event_id"], expected["usgs_event_id"]
                )
                self.assertEqual(
                    pair["time_diff_seconds"],
                    expected["time_diff_seconds"],
                )
                self.assertAlmostEqual(
                    pair["distance_km"], expected["distance_km"], places=3
                )
                self.assertAlmostEqual(
                    pair["bmkg_magnitude"], expected["bmkg_magnitude"]
                )
                self.assertAlmostEqual(
                    pair["usgs_magnitude"], expected["usgs_magnitude"]
                )
                self.assertAlmostEqual(
                    pair["bmkg_depth_km"], expected["bmkg_depth_km"]
                )
                self.assertAlmostEqual(
                    pair["usgs_depth_km"], expected["usgs_depth_km"]
                )

    def test_assessment_is_likely_but_not_confirmed(self):
        for pair in self.pairs:
            with self.subTest(label=pair["pair_label"]):
                self.assertEqual(pair["assessment"], "likely_same_event")
                self.assertIn("bukan confirmed_same_event", pair["reason"])
                self.assertIn("tidak dilakukan merge", pair["reason"])
                self.assertIn("katalog independen", pair["reason"])

    def test_relation_rows_use_neutral_type_and_explicit_evidence(self):
        created_at = "2026-11-03T00:00:00+00:00"
        rows = fix.build_relation_rows(self.pairs, created_at)
        event_ids = {row["event_id"] for row in self.tables["event"]}
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({row["event_relation_id"] for row in rows}), 2)
        for row in rows:
            with self.subTest(relation=row["event_relation_id"]):
                self.assertEqual(row["event_relation_type"], "related_to")
                self.assertNotEqual(
                    row["event_relation_type"], "same_event"
                )
                self.assertEqual(
                    row["event_relation_confidence"], "medium"
                )
                self.assertEqual(row["created_at"], created_at)
                self.assertIn(row["from_event_id"], event_ids)
                self.assertIn(row["to_event_id"], event_ids)
                self.assertNotEqual(
                    row["from_event_id"], row["to_event_id"]
                )
                evidence = row["event_relation_evidence"]
                for token in [
                    "assessment=likely_same_event",
                    "candidate_duplicate=true",
                    "no_merge=true",
                    "confirmed_same_event=false",
                    "reason=",
                    "source_refs=",
                    "BMKG_DOC=",
                    "USGS_DOC=",
                    "BMKG_RAW=",
                    "USGS_RAW=",
                    "RAW_SHA256=",
                ]:
                    self.assertIn(token, evidence)


@unittest.skipUnless(
    fix.latest_tsunami_fix().is_dir(), "FIX 01 sumber tidak tersedia"
)
class EventRelationFixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = fix.latest_tsunami_fix()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = (
            Path(cls.tmp.name) / "FIX-EVENT-RELATION-TEST"
        )
        cls.generated_at = "2026-11-03T00:00:00+00:00"
        cls.source_event_hash = pilot.sha256_file(
            fix.table_path(cls.source, "event")
        )
        cls.source_raw_hash = pilot.sha256_file(
            fix.table_path(cls.source, "raw_payload")
        )
        cls.manifest = fix.write_fix(
            cls.source,
            cls.output,
            fix_id="FIX-EVENT-RELATION-TEST",
            generated_at=cls.generated_at,
        )
        cls.source_events = read_table(cls.source, "event")
        cls.output_events = read_table(cls.output, "event")
        cls.relations = read_table(cls.output, "event_relation")
        cls.source_changes = read_table(cls.source, "change_log")
        cls.output_changes = read_table(cls.output, "change_log")
        cls.summary = pilot.read_csv(
            cls.output / "event_relation_fix_summary.csv"
        )
        cls.validation = pilot.read_csv(
            cls.output / "event_relation_validation.csv"
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_both_events_remain_stored(self):
        self.assertEqual(len(self.output_events), 20)
        output_ids = {row["event_id"] for row in self.output_events}
        for expected in EXPECTED_PAIRS.values():
            self.assertIn(expected["bmkg_event_id"], output_ids)
            self.assertIn(expected["usgs_event_id"], output_ids)

    def test_event_ids_do_not_change(self):
        self.assertEqual(
            [row["event_id"] for row in self.source_events],
            [row["event_id"] for row in self.output_events],
        )
        self.assertEqual(
            {row["event_id"] for row in self.source_events},
            {row["event_id"] for row in self.output_events},
        )

    def test_relations_point_to_valid_events(self):
        event_ids = {row["event_id"] for row in self.output_events}
        self.assertEqual(len(self.relations), 2)
        for relation in self.relations:
            with self.subTest(relation=relation["event_relation_id"]):
                self.assertIn(relation["from_event_id"], event_ids)
                self.assertIn(relation["to_event_id"], event_ids)
                self.assertNotEqual(
                    relation["from_event_id"],
                    relation["to_event_id"],
                )
        actual_pairs = {
            (row["from_event_id"], row["to_event_id"])
            for row in self.relations
        }
        expected_pairs = {
            (row["bmkg_event_id"], row["usgs_event_id"])
            for row in EXPECTED_PAIRS.values()
        }
        self.assertEqual(actual_pairs, expected_pairs)

    def test_no_event_is_deleted(self):
        self.assertTrue(
            {row["event_id"] for row in self.output_events}.issuperset(
                {row["event_id"] for row in self.source_events}
            )
        )
        self.assertEqual(
            len(self.output_events), len(self.source_events)
        )
        self.assertEqual(self.manifest["checks"]["no_event_deleted"], True)

    def test_no_automatic_merge(self):
        self.assertEqual(self.source_events, self.output_events)
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.output, "event")),
            self.source_event_hash,
        )
        self.assertTrue(
            all(not row["event_group_id"] for row in self.output_events)
        )
        self.assertEqual(self.manifest["checks"]["no_merge"], True)
        self.assertEqual(
            self.manifest["counts"]["events_before"],
            self.manifest["counts"]["events_after"],
        )

    def test_relations_have_evidence_and_reason(self):
        self.assertEqual(len(self.summary), 2)
        for row in self.relations:
            with self.subTest(relation=row["event_relation_id"]):
                self.assertTrue(row["event_relation_evidence"])
                self.assertIn(
                    "assessment=likely_same_event",
                    row["event_relation_evidence"],
                )
                self.assertIn("reason=", row["event_relation_evidence"])
                self.assertIn("source_refs=", row["event_relation_evidence"])
                self.assertIn(
                    "caveat=", row["event_relation_evidence"]
                )
        for row in self.summary:
            with self.subTest(pair=row["pair_label"]):
                self.assertTrue(row["reason"])
                self.assertEqual(row["assessment"], "likely_same_event")
                self.assertEqual(row["relation_type"], "related_to")
                self.assertEqual(row["relation_confidence"], "medium")

    def test_baseline_is_unchanged(self):
        metadata = dataset_baseline.verify_dataset()
        self.assertEqual(metadata["sha256"], dataset_baseline.DATASET_SHA256)
        self.assertTrue(self.manifest["checks"]["baseline_unchanged"])
        self.assertEqual(
            self.manifest["baseline_before"]["sha256"],
            self.manifest["baseline_after"]["sha256"],
        )
        self.assertEqual(
            self.manifest["baseline_after"]["sha256"],
            dataset_baseline.DATASET_SHA256,
        )

    def test_raw_payload_is_unchanged(self):
        self.assertEqual(
            self.manifest["raw_payload_before"],
            self.manifest["raw_payload_after"],
        )
        self.assertTrue(
            self.manifest["checks"]["raw_payload_files_unchanged"]
        )
        self.assertTrue(
            self.manifest["checks"]["raw_payload_table_unchanged"]
        )
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.output, "raw_payload")),
            self.source_raw_hash,
        )
        for row in read_table(self.output, "raw_payload"):
            path = fix.ROOT / row["raw_payload_path"]
            self.assertTrue(path.is_file())
            self.assertEqual(
                pilot.sha256_file(path), row["raw_payload_sha256"]
            )

    def test_change_log_records_only_relation_creates(self):
        self.assertEqual(
            len(self.output_changes), len(self.source_changes) + 2
        )
        new_rows = [
            row
            for row in self.output_changes
            if row["target_type"] == "event_relation"
        ]
        self.assertEqual(len(new_rows), 2)
        for row in new_rows:
            with self.subTest(change=row["change_id"]):
                self.assertEqual(row["change_type"], "create")
                self.assertIn(
                    row["target_id"],
                    {relation["event_relation_id"] for relation in self.relations},
                )
                self.assertIn("tanpa merge", row["change_reason"])
                self.assertEqual(row["schema_version"], pilot.SCHEMA_VERSION)

    def test_relation_validation_passes(self):
        self.assertEqual(
            [row["rule_id"] for row in self.validation],
            ["R-REL-01", "R-REL-02", "R-REL-03"],
        )
        self.assertTrue(
            all(row["status"] == "lulus" for row in self.validation)
        )
        self.assertTrue(
            self.manifest["checks"]["relation_validation_no_p0"]
        )

    def test_manifest_checks_all_pass(self):
        self.assertTrue(all(self.manifest["checks"].values()))
        self.assertFalse(self.manifest["schema_changes"]["applied"])

    def test_source_fix_is_not_mutated(self):
        self.assertEqual(
            len(read_table(self.source, "event_relation")), 0
        )
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.source, "event")),
            self.source_event_hash,
        )
        self.assertEqual(
            pilot.sha256_file(fix.table_path(self.source, "raw_payload")),
            self.source_raw_hash,
        )


class PersistedEventRelationFixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = fix.latest_event_relation_fix()

    @unittest.skipUnless(
        fix.latest_event_relation_fix() is not None,
        "Output FIX-EVENT-RELATION belum dihasilkan",
    )
    def test_persisted_fix_keeps_events_and_has_two_relations(self):
        events = read_table(self.output, "event")
        relations = read_table(self.output, "event_relation")
        self.assertEqual(len(events), 20)
        self.assertEqual(len(relations), 2)
        event_ids = {row["event_id"] for row in events}
        for relation in relations:
            self.assertIn(relation["from_event_id"], event_ids)
            self.assertIn(relation["to_event_id"], event_ids)
            self.assertEqual(
                relation["event_relation_type"], "related_to"
            )


if __name__ == "__main__":
    unittest.main()
