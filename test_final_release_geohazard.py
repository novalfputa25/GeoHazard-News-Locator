import unittest

from scripts import finalize_geohazard_release as fr


class FinalReleaseTest(unittest.TestCase):
    def baris(self, **kwargs):
        dasar = {
            "judul": "Uji bahaya geologi",
            "published_time": "Mon, 19 Oct 2026 13:40:00 +0700",
            "event_time": "",
            "event_time_status": "tidak_tersedia",
            "event_time_basis": "tidak_ada_bukti",
            "event_time_evidence": "",
            "sumber": "CNN Indonesia",
            "kategori": "Lainnya",
            "kategori_asal": "Lainnya",
            "kategori_berubah": "tidak",
            "kategori_alasan": "",
            "status_cakupan": "tidak_terklasifikasi",
            "url": "https://example.com/berita",
            "isi_berita": "Informasi umum tanpa tanggal kejadian.",
            "provinsi": "",
            "kabupaten_kota": "",
            "kecamatan": "",
            "desa_kelurahan": "",
            "alamat_detail": "",
            "latitude": "",
            "longitude": "",
            "koordinat_status": "tidak_tersedia",
            "koordinat_verifikasi": "tidak_ada",
            "domain_lokasi": "tidak_diketahui",
            "domain_lokasi_basis": "tidak_diketahui",
            "lokasi_verifikasi": "tidak_ada",
            "lokasi_basis": "tidak_ada",
            "lokasi_risiko": "",
            "duplikat_judul": "tidak",
            "duplikat_url": "tidak",
            "duplikat_dengan": "",
            "catatan_stage5": "",
            "catatan_stage5_2": "",
        }
        dasar.update(kwargs)
        return dasar

    def hasil(self, row, nomor=1):
        return fr.bangun_baris([row], nomor_awal=nomor)[0]

    def test_kategori_target_dipertahankan(self):
        hasil = self.hasil(
            self.baris(kategori="Gempabumi", status_cakupan="dalam_8_kategori")
        )
        self.assertEqual(hasil["kategori"], "Gempabumi")
        self.assertEqual(hasil["kategori_sebelum_final"], "Gempabumi")
        self.assertEqual(hasil["kategori_final_aksi"], "dipertahankan")

    def test_kategori_out_of_scope_dipetakan_ke_lainnya(self):
        hasil = self.hasil(
            self.baris(
                kategori="Cuaca Ekstrem",
                status_cakupan="di_luar_8_kategori",
            )
        )
        self.assertEqual(hasil["kategori"], "Lainnya")
        self.assertEqual(hasil["kategori_sebelum_final"], "Cuaca Ekstrem")
        self.assertEqual(hasil["kategori_final_aksi"], "dipetakan_ke_lainnya")
        self.assertIn("di luar 8 kategori", hasil["catatan_final"])

    def test_kategori_lainnya_dipertahankan(self):
        hasil = self.hasil(
            self.baris(kategori="Lainnya", status_cakupan="di_luar_8_kategori")
        )
        self.assertEqual(hasil["kategori"], "Lainnya")
        self.assertEqual(hasil["kategori_final_aksi"], "dipertahankan")

    def test_published_time_rfc_dinormalisasi_dengan_zona_sumber(self):
        mentah = "Mon, 19 Oct 2026 13:40:00 +0700"
        hasil = self.hasil(self.baris(published_time=mentah))
        self.assertEqual(hasil["published_time"], "2026-10-19T13:40:00+07:00")
        self.assertEqual(hasil["published_time_mentah"], mentah)
        self.assertEqual(hasil["published_time_zona"], "+07:00")
        self.assertEqual(hasil["published_time_format"], "rfc2822")

    def test_published_time_iso_z_dinormalisasi(self):
        mentah = "2026-10-19T07:07:24.040Z"
        hasil = self.hasil(self.baris(published_time=mentah))
        self.assertEqual(hasil["published_time"], "2026-10-19T07:07:24+00:00")
        self.assertEqual(hasil["published_time_zona"], "+00:00")
        self.assertEqual(hasil["published_time_format"], "iso8601")

    def test_published_time_indonesia_dinormalisasi(self):
        mentah = "19 Okt 2026 02:17:05 +0000"
        hasil = self.hasil(self.baris(published_time=mentah))
        self.assertEqual(hasil["published_time"], "2026-10-19T02:17:05+00:00")
        self.assertEqual(hasil["published_time_zona"], "+00:00")
        self.assertEqual(hasil["published_time_format"], "indonesia")

    def test_event_time_jenis_aktual_nowcast_tanggal_dan_unknown(self):
        rows = [
            self.baris(
                event_time="2026-10-19T13:50:00+07:00",
                event_time_status="terekstrak",
                event_time_basis="bmkg_tanggal",
            ),
            self.baris(
                event_time="2026-10-19T13:50:00+08:00",
                event_time_status="terekstrak",
                event_time_basis="bmkg_nowcast",
            ),
            self.baris(
                event_time="2026-10-12",
                event_time_status="tanggal_saja",
                event_time_basis="gdacs_start",
            ),
            self.baris(
                event_time="",
                event_time_status="perlu_review",
                event_time_basis="kandidat_bukan_waktu_kejadian",
            ),
        ]
        hasil = fr.bangun_baris(rows)
        self.assertEqual(hasil[0]["event_time_jenis"], "aktual")
        self.assertEqual(hasil[1]["event_time_jenis"], "prediksi_nowcast")
        self.assertEqual(hasil[2]["event_time_jenis"], "tanggal_saja")
        self.assertEqual(hasil[3]["event_time_jenis"], "tidak_diketahui")

    def test_event_time_tidak_diisi_dari_published_time(self):
        hasil = self.hasil(
            self.baris(
                published_time="2026-10-19T07:00:00+07:00",
                event_time="",
                event_time_status="tidak_tersedia",
            )
        )
        self.assertEqual(hasil["event_time"], "")
        self.assertEqual(hasil["event_time_jenis"], "tidak_diketahui")

    def test_event_time_zona_diambil_dari_nilai(self):
        rows = [
            self.baris(
                event_time="2026-10-19T06:15:13+00:00",
                event_time_status="terekstrak",
            ),
            self.baris(
                event_time="2026-10-06T01:00:00",
                event_time_status="terekstrak",
            ),
            self.baris(
                event_time="2026-10-12",
                event_time_status="tanggal_saja",
            ),
        ]
        hasil = fr.bangun_baris(rows)
        self.assertEqual(hasil[0]["event_time_zona"], "+00:00")
        self.assertEqual(hasil[1]["event_time_zona"], "")
        self.assertEqual(hasil[2]["event_time_zona"], "")

    def test_lokasi_hubungan_membezakan_kejadian_dan_rujukan(self):
        rows = [
            self.baris(
                domain_lokasi_basis="koordinat",
                latitude="-6.2",
                longitude="106.8",
                koordinat_verifikasi="belum_diverifikasi",
            ),
            self.baris(
                domain_lokasi_basis="provinsi",
                provinsi="Jawa Barat",
                kabupaten_kota="Kabupaten Bogor",
                lokasi_verifikasi="belum_diverifikasi",
            ),
            self.baris(
                domain_lokasi_basis="judul",
                provinsi="",
                kabupaten_kota="",
            ),
            self.baris(domain_lokasi_basis="tidak_diketahui"),
        ]
        hasil = fr.bangun_baris(rows)
        self.assertEqual(hasil[0]["lokasi_hubungan"], "titik_kejadian_terindikasi")
        self.assertEqual(hasil[1]["lokasi_hubungan"], "rujukan_admin_belum_verifikasi")
        self.assertEqual(hasil[2]["lokasi_hubungan"], "domain_disebut_dalam_judul")
        self.assertEqual(hasil[3]["lokasi_hubungan"], "tidak_diketahui")

    def test_lokasi_presisi_tidak_mengklaim_titik_terverifikasi(self):
        rows = [
            self.baris(domain_lokasi_basis="koordinat", latitude="1", longitude="2"),
            self.baris(
                domain_lokasi_basis="provinsi",
                provinsi="Aceh",
                kabupaten_kota="Kabupaten Aceh Jaya",
            ),
            self.baris(domain_lokasi_basis="provinsi", provinsi="Aceh"),
            self.baris(domain_lokasi_basis="judul"),
        ]
        hasil = fr.bangun_baris(rows)
        self.assertEqual(hasil[0]["lokasi_presisi"], "titik_terindikasi")
        self.assertEqual(hasil[1]["lokasi_presisi"], "kabupaten_kota")
        self.assertEqual(hasil[2]["lokasi_presisi"], "provinsi")
        self.assertEqual(hasil[3]["lokasi_presisi"], "domain_negara")

    def test_duplikat_isi_ditandai_tanpa_menghapus_baris(self):
        rows = [
            self.baris(
                judul="Berita A",
                url="https://example.com/a",
                isi_berita="Isi identik.",
            ),
            self.baris(
                judul="Berita B",
                url="https://example.com/b",
                isi_berita="Isi identik.",
            ),
        ]
        hasil = fr.bangun_baris(rows)
        self.assertEqual(len(hasil), 2)
        self.assertEqual([r["duplikat_isi"] for r in hasil], ["ya", "ya"])
        self.assertEqual(hasil[0]["duplikat_kelompok"], "isi:1-2")
        self.assertEqual(hasil[1]["duplikat_kelompok"], "isi:1-2")

    def test_duplikat_judul_tidak_menghapus_kejadian_berbeda(self):
        rows = [
            self.baris(judul="Judul sama", url="https://example.com/a"),
            self.baris(judul="Judul sama", url="https://example.com/b"),
        ]
        hasil = fr.bangun_baris(rows)
        self.assertEqual(len(hasil), 2)
        self.assertEqual([r["duplikat_judul"] for r in hasil], ["ya", "ya"])

    def test_row_216_desa_generik_dikosongkan(self):
        hasil = self.hasil(
            self.baris(
                judul="Aceh Barat Daya Hujan Deras, Sejumlah Desa Banjir",
                provinsi="Aceh",
                desa_kelurahan="Banjir",
            ),
            nomor=216,
        )
        self.assertEqual(hasil["desa_kelurahan"], "")
        self.assertIn("kata umum", hasil["catatan_final"])

    def test_bangun_baris_mempertahankan_kolom_lama(self):
        row = self.baris(
            judul="Judul asli",
            provinsi="Jambi",
            event_time="2026-10-18",
            event_time_status="tanggal_saja",
            event_time_basis="isi_berita",
            catatan_stage5_2="catatan lama",
        )
        hasil = self.hasil(row)
        for field in (
            "judul",
            "sumber",
            "provinsi",
            "event_time",
            "event_time_status",
            "event_time_basis",
            "catatan_stage5_2",
        ):
            self.assertEqual(hasil[field], row[field])

    def test_validasi_menerima_baris_final_yang_konsisten(self):
        hasil = self.hasil(self.baris())
        validasi = fr.validasi([hasil], jumlah_diharapkan=1)
        self.assertEqual(validasi["errors"], [])

    def test_validasi_menolak_kategori_final_di_luar_kontrak(self):
        hasil = self.hasil(self.baris())
        hasil["kategori"] = "Cuaca Ekstrem"
        validasi = fr.validasi([hasil], jumlah_diharapkan=1)
        self.assertTrue(any("kategori final" in x for x in validasi["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
