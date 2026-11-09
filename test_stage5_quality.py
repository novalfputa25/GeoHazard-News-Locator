import unittest

import category_detector as cd
import location_extractor as le
from scripts import improve_geohazard_quality_stage5 as s5


class Stage5QualityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exact, cls.bare, cls.bare_index = le.muat_gazetteer()

    def lokasi(self, judul, isi=""):
        return le.ekstrak_lokasi(
            judul, isi, self.exact, self.bare, self.bare_index
        )

    def test_magnitude_like_token_is_not_earthquake_without_event_context(self):
        self.assertEqual(
            cd.detect_category(
                "Mendengar Suara Alam Semesta: NASA Ubah Gambar "
                "Pilar-Pilar Nebula Elang Menjadi Musik",
                "NASA merilis sonifikasi foto M16 melalui nada.",
            ),
            "Lainnya",
        )

    def test_usgs_magnitude_title_is_earthquake(self):
        self.assertEqual(
            cd.detect_category("M 4.5 - Banda Sea", ""),
            "Gempabumi",
        )

    def test_out_of_scope_categories_are_preserved(self):
        for kategori in ("Kebakaran Hutan dan Lahan", "Cuaca Ekstrem"):
            hasil, alasan, cakupan = s5.kategori_final(
                kategori,
                "Green forest fire notification in Indonesia",
                "",
            )
            self.assertEqual(hasil, kategori)
            self.assertEqual(alasan, "dipertahankan_di_luar_8_kategori")
            self.assertEqual(cakupan, "di_luar_8_kategori")

        hasil, alasan, cakupan = s5.kategori_final(
            "Lainnya",
            "Green forest fire notification in Indonesia",
            "",
        )
        self.assertEqual(hasil, "Lainnya")
        self.assertEqual(alasan, "indikasi_karhutla_di_luar_8_kategori")
        self.assertEqual(cakupan, "di_luar_8_kategori")

        hasil, alasan, cakupan = s5.kategori_final(
            "Lainnya",
            "Prakiraan Cuaca Jakarta 19 Oktober: Jaksel dan Jaktim Berpotensi Hujan",
            "",
        )
        self.assertEqual(hasil, "Lainnya")
        self.assertEqual(alasan, "indikasi_cuaca_ekstrem_di_luar_8_kategori")
        self.assertEqual(cakupan, "di_luar_8_kategori")

    def test_glued_bmkg_toponyms(self):
        kasus = [
            (
                "Gempa M5.9 68 km BaratDaya CALANG-ACEHJAYA",
                "Aceh",
                "Kabupaten Aceh Jaya",
            ),
            (
                "Gempa M5.1 105 km BaratDaya SUMBABARATDAYA-NTT",
                "Nusa Tenggara Timur",
                "Kabupaten Sumba Barat Daya",
            ),
            (
                "Gempa M5.7 29 km BaratLaut POHUWATO-GORONTALO",
                "Gorontalo",
                "Kabupaten Pohuwato",
            ),
            (
                "Gempa M5.7 193 km BaratDaya KAB-SUKABUMI-JABAR",
                "Jawa Barat",
                "Kabupaten Sukabumi",
            ),
        ]
        for judul, provinsi, kabupaten in kasus:
            with self.subTest(judul=judul):
                hasil = self.lokasi(judul)
                self.assertEqual(hasil["provinsi"], provinsi)
                self.assertEqual(hasil["kabupaten_kota"], kabupaten)

    def test_non_address_phrases_are_rejected(self):
        kasus = [
            "Truk Tabrak Separator Jalan Dievakuasi, Lalin Arah Cawang Normal",
            "Wapres Lolos dari 3 Dakwaan, tapi Pemakzulan Jalan Terus",
            "Menko Muhaimin: Sekolah Rakyat Bukan Sekadar Pendidikan, "
            "tetapi Jalan Pemberdayaan",
            "Jabar Siapkan 18 Mobile Batching Plant untuk Bangun "
            "Jalan Desa Terpencil",
            "Daftar Jalan Ditutup Sementara Saat Kunjungan Sekjen PBB 17-19",
        ]
        for judul in kasus:
            with self.subTest(judul=judul):
                self.assertEqual(
                    self.lokasi(judul)["alamat_detail"],
                    "",
                )
        self.assertEqual(
            self.lokasi(
                "Truk Tabrak Separator Jalan di MT Haryono, "
                "Lalin Arah Cawang Padat"
            )["alamat_detail"],
            "",
        )
        self.assertEqual(
            self.lokasi(
                "Lalin di Grogol arah Tomang Macet Imbas Mobil "
                "Tabrak Separator Busway",
                "Jl. Letjen MT Haryono menjadi lokasi kejadian.",
            )["alamat_detail"],
            "Jl. Letjen MT Haryono",
        )

    def test_coordinate_verification_and_domain(self):
        dalam = le.ekstrak_koordinat(
            {"url": "https://example.test/?lat=-6.337&lon=129.929"}
        )
        self.assertEqual(dalam["koordinat_status"], "tersedia_sumber")
        self.assertEqual(dalam["koordinat_verifikasi"], "belum_diverifikasi")
        self.assertEqual(dalam["koordinat_domain"], "indonesia")

        luar = le.ekstrak_koordinat(
            {"isi_berita": "Location 11.123 N 86.482 W"}
        )
        self.assertEqual(luar["koordinat_domain"], "luar_indonesia")

        kosong = le.ekstrak_koordinat({})
        self.assertEqual(kosong["koordinat_verifikasi"], "tidak_ada")
        self.assertEqual(kosong["koordinat_domain"], "tidak_diketahui")

    def test_builder_marks_duplicates_without_deleting_rows(self):
        rows = [
            {
                "judul": "Gempa Cianjur",
                "kategori": "Gempa Bumi",
                "provinsi": "",
                "kabupaten_kota": "",
                "alamat_detail": "",
                "url": "https://example.test/a",
                "isi_berita": "Gempa magnitudo 5,0 berpusat di Cianjur.",
            },
            {
                "judul": "Gempa Cianjur",
                "kategori": "Lainnya",
                "provinsi": "",
                "kabupaten_kota": "",
                "alamat_detail": "",
                "url": "https://example.test/b",
                "isi_berita": "Gempa magnitudo 5,0 berpusat di Cianjur.",
            },
        ]
        hasil = s5.bangun_baris(
            rows, self.exact, self.bare, self.bare_index
        )
        self.assertEqual(len(hasil), 2)
        self.assertEqual(hasil[0]["duplikat_judul"], "ya")
        self.assertEqual(hasil[1]["duplikat_judul"], "ya")
        self.assertEqual(hasil[0]["duplikat_dengan"], "2")
        self.assertEqual(hasil[1]["duplikat_dengan"], "1")
        self.assertEqual(hasil[0]["kategori"], "Gempabumi")
        self.assertEqual(hasil[1]["kategori"], "Gempabumi")


if __name__ == "__main__":
    unittest.main(verbosity=2)
