import sqlite3
import sys
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import backfill_document_relevance as backfill_module
from relevance import (
    CLASSIFIER_VERSION,
    RELEVANCE_IRRELEVANT,
    RELEVANCE_RELEVANT,
    RELEVANCE_REVIEW,
    classify_relevance,
)


class RelevanceClassifierTest(unittest.TestCase):
    def assertDecision(self, title, content, category, status, category_name=None):
        result = classify_relevance(
            title,
            content,
            category,
            "ANTARA",
            "news",
        )
        self.assertEqual(result["relevance_status"], status)
        if category_name is not None:
            self.assertEqual(result["relevance_category"], category_name)
        self.assertEqual(result["classifier_version"], CLASSIFIER_VERSION)

    def test_earthquake_news_is_relevant(self):
        self.assertDecision(
            "Gempa M5.2 Guncang Sukabumi, Warga Berhamburan ke Jalan",
            "Gempa berkekuatan magnitudo 5,2 mengguncang Sukabumi. "
            "BMKG mencatat episenter berada di laut.",
            "Gempabumi",
            RELEVANCE_RELEVANT,
            "Gempabumi",
        )

    def test_official_weather_warning_is_not_geohazard_news(self):
        result = classify_relevance(
            "Hujan Lebat disertai Petir di Riau",
            "BMKG memprakirakan hujan lebat disertai petir di Riau.",
            "Lainnya",
            "BMKG Open Data",
            "official",
        )
        self.assertEqual(result["relevance_status"], RELEVANCE_IRRELEVANT)
        self.assertEqual(result["relevance_basis"], "di_luar_8_kategori")

    def test_forest_fire_and_drought_are_out_of_scope(self):
        for title in (
            "Green forest fire notification in Indonesia",
            "Drought is on going in Indonesia",
        ):
            result = classify_relevance(title, "", "Lainnya", "GDACS", "official")
            self.assertEqual(result["relevance_status"], RELEVANCE_IRRELEVANT)
            self.assertEqual(result["relevance_category"], "Lainnya")

    def test_wildlife_and_environment_news_is_irrelevant(self):
        self.assertDecision(
            "Monyet Ekor Panjang Masuk Permukiman Warga",
            "Monyet ekor panjang meresahkan warga. "
            "Upaya konservasi satwa liar terus dilakukan.",
            "Lainnya",
            RELEVANCE_IRRELEVANT,
        )

    def test_tourism_context_is_irrelevant(self):
        self.assertDecision(
            "Pesona Gunung Semeru untuk Pendakian Akhir Pekan",
            "Pendaki menikmati panorama Gunung Semeru.",
            "Gunungapi",
            RELEVANCE_IRRELEVANT,
        )

    def test_fraud_using_disaster_funds_is_irrelevant(self):
        result = classify_relevance(
            "Adik eks Kepala BNPB diduga gunakan dana bencana gempa NTT",
            "Tersangka korupsi dana bantuan gempa NTT menjalani sidang.",
            "Gempabumi",
            "ANTARA",
            "news",
        )
        self.assertEqual(result["relevance_status"], RELEVANCE_IRRELEVANT)
        self.assertEqual(result["relevance_basis"], "konteks_non_geohazard")

    def test_landslide_is_relevant(self):
        self.assertDecision(
            "Longsor Timpa Rumah Warga di Bogor",
            "Longsor mengakibatkan rumah rusak dan korban luka.",
            "Gerakan Tanah/Tanah Longsor",
            RELEVANCE_RELEVANT,
            "Gerakan Tanah/Tanah Longsor",
        )

    def test_volcanic_eruption_is_relevant(self):
        self.assertDecision(
            "Gunung Anak Krakatau Erupsi, Kolom Abu Capai 500 Meter",
            "Gunung Anak Krakatau erupsi dan mengeluarkan abu vulkanik.",
            "Gunungapi",
            RELEVANCE_RELEVANT,
            "Gunungapi",
        )

    def test_coastal_abrasion_is_relevant(self):
        self.assertDecision(
            "Abrasi Pantai di Demak Rusak Puluhan Rumah",
            "Abrasi pantai merusak puluhan rumah warga.",
            "Abrasi dan Akresi",
            RELEVANCE_RELEVANT,
            "Abrasi dan Akresi",
        )

    def test_ambiguous_geology_without_event_needs_review(self):
        result = classify_relevance(
            "Ada Daratan Baru di Dekat Anak Krakatau",
            "Fenomena geologi ini menarik perhatian warga.",
            "Lainnya",
            "Kompas",
            "news",
        )
        self.assertEqual(result["relevance_status"], RELEVANCE_REVIEW)
        self.assertEqual(result["relevance_basis"], "konteks_geologi_tanpa_peristiwa")

    def test_non_geologic_earthquake_metaphor_is_irrelevant(self):
        self.assertDecision(
            "Gempa Saham di Bursa, IHSG Anjlok",
            "Gempa saham membuat IHSG anjlok.",
            "Lainnya",
            RELEVANCE_IRRELEVANT,
        )


class RelevanceBackfillTest(unittest.TestCase):
    def _insert_document(self, connection):
        connection.execute(
            """
            INSERT INTO document (
                document_id, document_type, document_source_label,
                document_source_identity_status, document_source_type,
                document_url, document_url_canonical, document_title,
                document_status, document_provenance_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "DOC-test-relevance",
                "news_article",
                "ANTARA",
                "verified",
                "news",
                "https://example.test/gempa",
                "https://example.test/gempa",
                "Gempa M5.2 Guncang Sukabumi",
                "active",
                "verified",
            ),
        )
        connection.execute(
            """
            INSERT INTO document_classification (
                classification_id, document_id, category_name,
                category_scope, category_basis, category_confidence,
                category_evidence, classified_at, review_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "CLS-test-relevance",
                "DOC-test-relevance",
                "Gempabumi",
                "in_scope",
                "judul:Gempabumi",
                "high",
                "gempa",
                "2026-11-04T00:00:00Z",
                "not_reviewed",
            ),
        )
        connection.commit()

    def test_backfill_is_idempotent_and_preserves_reviewed_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            backfill_module.initialize_database(db_path)
            with closing(sqlite3.connect(str(db_path))) as connection:
                self._insert_document(connection)

            first = backfill_module.backfill(db_path)
            self.assertEqual(first["documents"], 1)
            self.assertEqual(first["status_counts"], {RELEVANCE_RELEVANT: 1})

            with closing(sqlite3.connect(str(db_path))) as connection:
                connection.execute(
                    """
                    UPDATE document_relevance
                    SET relevance_status = ?, relevance_basis = ?,
                        review_status = 'reviewed', reviewed_by = 'tester'
                    WHERE document_id = ?
                    """,
                    (
                        RELEVANCE_IRRELEVANT,
                        "manual_review",
                        "DOC-test-relevance",
                    ),
                )
                connection.commit()

            second = backfill_module.backfill(db_path)
            self.assertEqual(second["documents"], 1)
            with closing(sqlite3.connect(str(db_path))) as connection:
                rows = connection.execute(
                    """
                    SELECT relevance_status, relevance_basis,
                           review_status, reviewed_by
                    FROM document_relevance
                    WHERE document_id = ?
                    """,
                    ("DOC-test-relevance",),
                ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0], (RELEVANCE_IRRELEVANT, "manual_review", "reviewed", "tester"))


if __name__ == "__main__":
    unittest.main()
