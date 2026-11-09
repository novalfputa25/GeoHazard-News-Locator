import csv
import sqlite3
import tempfile
from contextlib import closing
import unittest
from pathlib import Path

from geohazard_pipeline.baseline_import import build_baseline_rows
from geohazard_pipeline.db import import_baseline, import_run_dir, initialize_database
from geohazard_pipeline.runner import run_pipeline
from geohazard_pipeline.util import ROOT

RAW_DIR = ROOT / "data" / "pilot" / "runs" / "PILOT-20261102T110641Z" / "raw"
FIX05_EVENTS = {
    "EVT-BMKG-72D9473D8378",
    "EVT-BMKG-FFB357F335AE",
    "EVT-BMKG-608A37F640B2",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class BaselineImportTest(unittest.TestCase):
    def test_baseline_rows_are_legacy_candidates(self):
        tables = build_baseline_rows()
        self.assertEqual(len(tables["document"]), 787)
        self.assertEqual(len(tables["event"]), 45)
        self.assertEqual(len(tables["event_time"]), 45)
        self.assertEqual(len(tables["document_event_link"]), 45)
        for document in tables["document"]:
            self.assertEqual(
                document["document_source_identity_status"], "legacy_label_only"
            )
            self.assertEqual(document["document_source_id"], "")
        for event in tables["event"]:
            self.assertEqual(event["event_status"], "candidate")
            self.assertEqual(event["event_verification_status"], "unverified")
        for category in tables["category"]:
            self.assertIn(
                category["category_name"],
                {
                    "Gunungapi",
                    "Gempabumi",
                    "Tsunami",
                    "Gerakan Tanah/Tanah Longsor",
                    "Likuefaksi",
                    "Abrasi dan Akresi",
                    "Penurunan Muka Tanah",
                    "Semburan Gas dan Lumpur",
                },
            )


class PipelineStage12Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.temp_root = Path(cls.temp.name)
        cls.manifest = run_pipeline(
            output_root=cls.temp_root / "runs",
            raw_dir=RAW_DIR,
            sources=[
                "bmkg_autogempa",
                "bmkg_gempa_terkini",
                "bmkg_gempa_dirasakan",
                "usgs_m45",
            ],
            max_items=100,
            run_id="RUN-TEST-STAGE12",
        )
        cls.run_dir = Path(cls.manifest["run_dir"])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_offline_run_materializes_all_dirasakan_records(self):
        documents = read_csv(self.run_dir / "tables" / "document.csv")
        by_source = {}
        for document in documents:
            by_source.setdefault(document["document_source_id"], []).append(document)
        self.assertEqual(len(by_source["bmkg_gempa_dirasakan"]), 15)
        self.assertEqual(len(by_source["bmkg_gempa_terkini"]), 15)
        self.assertEqual(len(documents), 33)

    def test_fix05_records_link_to_existing_events(self):
        links = read_csv(self.run_dir / "tables" / "document_event_link.csv")
        documents = {
            row["document_id"]: row
            for row in read_csv(self.run_dir / "tables" / "document.csv")
        }
        linked = {
            link["event_id"]
            for link in links
            if documents[link["document_id"]]["document_source_id"]
            == "bmkg_gempa_dirasakan"
        }
        self.assertTrue(FIX05_EVENTS.issubset(linked))
        for event_id in FIX05_EVENTS:
            event_links = [link for link in links if link["event_id"] == event_id]
            self.assertEqual(len(event_links), 2)
            self.assertEqual(
                sum(link["is_primary"] == "ya" for link in event_links), 1
            )

    def test_manifest_preserves_baseline_and_has_no_network_issue(self):
        self.assertEqual(self.manifest["baseline"]["rows"], 787)
        self.assertEqual(self.manifest["issues"], [])
        self.assertTrue((self.run_dir / "manifest.json").is_file())

    def test_sqlite_import_is_idempotent(self):
        database = self.temp_root / "stage12.db"
        initialize_database(database)
        baseline = build_baseline_rows()
        import_baseline(database, baseline, initialize=False)
        first = import_run_dir(database, self.run_dir, initialize=False)
        second = import_run_dir(database, self.run_dir, initialize=False)
        self.assertEqual(first["foreign_key_check"], [])
        self.assertEqual(second["foreign_key_check"], [])
        with closing(sqlite3.connect(database)) as connection:
            document_count = connection.execute(
                "SELECT COUNT(*) FROM document"
            ).fetchone()[0]
            event_count = connection.execute("SELECT COUNT(*) FROM event").fetchone()[0]
            fix05_links = connection.execute(
                "SELECT COUNT(*) FROM document_event_link WHERE event_id IN (?, ?, ?)",
                tuple(FIX05_EVENTS),
            ).fetchone()[0]
            sourceless_legacy = connection.execute(
                "SELECT COUNT(*) FROM document "
                "WHERE document_source_identity_status = 'legacy_label_only' "
                "AND document_source_id IS NULL"
            ).fetchone()[0]
        self.assertEqual(document_count, 787 + 33)
        self.assertEqual(event_count, 45 + 27)
        self.assertEqual(fix05_links, 6)
        self.assertEqual(sourceless_legacy, 787)


if __name__ == "__main__":
    unittest.main()
