import unittest
from collections import Counter
from datetime import datetime, timezone

from scripts import fix_tsunami_potential_semantics as fix
from scripts import pilot_collect_official_geohazard as pilot


class TsunamiClassifierTest(unittest.TestCase):
    def test_explicit_positive(self):
        values = [
            "Berpotensi tsunami",
            "Gempa berpotensi tsunami",
            "Tsunami warning issued",
            "Tsunami may occur",
        ]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(
                    pilot.classify_tsunami_potential(value), "positive"
                )

    def test_explicit_negative(self):
        values = [
            "Tidak berpotensi tsunami",
            "Tidak ada potensi tsunami",
            "Tidak ada ancaman tsunami",
            "Gempa ini tidak berpotensi tsunami",
            "Tidak menimbulkan tsunami",
            "Tsunami potential: none",
            "No tsunami threat",
        ]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(
                    pilot.classify_tsunami_potential(value), "negative"
                )

    def test_unknown(self):
        values = [
            "",
            "Tidak diketahui",
            "Informasi tsunami dapat diakses di BMKG",
            "Tidak ada informasi tsunami",
            "Tidak ada laporan tsunami",
            "Tidak ada peringatan tsunami",
            "No tsunami warning",
            "Tsunami",
            "Gempa ini dirasakan untuk diteruskan pada masyarakat",
        ]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(
                    pilot.classify_tsunami_potential(value), "unknown"
                )


class TsunamiAttributesTest(unittest.TestCase):
    def setUp(self):
        self.dictionary = pilot.load_dictionary()

    def attributes(self, value, source_id="bmkg_gempa_terkini"):
        item = {
            "magnitude_text": "5.0",
            "depth_text": "10 km",
            "source_id": source_id,
            "extra": {"potensi": value},
        }
        return {
            row["attribute_name"]: row
            for row in pilot.build_attributes(
                item, "EVT-TEST-TSUNAMI", self.dictionary
            )
        }

    def test_negative_keeps_raw_text_and_uses_status(self):
        rows = self.attributes("Tidak berpotensi tsunami")
        self.assertNotIn("tsunami_potential", rows)
        self.assertNotIn("bmkg_potential_note", rows)
        self.assertEqual(
            rows["bmkg_potential_text"]["attribute_value"],
            "Tidak berpotensi tsunami",
        )
        self.assertEqual(
            rows["tsunami_potential_status"]["attribute_value"], "negative"
        )
        self.assertEqual(
            rows["tsunami_potential_status"]["attribute_confidence"], "high"
        )

    def test_positive_keeps_raw_text_and_uses_status(self):
        rows = self.attributes("Gempa berpotensi tsunami")
        self.assertEqual(
            rows["bmkg_potential_text"]["attribute_value"],
            "Gempa berpotensi tsunami",
        )
        self.assertEqual(
            rows["tsunami_potential_status"]["attribute_value"], "positive"
        )

    def test_empty_source_value_is_unknown(self):
        rows = self.attributes("")
        self.assertNotIn("bmkg_potential_text", rows)
        self.assertEqual(
            rows["tsunami_potential_status"]["attribute_value"], "unknown"
        )
        self.assertEqual(
            rows["tsunami_potential_status"]["attribute_confidence"], "unknown"
        )

    def test_non_tsunami_note_is_unknown(self):
        rows = self.attributes(
            "Gempa ini dirasakan untuk diteruskan pada masyarakat"
        )
        self.assertEqual(
            rows["tsunami_potential_status"]["attribute_value"], "unknown"
        )
        self.assertEqual(
            rows["tsunami_potential_status"]["attribute_confidence"], "low"
        )

    def test_status_does_not_create_tsunami_category(self):
        item = {
            "source_id": "usgs_m45",
            "native_id": "test-event",
            "priority": 0,
            "retrieved_at": datetime(2026, 11, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 11, 1, tzinfo=timezone.utc),
            "title": "M 5.0 - Test",
            "event_time": datetime(2026, 11, 1, tzinfo=timezone.utc),
            "event_time_evidence": "Test evidence",
            "location_name": "Test location",
            "lat": -2.0,
            "lon": 120.0,
            "category_original": "Gempa Bumi",
        }
        built = pilot.build_event_group([item], self.dictionary)
        self.assertEqual(built["category"]["category_name"], "Gempabumi")


class PilotFixRegressionTest(unittest.TestCase):
    @unittest.skipUnless(
        fix.DEFAULT_SOURCE_RUN.is_dir(), "Run pilot sumber tidak tersedia"
    )
    def test_fix_migrates_legacy_rows_without_mutating_source(self):
        source_path = (
            fix.DEFAULT_SOURCE_RUN / "tables" / "event_attribute.csv"
        )
        before = pilot.sha256_file(source_path)
        attributes, rebuilt, summary = fix.event_attribute_rows(
            fix.DEFAULT_SOURCE_RUN, pilot.load_dictionary()
        )
        self.assertEqual(pilot.sha256_file(source_path), before)
        self.assertEqual(len(attributes), 59)
        self.assertEqual(len(rebuilt), 79)
        names = Counter(row["attribute_name"] for row in rebuilt)
        self.assertNotIn("tsunami_potential", names)
        self.assertNotIn("bmkg_potential_note", names)
        self.assertEqual(names["bmkg_potential_text"], 11)
        statuses = Counter(
            row["tsunami_potential_status"] for row in summary
        )
        self.assertEqual(
            statuses, Counter({"negative": 10, "unknown": 10})
        )


if __name__ == "__main__":
    unittest.main()
