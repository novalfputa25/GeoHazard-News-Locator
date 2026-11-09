import unittest

from scripts import refine_geohazard_quality_stage5_2 as s52


class Stage52QualityTest(unittest.TestCase):
    def baris(self, **kwargs):
        dasar = {
            "judul": "",
            "provinsi": "",
            "kabupaten_kota": "",
            "domain_lokasi": "tidak_diketahui",
            "koordinat_domain": "tidak_diketahui",
            "status_cakupan": "tidak_terklasifikasi",
        }
        dasar.update(kwargs)
        return dasar

    def test_domain_from_province(self):
        row = self.baris(provinsi="Jambi", judul="Hujan Lebat disertai Petir di Jambi")
        domain, basis = s52.koreksi_domain(row)
        self.assertEqual(domain, "indonesia")
        self.assertEqual(basis, "provinsi")

    def test_domain_from_explicit_title(self):
        row = self.baris(
            judul="Green forest fire notification in Indonesia",
            status_cakupan="di_luar_8_kategori",
        )
        domain, basis = s52.koreksi_domain(row)
        self.assertEqual(domain, "indonesia")
        self.assertEqual(basis, "judul")

    def test_generic_indonesia_phrase_is_not_domain_evidence(self):
        row = self.baris(
            judul="Asus ROG Xbox Ally X20 Resmi di Indonesia",
            status_cakupan="tidak_terklasifikasi",
        )
        domain, basis = s52.koreksi_domain(row)
        self.assertEqual(domain, "tidak_diketahui")
        self.assertEqual(basis, "tidak_diketahui")

    def test_generic_indonesia_mention_is_not_event_domain(self):
        row = self.baris(judul="Medali pertama Indonesia di Asian Para Games 2026")
        domain, basis = s52.koreksi_domain(row)
        self.assertEqual(domain, "tidak_diketahui")
        self.assertEqual(basis, "tidak_diketahui")

    def test_coordinate_domain_wins(self):
        row = self.baris(
            provinsi="",
            judul="M 4.9 - 68 km WSW of San Juan del Sur, Nicaragua",
            koordinat_domain="luar_indonesia",
        )
        domain, basis = s52.koreksi_domain(row)
        self.assertEqual(domain, "luar_indonesia")
        self.assertEqual(basis, "koordinat")

    def test_row_27_is_flagged_not_reverted(self):
        row = self.baris(
            judul="Gempa M4.6 Pusat gempa berada di laut 49 km Barat KODI-SUMBABARATDAYA",
            provinsi="Nusa Tenggara Timur",
            kabupaten_kota="Kabupaten Sumba Barat Daya",
            domain_lokasi="indonesia",
        )
        hasil = s52.metadata_lokasi(27, row)
        self.assertEqual(hasil["lokasi_verifikasi"], "perlu_verifikasi")
        self.assertEqual(hasil["lokasi_basis"], "rujukan_toponimi")
        self.assertEqual(hasil["lokasi_risiko"], "tinggi")

    def test_focus_locations_have_risk(self):
        for nomor in (12, 14, 17, 18, 19, 24, 27):
            with self.subTest(nomor=nomor):
                hasil = s52.metadata_lokasi(nomor, self.baris())
                self.assertEqual(hasil["lokasi_verifikasi"], "perlu_verifikasi")
                self.assertIn(hasil["lokasi_risiko"], {"sedang", "tinggi"})

    def test_row_214_note(self):
        rows = [self.baris() for _ in range(214)]
        rows[-1]["judul"] = "Pemotor di Bogor Tewas Terpental Usai Hantam Trotoar"
        hasil = s52.bangun_baris(rows)
        self.assertEqual(hasil[213]["catatan_stage5_2"], "alamat_dinormalkan")

    def test_builder_preserves_rows_and_adds_notes(self):
        rows = [
            self.baris(judul="Hujan Lebat di Jambi", provinsi="Jambi"),
            self.baris(judul="Berita umum", domain_lokasi="indonesia"),
        ]
        hasil = s52.bangun_baris(rows)
        self.assertEqual(len(hasil), len(rows))
        self.assertEqual(hasil[0]["domain_lokasi"], "indonesia")
        self.assertEqual(hasil[0]["domain_lokasi_basis"], "provinsi")
        self.assertEqual(hasil[1]["domain_lokasi"], "tidak_diketahui")
        self.assertEqual(hasil[0]["lokasi_verifikasi"], "belum_diverifikasi")
        self.assertEqual(hasil[1]["lokasi_verifikasi"], "tidak_ada")


if __name__ == "__main__":
    unittest.main(verbosity=2)
