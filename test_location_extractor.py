import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import location_extractor as le


STAGE1_FIELDS = [
    "judul",
    "published_time",
    "event_time",
    "sumber",
    "source_id",
    "kategori",
    "provinsi",
    "kabupaten_kota",
    "kecamatan",
    "desa_kelurahan",
    "dusun_kampung",
    "rw",
    "rt",
    "alamat_detail",
    "url",
    "isi_berita",
    "duplicate_of",
    "duplicate_reason",
]


class LocationExtractorStage3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exact, cls.bare, cls.bare_index = le.muat_gazetteer()

    def lokasi(self, judul, isi=""):
        return le.ekstrak_lokasi(
            judul, isi, self.exact, self.bare, self.bare_index
        )

    def assert_lokasi(self, judul, isi, provinsi, kabupaten):
        hasil = self.lokasi(judul, isi)
        self.assertEqual(hasil["provinsi"], provinsi)
        self.assertEqual(hasil["kabupaten_kota"], kabupaten)

    def test_event_location_is_filled(self):
        self.assert_lokasi(
            "Gempa M 5,0 berpusat di Cianjur", "", "Jawa Barat",
            "Kabupaten Cianjur",
        )
        self.assert_lokasi(
            "Gempa di Palu", "", "Sulawesi Tengah", "Kota Palu",
        )
        self.assert_lokasi(
            "Info cuaca",
            "Hujan lebat melanda Kabupaten Bogor.",
            "Jawa Barat",
            "Kabupaten Bogor",
        )

    def test_office_narasumber_and_comparison_are_ignored(self):
        self.assert_lokasi(
            "Kunjungan ke Kantor BMKG Jakarta",
            "Kegiatan berlangsung di kantor.",
            "",
            "",
        )
        self.assert_lokasi(
            "Gempa Cianjur, kata narasumber di Jakarta",
            "Gempa berpusat di Cianjur.",
            "Jawa Barat",
            "Kabupaten Cianjur",
        )
        self.assert_lokasi(
            "Gempa Cianjur, dibandingkan gempa Aceh tahun 2004",
            "",
            "Jawa Barat",
            "Kabupaten Cianjur",
        )

    def test_forecast_and_generic_context_are_ignored(self):
        self.assert_lokasi("Prakiraan Cuaca Jakarta", "", "", "")
        self.assert_lokasi(
            "Prakiraan Cuaca Jakarta",
            "BMKG memprakirakan hujan di Jakarta Selatan.",
            "",
            "",
        )
        self.assert_lokasi(
            "Moto Prix Piala Wali Kota Pekanbaru",
            "Event ini memberi bantuan untuk korban bencana di NTT.",
            "",
            "",
        )
        self.assert_lokasi(
            "Kontainer Terlepas dari Truk Timpa 3 Mahasiswi",
            "Peristiwa terjadi di Takalar, Sulawesi Selatan.",
            "",
            "",
        )
        self.assert_lokasi(
            "Adik eks Kepala BNPB diduga gunakan dana bencana",
            "Dana itu untuk menangani banjir Sumatra dan gempa NTT.",
            "",
            "",
        )

    def test_ambiguous_bare_names_do_not_guess_type(self):
        self.assert_lokasi(
            "Gempa Cianjur dan Sukabumi", "", "Jawa Barat", "",
        )
        self.assert_lokasi("Gempa Bogor", "", "Jawa Barat", "")
        self.assert_lokasi(
            "Gempa Kabupaten Bogor", "", "Jawa Barat", "Kabupaten Bogor",
        )
        self.assert_lokasi(
            "Gempa Kota Bogor", "", "Jawa Barat", "Kota Bogor",
        )

    def test_title_province_wins_over_conflicting_content_name(self):
        self.assert_lokasi(
            "Hujan Lebat disertai Petir di Riau",
            "Hujan lebat di BATANG GANGSAL, BATANG TUAKA, dan ENOK.",
            "Riau",
            "",
        )
        self.assert_lokasi(
            "Hujan Lebat disertai Petir di Kep. Riau",
            "Hujan lebat di wilayah Kepulauan Riau.",
            "Kepulauan Riau",
            "",
        )

    def test_contextual_manggarai_and_batu_are_not_guessed(self):
        self.assert_lokasi(
            "Pedagang di Manggarai jadi korban penjarahan",
            "Tawuran terjadi di Stasiun Manggarai, Jakarta.",
            "",
            "",
        )
        self.assert_lokasi(
            "Pramono Resmikan 2 Embung di Jaktim",
            "Embung Batu Bangkong untuk pengendalian banjir.",
            "",
            "",
        )

    def test_bmkg_url_coordinates(self):
        hasil = le.ekstrak_koordinat({
            "url": (
                "https://www.bmkg.go.id/gempabumi/"
                "?t=2026-10-18T08%3A02%3A46%2B00%3A00"
                "&lat=8.14+LS&lon=120.29+BT&mag=4.1"
            )
        })
        self.assertEqual(hasil["latitude"], "-8.14")
        self.assertEqual(hasil["longitude"], "120.29")
        self.assertEqual(hasil["koordinat_status"], "tersedia_sumber")
        self.assertEqual(hasil["koordinat_sumber"], "URL BMKG")

    def test_usgs_coordinates_and_invalid_coordinates(self):
        hasil = le.ekstrak_koordinat({
            "isi_berita": "Location 6.337 S 129.929 E Depth 10 km",
        })
        self.assertEqual(hasil["latitude"], "-6.337")
        self.assertEqual(hasil["longitude"], "129.929")
        self.assertEqual(hasil["koordinat_status"], "tersedia_sumber")
        self.assertEqual(hasil["koordinat_sumber"], "isi USGS")

        hasil = le.ekstrak_koordinat({
            "url": "https://example.test/?lat=abc&lon=999",
        })
        self.assertEqual(hasil["latitude"], "")
        self.assertEqual(hasil["longitude"], "")
        self.assertEqual(hasil["koordinat_status"], "tidak_ada")

    def test_output_fieldnames_preserve_stage1_schema(self):
        hasil = le._fieldnames_output(STAGE1_FIELDS)
        for nama in (
            "source_id",
            "duplicate_of",
            "duplicate_reason",
            "latitude",
            "longitude",
            "koordinat_status",
            "koordinat_sumber",
        ):
            self.assertIn(nama, hasil)

    def test_main_preserves_input_and_writes_new_file(self):
        with tempfile.TemporaryDirectory(prefix="geohazard_stage3_") as folder:
            folder = Path(folder)
            input_path = folder / "geohazard_news_scrape_20261029T000000Z.csv"
            rows = [
                {
                    "judul": "Gempa M 5,0 berpusat di Cianjur",
                    "published_time": "",
                    "event_time": "2026-10-18T08:02:46+00:00",
                    "sumber": "BMKG",
                    "source_id": "bmkg_autogempa",
                    "kategori": "Gempa Bumi",
                    "provinsi": "",
                    "kabupaten_kota": "",
                    "kecamatan": "",
                    "desa_kelurahan": "",
                    "dusun_kampung": "",
                    "rw": "",
                    "rt": "",
                    "alamat_detail": "",
                    "url": (
                        "https://www.bmkg.go.id/gempabumi/"
                        "?lat=8.14+LS&lon=120.29+BT&mag=4.1"
                    ),
                    "isi_berita": "Gempa berpusat di Cianjur.",
                    "duplicate_of": "",
                    "duplicate_reason": "",
                },
                {
                    "judul": "Kunjungan ke Kantor BMKG Jakarta",
                    "published_time": "",
                    "event_time": "",
                    "sumber": "ANTARA",
                    "source_id": "antara",
                    "kategori": "Lainnya",
                    "provinsi": "",
                    "kabupaten_kota": "",
                    "kecamatan": "",
                    "desa_kelurahan": "",
                    "dusun_kampung": "",
                    "rw": "",
                    "rt": "",
                    "alamat_detail": "",
                    "url": "https://example.test/office",
                    "isi_berita": "Kegiatan berlangsung di kantor.",
                    "duplicate_of": "",
                    "duplicate_reason": "",
                },
            ]
            with open(input_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=STAGE1_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            before = input_path.read_bytes()

            old_output_dir = le.OUTPUT_DIR
            old_input_file = le.INPUT_FILE
            le.OUTPUT_DIR = folder
            le.INPUT_FILE = folder / "tidak-ada.csv"
            try:
                with redirect_stdout(io.StringIO()):
                    le.main()
            finally:
                le.OUTPUT_DIR = old_output_dir
                le.INPUT_FILE = old_input_file

            self.assertEqual(input_path.read_bytes(), before)
            files = list(folder.glob("geohazard_news_located_*.csv"))
            self.assertEqual(len(files), 1)
            output_path = files[0]
            self.assertNotEqual(output_path.name, "geohazard_news_located.csv")

            with open(output_path, newline="", encoding="utf-8-sig") as f:
                output_rows = list(csv.DictReader(f))
            self.assertEqual(len(output_rows), 2)
            self.assertIn("source_id", output_rows[0])
            self.assertIn("duplicate_of", output_rows[0])
            self.assertIn("duplicate_reason", output_rows[0])
            self.assertEqual(
                output_rows[0]["kabupaten_kota"], "Kabupaten Cianjur"
            )
            self.assertEqual(output_rows[0]["latitude"], "-8.14")
            self.assertEqual(output_rows[0]["longitude"], "120.29")
            self.assertEqual(output_rows[1]["provinsi"], "")
            self.assertEqual(output_rows[1]["kabupaten_kota"], "")


if __name__ == "__main__":
    unittest.main()
