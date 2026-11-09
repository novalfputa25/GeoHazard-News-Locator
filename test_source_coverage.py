import unittest
from collections import Counter

import category_detector as cd
import dataset_baseline
import source_coverage as sc


class SourceCoverageRegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources, cls.mappings = sc.load_registry()
        cls.summary = sc.coverage_summary(cls.sources, cls.mappings)
        cls.by_category = {
            item["category"]: item for item in cls.summary["categories"]
        }

    def test_target_categories_match_classifier(self):
        self.assertEqual(
            sc.TARGET_CATEGORIES,
            tuple(cd.CATEGORIES[:8]),
        )
        self.assertEqual(len(sc.TARGET_CATEGORIES), 8)

    def test_registry_is_valid(self):
        self.assertGreater(len(self.sources), 0)
        self.assertGreater(len(self.mappings), 0)
        self.assertEqual(sc.validate_registry(self.sources, self.mappings), [])

    def test_source_ids_are_unique(self):
        source_ids = [row["source_id"] for row in self.sources]
        self.assertEqual(len(source_ids), len(set(source_ids)))

    def test_status_counts_and_lists_share_registry_source(self):
        access = Counter(row["status_akses"] for row in self.sources)
        permission = Counter(row["status_izin"] for row in self.sources)
        implementation = Counter(
            row["status_implementasi"] for row in self.sources
        )
        need_permission = sorted(
            row["source_id"]
            for row in self.sources
            if row["status_izin"] == "perlu_izin"
        )
        access_permission = sorted(
            row["source_id"]
            for row in self.sources
            if row["status_akses"] == "perlu_izin"
        )

        self.assertEqual(
            self.summary["access_counts"],
            dict(sorted(access.items())),
        )
        self.assertEqual(
            self.summary["permission_counts"],
            dict(sorted(permission.items())),
        )
        self.assertEqual(
            self.summary["implementation_counts"],
            dict(sorted(implementation.items())),
        )
        self.assertEqual(self.summary["need_permission_ids"], need_permission)
        self.assertEqual(self.summary["access_permission_ids"], access_permission)
        self.assertEqual(
            len(self.summary["need_permission_ids"]),
            self.summary["permission_counts"].get("perlu_izin", 0),
        )
        self.assertEqual(
            len(self.summary["access_permission_ids"]),
            self.summary["access_counts"].get("perlu_izin", 0),
        )
        self.assertEqual(
            self.summary["need_permission_without_access_permission_ids"],
            sorted(set(need_permission) - set(access_permission)),
        )
        self.assertEqual(len(need_permission), 15)
        self.assertEqual(self.summary["access_counts"].get("perlu_izin"), 14)

    def test_mapping_references_and_values_are_valid(self):
        source_ids = {row["source_id"] for row in self.sources}
        for row in self.mappings:
            with self.subTest(
                source=row["source_id"],
                category=row["category"],
                jenis_data=row["jenis_data"],
            ):
                self.assertIn(row["source_id"], source_ids)
                self.assertIn(row["category"], sc.TARGET_CATEGORIES)
                self.assertIn(row["jenis_data"], sc.DATA_TYPES)
                self.assertIn(row["status_pemetaan"], sc.MAPPING_STATUSES)
                self.assertIn(row["prioritas"], sc.PRIORITIES)

    def test_all_eight_categories_have_mappings(self):
        for category in sc.TARGET_CATEGORIES:
            with self.subTest(category=category):
                self.assertGreater(
                    len(sc.mappings_for_category(category, self.mappings)),
                    0,
                )

    def test_many_to_many_source_and_category(self):
        self.assertEqual(
            sc.categories_for_source("gdacs_all", self.mappings),
            ["Gempabumi", "Tsunami"],
        )
        self.assertEqual(
            sc.categories_for_source("pvmbg_laporan_singkat", self.mappings),
            [
                "Gunungapi",
                "Gempabumi",
                "Gerakan Tanah/Tanah Longsor",
            ],
        )
        landslide_sources = {
            row["source_id"]
            for row in sc.sources_for_category(
                "Gerakan Tanah/Tanah Longsor",
                self.sources,
                self.mappings,
            )
        }
        self.assertIn("portalmbg_field_reports", landslide_sources)
        self.assertIn("pvmbg_laporan_singkat", landslide_sources)
        self.assertIn("mongabay_indonesia", landslide_sources)

    def test_tsunami_potential_is_not_an_event_mapping(self):
        rows = [
            row
            for row in self.mappings
            if row["source_id"] == "bmkg_autogempa"
        ]
        by_category = {row["category"]: row for row in rows}
        self.assertEqual(
            by_category["Gempabumi"]["jenis_data"],
            "kejadian_aktual",
        )
        self.assertEqual(
            by_category["Tsunami"]["jenis_data"],
            "atribut_bahaya",
        )
        self.assertNotEqual(
            by_category["Tsunami"]["jenis_data"],
            "kejadian_aktual",
        )

    def test_tsunami_attributes_are_not_counted_as_events(self):
        tsunami = self.by_category["Tsunami"]
        attribute_ids = {
            row["source_id"]
            for row in self.mappings
            if row["category"] == "Tsunami"
            and row["jenis_data"] == "atribut_bahaya"
        }
        self.assertIn("bmkg_autogempa", attribute_ids)
        self.assertIn("bmkg_gempa_terkini", attribute_ids)
        self.assertFalse(
            attribute_ids & set(tsunami["active_event_source_ids"])
        )
        self.assertFalse(
            attribute_ids & set(tsunami["official_candidate_event_source_ids"])
        )
        self.assertFalse(
            attribute_ids & set(tsunami["event_candidate_source_ids"])
        )
        self.assertEqual(tsunami["active_event_sources"], 0)

    def test_report_permission_count_matches_registry(self):
        report = sc.render_markdown(self.summary, self.sources, self.mappings)
        expected = len(self.summary["need_permission_ids"])
        self.assertIn(
            f"Sumber dengan status izin `perlu_izin`: **{expected}**.",
            report,
        )
        self.assertIn(
            f"| `perlu_izin` | {self.summary['permission_counts']['perlu_izin']} |",
            report,
        )
        section = report.split("### Perlu izin (status izin)", 1)[1]
        section = section.split("###", 1)[0]
        listed_ids = [
            line.split("`")[1]
            for line in section.splitlines()
            if line.startswith("- `")
        ]
        self.assertEqual(listed_ids, self.summary["need_permission_ids"])

    def test_coverage_summary_statuses(self):
        gempa = self.by_category["Gempabumi"]
        self.assertEqual(gempa["coverage_status"], "TERCAKUP_OPERASIONAL")
        self.assertGreaterEqual(gempa["official_active_event_sources"], 1)

        for category in (
            "Gunungapi",
            "Gerakan Tanah/Tanah Longsor",
        ):
            with self.subTest(category=category):
                item = self.by_category[category]
                self.assertEqual(
                    item["coverage_status"],
                    "KANDIDAT_RESMI_PERLU_IZIN",
                )
                self.assertEqual(item["official_active_event_sources"], 0)
                self.assertGreater(item["official_candidate_event_sources"], 0)

        tsunami = self.by_category["Tsunami"]
        self.assertEqual(tsunami["coverage_status"], "KANDIDAT_KEJADIAN")
        self.assertEqual(tsunami["official_active_event_sources"], 0)
        self.assertGreaterEqual(tsunami["historical_sources"], 1)

        for category in (
            "Likuefaksi",
            "Abrasi dan Akresi",
            "Penurunan Muka Tanah",
            "Semburan Gas dan Lumpur",
        ):
            with self.subTest(category=category):
                item = self.by_category[category]
                self.assertEqual(item["active_event_sources"], 0)
                self.assertEqual(item["official_active_event_sources"], 0)
                self.assertNotEqual(
                    item["coverage_status"],
                    "TERCAKUP_OPERASIONAL",
                )

        self.assertGreaterEqual(self.by_category["Likuefaksi"]["risk_sources"], 1)
        self.assertGreaterEqual(
            self.by_category["Abrasi dan Akresi"]["risk_sources"],
            1,
        )
        self.assertGreaterEqual(
            self.by_category["Penurunan Muka Tanah"]["manual_sources"],
            1,
        )
        self.assertGreaterEqual(
            self.by_category["Semburan Gas dan Lumpur"]["manual_sources"],
            1,
        )

    def test_report_contains_all_categories_and_statuses(self):
        report = sc.render_markdown(self.summary, self.sources, self.mappings)
        for category in sc.TARGET_CATEGORIES:
            with self.subTest(category=category):
                self.assertIn(category, report)
        self.assertIn("TERCAKUP_OPERASIONAL", report)
        self.assertIn("KANDIDAT_RESMI_PERLU_IZIN", report)
        self.assertIn("KANDIDAT_KEJADIAN", report)
        self.assertIn("HANYA_BERITA_DAN_INFORMASI_MANUAL", report)

    def test_unknown_category_is_rejected(self):
        with self.assertRaises(ValueError):
            sc.sources_for_category(
                "Banjir",
                self.sources,
                self.mappings,
            )

    def test_baseline_is_unchanged(self):
        metadata = dataset_baseline.verify_dataset()
        self.assertEqual(
            metadata["sha256"],
            dataset_baseline.DATASET_SHA256,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
