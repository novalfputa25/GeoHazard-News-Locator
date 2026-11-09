# Perbaikan Kualitas Data Stage 5.2

- Tanggal proses: 2026-11-01 14:09 UTC
- Sumber: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261030T125936Z_stage5.csv`
- SHA-256 sumber sebelum: `4a0c3377bddc1672e32e2e1dd6ed313e3a9c2702f64c3d0cbc8f313c9d189f0f`
- SHA-256 sumber sesudah: `4a0c3377bddc1672e32e2e1dd6ed313e3a9c2702f64c3d0cbc8f313c9d189f0f`
- Sumber tidak berubah: **True**
- Keluaran: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261101T140913Z_stage5_2.csv`
- SHA-256 keluaran: `a954df014dd7f6e03051381fb75b9c451bd3e740ba20378d96c05489be860343`
- Mode: non-destruktif; dataset Stage 5 dan CSV historis tidak diubah.

## 1. Ringkasan

- Baris: **787 -> 787** (tidak ada baris dihapus).
- Kolom: **30 -> 36**.
- `domain_lokasi` berubah: **93 baris**.
- `lokasi_verifikasi=perlu_verifikasi`: **7 baris**.
- `lokasi_risiko=tinggi`: **4 baris**.
- Catatan Stage 5.2 terisi: **101 baris**.
- Duplikat judul/URL tetap: **10 / 0** baris.

## 2. Integritas

| Pemeriksaan | Hasil |
|---|---:|
| Baris sumber | 787 |
| Baris keluaran | 787 |
| Kolom sumber | 30 |
| Kolom keluaran | 36 |
| URL unik | 787 |
| Hash sumber tetap | True |

Kolom baru:

- `domain_lokasi_sebelum`
- `domain_lokasi_basis`
- `lokasi_verifikasi`
- `lokasi_basis`
- `lokasi_risiko`
- `catatan_stage5_2`

## 3. Koreksi domain_lokasi

Aturan baru: koordinat -> provinsi -> penanda eksplisit `in/di Indonesia` pada berita terklasifikasi -> `tidak_diketahui`.

| Domain | Sebelum | Sesudah |
|---|---:|---:|
| indonesia | 74 | 99 |
| luar_indonesia | 9 | 9 |
| tidak_diketahui | 704 | 679 |

| Transisi | Jumlah |
|---|---:|
| indonesia -> tidak_diketahui | 34 |
| tidak_diketahui -> indonesia | 59 |

Basis domain:

| Basis | Jumlah |
|---|---:|
| judul | 9 |
| koordinat | 40 |
| provinsi | 59 |
| tidak_diketahui | 679 |

Contoh koreksi:

| Baris | Sebelum | Sesudah | Judul |
|---:|---|---|---|
| 1 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Jambi |
| 2 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Kalimantan Selatan |
| 3 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Kep. Riau |
| 4 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Kep. Bangka Belitung |
| 5 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Sulawesi Tengah |
| 6 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Sumatera Utara |
| 7 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Kalimantan Timur |
| 8 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Aceh |
| 9 | tidak_diketahui | indonesia | Hujan Lebat disertai Petir di Riau |
| 47 | indonesia | tidak_diketahui | Drought is on going in Brunei, Indonesia, Cambodia, Malaysia, Papua New Guinea, Philippine |
| 82 | tidak_diketahui | indonesia | AAJI-Benih Baik salurkan bantuan perlindungan bagi korban gempa NTT |
| 89 | tidak_diketahui | indonesia | DKI izinkan warga non-KTP Jakarta berobat akibat asap karhutla |

## 4. Status verifikasi lokasi

| Status | Jumlah |
|---|---:|
| belum_diverifikasi | 81 |
| perlu_verifikasi | 7 |
| tidak_ada | 699 |

| Risiko | Jumlah |
|---|---:|
| sedang | 3 |
| tidak_dinilai | 780 |
| tinggi | 4 |

Baris yang ditandai:

| Baris | Judul | Provinsi/Kabupaten | Risiko | Catatan |
|---:|---|---|---|---|
| 12 | Gempa M5.7 29 km BaratLaut POHUWATO-GORONTALO | Gorontalo/Kabupaten Pohuwato | sedang | lokasi_rujukan;jarak_29_km;batas_admin_perlu_verifikasi |
| 14 | Gempa M5.1 125 km Tenggara BITUNG-SULUT | Sulawesi Utara/Kota Bitung | tinggi | lokasi_rujukan;jarak_125_km;batas_admin_perlu_verifikasi |
| 17 | Gempa M5.3 219 km TimurLaut TARAKAN-KALTARA | Kalimantan Utara/Kota Tarakan | tinggi | lokasi_rujukan;jarak_219_km;batas_admin_perlu_verifikasi |
| 18 | Gempa M5.9 68 km BaratDaya CALANG-ACEHJAYA | Aceh/Kabupaten Aceh Jaya | tinggi | lokasi_rujukan;jarak_68_km;batas_admin_perlu_verifikasi |
| 19 | Gempa M6.1 14 km BaratDaya KODI-SUMBABARATDAYA-NTT | Nusa Tenggara Timur/Kabupaten Sumba Barat Daya | sedang | lokasi_rujukan;jarak_14_km;batas_admin_perlu_verifikasi |
| 24 | Gempa M5.1 33 km TimurLaut SARMI-PAPUA | Papua/Kabupaten Sarmi | sedang | lokasi_rujukan;jarak_33_km;batas_admin_perlu_verifikasi |
| 27 | Gempa M4.6 Pusat gempa berada di laut 49 km Barat KODI-SUMBABARATDAYA | Nusa Tenggara Timur/Kabupaten Sumba Barat Daya | tinggi | lokasi_rujukan;epicenter_di_laut;batas_admin_perlu_verifikasi |

Baris 27 tetap memakai `Nusa Tenggara Timur` / `Kabupaten Sumba Barat Daya`, tetapi statusnya `perlu_verifikasi` karena epicenter dinyatakan di laut.

## 5. Perubahan lain

- Baris 214 diberi catatan `alamat_dinormalkan`; alamat yang tidak valid tetap dihapus pada Stage 5.
- Penandaan duplikat tidak diubah: 10 baris judul, 0 baris URL.
- Kategori, provinsi, kabupaten/kota, alamat, koordinat, dan `isi_berita` tidak diubah pada Stage 5.2.
- `domain_lokasi_sebelum` menyimpan nilai Stage 5 untuk jejak audit.

## 6. Batas

- Tidak ada verifikasi koordinat independen; 40 koordinat tetap `belum_diverifikasi`.
- Tidak ada scraping atau geocoding online.
- Kabupaten/kota pada tujuh baris tetap berupa rujukan toponimi, bukan batas administratif terverifikasi.
- `domain_lokasi` adalah domain kejadian berbasis bukti teks/koordinat, bukan validasi lapangan.

## 7. Pengujian

- Perintah: `python -m unittest -q test_category_detector test_location_extractor test_stage5_quality test_stage5_2_quality`
- Hasil: 34 test lulus (25 test Stage 2/3/5 + 9 test Stage 5.2).
