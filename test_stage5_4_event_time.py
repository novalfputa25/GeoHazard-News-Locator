import unittest

from scripts import extract_event_time_stage5_4 as s54


class Stage54EventTimeTest(unittest.TestCase):
    def baris(self, **kwargs):
        dasar = {
            "judul": "",
            "published_time": "Mon, 19 Oct 2026 07:00:00 +0700",
            "event_time": "",
            "sumber": "CNN Indonesia",
            "kategori": "Lainnya",
            "isi_berita": "",
        }
        dasar.update(kwargs)
        return dasar

    def test_bmkg_nowcast_uses_source_timezone(self):
        row = self.baris(
            sumber="BMKG",
            kategori="Cuaca Ekstrem",
            isi_berita="Hujan lebat akan terjadi pada 19 October 2026, 13:50 WITA di wilayah.",
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "terekstrak")
        self.assertEqual(hasil["event_time"], "2026-10-19T13:50:00+08:00")
        self.assertEqual(hasil["event_time_basis"], "bmkg_nowcast")
        self.assertIn("13:50 WITA", hasil["event_time_evidence"])

    def test_bmkg_earthquake_uses_tanggal(self):
        row = self.baris(
            sumber="BMKG",
            kategori="Gempabumi",
            isi_berita="Tanggal: 18 Okt 2026 15:02:46 WIB Koordinat: Magnitudo: 4.1",
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time"], "2026-10-18T15:02:46+07:00")
        self.assertEqual(hasil["event_time_basis"], "bmkg_tanggal")

    def test_usgs_uses_utc_time(self):
        row = self.baris(
            sumber="USGS",
            kategori="Gempabumi",
            isi_berita="Time 2026-10-19 06:15:13 UTC at epicenter Location 6.337S",
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time"], "2026-10-19T06:15:13+00:00")
        self.assertEqual(hasil["event_time_basis"], "usgs_time")

    def test_gdacs_fire_is_date_only(self):
        row = self.baris(
            sumber="GDACS",
            judul="Green forest fire notification in Indonesia",
            isi_berita="On 12/10/2026, a forest fire started in Indonesia, until 18/10/2026.",
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "tanggal_saja")
        self.assertEqual(hasil["event_time"], "2026-10-12")
        self.assertNotIn("T", hasil["event_time"])

    def test_gdacs_earthquake_uses_title_utc(self):
        row = self.baris(
            sumber="GDACS",
            kategori="Gempabumi",
            judul="Green earthquake in Indonesia 19/10/2026 06:15 UTC",
            isi_berita="On 10/19/2026 6:15:13 AM, an earthquake occurred in Indonesia.",
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time"], "2026-10-19T06:15:00+00:00")
        self.assertEqual(hasil["event_time_basis"], "gdacs_judul")

    def test_published_time_is_not_event_time(self):
        row = self.baris(
            judul="Berita tanpa tanggal kejadian",
            isi_berita="Informasi umum tanpa tanggal atau jam kejadian.",
            published_time="2026-10-19T07:00:00+07:00",
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "tidak_tersedia")
        self.assertEqual(hasil["event_time"], "")
        self.assertNotIn("2026-10-19T07:00:00", hasil["event_time"])

    def test_general_explicit_hazard_date_is_date_only(self):
        row = self.baris(
            kategori="Gunungapi",
            judul="Gunung Anak Krakatau Tiga Kali Erupsi",
            isi_berita=(
                "Gunung Anak Krakatau erupsi pada 18 Oktober 2026, "
                "dengan kolom abu mencapai 500 meter."
            ),
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "tanggal_saja")
        self.assertEqual(hasil["event_time"], "2026-10-18")
        self.assertEqual(hasil["event_time_basis"], "isi_berita")

    def test_general_policy_date_is_not_event_time(self):
        row = self.baris(
            kategori="Kebakaran Hutan dan Lahan",
            judul="Akses Wisata Bromo Dibatasi",
            isi_berita=(
                "Pengelola resmi memberlakukan pembatasan akses wisata "
                "mulai 17 Oktober 2026."
            ),
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "perlu_review")
        self.assertEqual(hasil["event_time"], "")
        self.assertEqual(hasil["event_time_basis"], "kandidat_bukan_waktu_kejadian")

    def test_date_without_year_is_not_inferred(self):
        row = self.baris(
            kategori="Kebakaran Hutan dan Lahan",
            judul="Melihat Asap Kebakaran Hutan",
            isi_berita="Asap tebal membubung di Sumatera Selatan pada Minggu (18/10).",
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "perlu_review")
        self.assertEqual(hasil["event_time"], "")
        self.assertEqual(hasil["event_time_basis"], "kandidat_tanggal_tanpa_tahun")

    def test_date_range_is_not_reduced_to_one_date(self):
        row = self.baris(
            kategori="Gunungapi",
            judul="KBM Dialihkan ke Daring",
            isi_berita=(
                "Pemerintah mengalihkan pembelajaran daring pada "
                "7-8 September 2026 akibat abu vulkanik."
            ),
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "perlu_review")
        self.assertEqual(hasil["event_time"], "")
        self.assertEqual(hasil["event_time_basis"], "kandidat_rentang_tanggal")

    def test_explicit_time_without_zone_is_kept_naive(self):
        row = self.baris(
            kategori="Gerakan Tanah/Tanah Longsor",
            judul="Empat Penambang Tewas Terimbun Longsor",
            isi_berita=(
                "Empat penambang tewas setelah longsor terjadi pada, "
                "Selasa (6/10/26). Korban tertimbun sekitar pukul 01.00 dini hari."
            ),
        )
        hasil = s54.ekstrak_event_time(row)
        self.assertEqual(hasil["event_time_status"], "terekstrak")
        self.assertEqual(hasil["event_time"], "2026-10-06T01:00:00")
        self.assertEqual(hasil["event_time_basis"], "isi_berita_tanpa_zona")
        self.assertIn("01.00", hasil["event_time_evidence"])

    def test_builder_preserves_other_fields(self):
        rows = [
            self.baris(judul="Hujan Lebat", kategori="Cuaca Ekstrem", provinsi="Jambi"),
            self.baris(judul="Berita umum", kategori="Lainnya", provinsi=""),
        ]
        hasil = s54.bangun_baris(rows)
        self.assertEqual(len(hasil), len(rows))
        self.assertEqual(hasil[0]["judul"], rows[0]["judul"])
        self.assertEqual(hasil[0]["provinsi"], "Jambi")
        self.assertEqual(hasil[0]["event_time_status"], "tidak_tersedia")
        for k in s54.NEW_FIELDS:
            self.assertIn(k, hasil[0])

    def test_nonempty_event_time_has_evidence(self):
        rows = [
            self.baris(
                sumber="BMKG",
                kategori="Gempabumi",
                isi_berita="Tanggal: 18 Okt 2026 15:02:46 WIB",
            ),
            self.baris(
                kategori="Gunungapi",
                judul="Erupsi",
                isi_berita="Gunung erupsi pada 18 Oktober 2026.",
            ),
        ]
        for row in s54.bangun_baris(rows):
            if row["event_time_status"] in {"terekstrak", "tanggal_saja"}:
                self.assertTrue(row["event_time_evidence"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
