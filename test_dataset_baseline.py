import unittest

import dataset_baseline as baseline


class DatasetBaselineTest(unittest.TestCase):
    def test_primary_path_exists(self):
        self.assertTrue(baseline.PRIMARY_DATASET_PATH.is_file())

    def test_metadata_contract(self):
        self.assertEqual(
            baseline.DATASET_RELATIVE_PATH,
            "data/geohazard_news_final_20261101T150501Z.csv",
        )
        self.assertEqual(baseline.DATASET_ROWS, 787)
        self.assertEqual(baseline.DATASET_COLUMNS, 51)
        self.assertEqual(baseline.FINALIZED_AT, "2026-11-01T15:05:01Z")

    def test_verify_dataset(self):
        metadata = baseline.verify_dataset()
        self.assertEqual(metadata["sha256"], baseline.DATASET_SHA256)
        self.assertEqual(metadata["rows"], 787)
        self.assertEqual(metadata["columns"], 51)


if __name__ == "__main__":
    unittest.main()
