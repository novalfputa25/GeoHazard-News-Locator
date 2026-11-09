import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from geohazard_pipeline.baseline_import import build_baseline_rows
from geohazard_pipeline.db import (
    connect,
    import_baseline,
    import_run_dir,
    initialize_database,
)
from geohazard_pipeline.util import ROOT
from scripts import fix06_materialize_supporting_documents as fix06

RUN_DIR = ROOT / "data" / "pipeline" / "RUN-20261103T160737Z"


class Fix06SupportingDocumentsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temp.name) / "fix06.db"
        initialize_database(cls.database)
        import_baseline(cls.database, build_baseline_rows(), initialize=False)
        import_run_dir(cls.database, RUN_DIR, initialize=False)
        cls.before = cls.snapshot()
        cls.result1 = fix06.apply_fix06(database=cls.database)
        cls.after1 = cls.snapshot()
        cls.result2 = fix06.apply_fix06(database=cls.database)
        cls.after2 = cls.snapshot()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def snapshot(cls):
        with closing(connect(cls.database)) as connection:
            counts = {}
            for table in (
                "document",
                "document_event_link",
                "event",
                "raw_payload",
                "document_classification",
                "event_assertion",
                "location_mention",
                "import_log",
            ):
                counts[table] = connection.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
            event_ids = sorted(
                row[0]
                for row in connection.execute("SELECT event_id FROM event")
            )
        return {"counts": counts, "event_ids": event_ids}

    def rows(self, sql, args=()):
        with closing(connect(self.database)) as connection:
            return [dict(row) for row in connection.execute(sql, args)]

    def test_missing_document_and_supporting_link_are_materialized(self):
        self.assertEqual(
            self.after1["counts"]["document"],
            self.before["counts"]["document"] + 1,
        )
        self.assertEqual(
            self.after1["counts"]["document_event_link"],
            self.before["counts"]["document_event_link"] + 1,
        )
        self.assertEqual(self.result1["inserted"].get("document"), 1)
        self.assertEqual(
            self.result1["inserted"].get("document_event_link"), 1
        )

    def test_all_three_targets_have_supporting_links(self):
        for target in fix06.TARGETS:
            documents = self.rows(
                "SELECT * FROM document WHERE document_id = ?",
                (target["document_id"],),
            )
            self.assertEqual(len(documents), 1, target["label"])
            document = documents[0]
            self.assertEqual(
                document["document_external_id"], target["external_id"]
            )
            self.assertEqual(document["document_source_id"], fix06.SOURCE_ID)
            self.assertEqual(document["document_status"], "active")
            self.assertTrue(document["document_raw_payload_id"])

            links = self.rows(
                "SELECT * FROM document_event_link "
                "WHERE document_id = ? AND event_id = ?",
                (target["document_id"], target["event_id"]),
            )
            self.assertEqual(len(links), 1, target["label"])
            link = links[0]
            self.assertEqual(link["relevance"], "supporting")
            self.assertEqual(link["is_primary"], "tidak")
            self.assertEqual(link["link_status"], "active")

    def test_no_duplicate_target_documents_or_links(self):
        for target in fix06.TARGETS:
            documents = self.rows(
                "SELECT COUNT(*) AS total FROM document "
                "WHERE document_external_id = ?",
                (target["external_id"],),
            )
            self.assertEqual(documents[0]["total"], 1)
            links = self.rows(
                "SELECT COUNT(*) AS total FROM document_event_link "
                "WHERE document_id = ? AND event_id = ?",
                (target["document_id"], target["event_id"]),
            )
            self.assertEqual(links[0]["total"], 1)

    def test_no_event_is_created_or_changed(self):
        self.assertEqual(
            self.after1["counts"]["event"],
            self.before["counts"]["event"],
        )
        self.assertEqual(self.after1["event_ids"], self.before["event_ids"])
        for target in fix06.TARGETS:
            events = self.rows(
                "SELECT event_id FROM event WHERE event_id = ?",
                (target["event_id"],),
            )
            self.assertEqual(len(events), 1)

    def test_target_auxiliary_rows_are_consistent_with_pipeline(self):
        for target in fix06.TARGETS:
            classifications = self.rows(
                "SELECT * FROM document_classification WHERE document_id = ?",
                (target["document_id"],),
            )
            self.assertEqual(len(classifications), 1)
            assertions = self.rows(
                "SELECT * FROM event_assertion "
                "WHERE document_id = ? AND event_id = ?",
                (target["document_id"], target["event_id"]),
            )
            self.assertGreater(len(assertions), 0)
            mentions = self.rows(
                "SELECT * FROM location_mention "
                "WHERE document_id = ? AND linked_event_id = ?",
                (target["document_id"], target["event_id"]),
            )
            self.assertGreater(len(mentions), 0)

    def test_raw_payload_provenance_is_valid(self):
        for target in fix06.TARGETS:
            documents = self.rows(
                "SELECT * FROM document WHERE document_id = ?",
                (target["document_id"],),
            )
            raw_id = documents[0]["document_raw_payload_id"]
            raw_rows = self.rows(
                "SELECT * FROM raw_payload WHERE raw_payload_id = ?",
                (raw_id,),
            )
            self.assertEqual(len(raw_rows), 1)
            raw = raw_rows[0]
            path = ROOT / raw["raw_payload_path"]
            self.assertTrue(path.is_file(), raw["raw_payload_path"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                raw["raw_payload_sha256"],
            )

    def test_second_run_is_idempotent(self):
        self.assertEqual(self.result2["inserted"], {})
        self.assertEqual(self.after2["counts"], self.after1["counts"])
        self.assertEqual(self.after2["event_ids"], self.after1["event_ids"])

    def test_baseline_and_foreign_keys_remain_valid(self):
        with closing(connect(self.database)) as connection:
            self.assertEqual(
                list(connection.execute("PRAGMA foreign_key_check")), []
            )
        self.assertEqual(self.result1["baseline_before"]["rows"], 787)
        self.assertEqual(self.result1["baseline_after"]["rows"], 787)
        self.assertEqual(self.result1["baseline_after"]["columns"], 51)
        self.assertEqual(
            self.result1["baseline_before"]["sha256"],
            self.result1["baseline_after"]["sha256"],
        )
        self.assertTrue(all(self.result1["checks"].values()))

    def test_dry_run_rolls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "dry-run.db"
            initialize_database(database)
            import_baseline(database, build_baseline_rows(), initialize=False)
            import_run_dir(database, RUN_DIR, initialize=False)
            with closing(connect(database)) as connection:
                before = connection.execute(
                    "SELECT COUNT(*) FROM document"
                ).fetchone()[0]
                links_before = connection.execute(
                    "SELECT COUNT(*) FROM document_event_link"
                ).fetchone()[0]
            result = fix06.apply_fix06(database=database, dry_run=True)
            with closing(connect(database)) as connection:
                after = connection.execute(
                    "SELECT COUNT(*) FROM document"
                ).fetchone()[0]
                links_after = connection.execute(
                    "SELECT COUNT(*) FROM document_event_link"
                ).fetchone()[0]
            self.assertTrue(result["dry_run"])
            self.assertEqual(before, after)
            self.assertEqual(links_before, links_after)


if __name__ == "__main__":
    unittest.main()
