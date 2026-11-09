# Perbaikan Kualitas Data Stage 5

- Tanggal proses: 2026-10-30 12:59 UTC
- Sumber: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261029T143308Z.csv`
- SHA-256 sumber sebelum: `5d1d3832e41fe6641ebedf4fe35c03a81aedf77d3bd3661e26ba91f6ffc7a6eb`
- SHA-256 sumber sesudah: `5d1d3832e41fe6641ebedf4fe35c03a81aedf77d3bd3661e26ba91f6ffc7a6eb`
- Sumber tidak berubah: **True**
- Keluaran: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261030T125936Z_stage5.csv`
- SHA-256 keluaran: `4a0c3377bddc1672e32e2e1dd6ed313e3a9c2702f64c3d0cbc8f313c9d189f0f`
- Mode: non-destruktif; tanpa scraping, geocoding online, atau penghapusan baris.

## 1. Ringkasan

- Baris: **787 -> 787** (tidak ada baris dihapus).
- Kategori berubah (termasuk penyeragaman nama): **50 baris**.
- Perubahan kategori substantif: **12 baris**.
- Provinsi berubah/terisi baru: **2 baris**.
- Kabupaten/kota berubah/terisi baru: **7 baris**.
- Alamat tidak valid dihapus: **6 baris**.
- Lainnya berindikasi di luar 8 kategori: **17 baris**.
- Koordinat berstatus belum diverifikasi: **40 baris**.
- Koordinat domain luar Indonesia: **9 baris**.
- Baris ditandai duplikat judul: **10 baris**.
- Baris ditandai duplikat URL: **0 baris**.

## 2. Kategori

Cakupan final tetap **delapan kategori wajib + Lainnya**. Kebakaran Hutan dan Lahan serta Cuaca Ekstrem dipertahankan sebagai baris lama di luar cakupan, bukan ditambahkan sebagai kategori baru.

### Sebelum
| Nilai | Jumlah |
|---|---:|
| Lainnya | 661 |
| Kebakaran Hutan dan Lahan | 71 |
| Gempa Bumi | 33 |
| Cuaca Ekstrem | 14 |
| Gunung Api | 4 |
| Abrasi dan Akresi | 3 |
| Gerakan Tanah / Longsor | 1 |

### Sesudah
| Nilai | Jumlah |
|---|---:|
| Lainnya | 649 |
| Kebakaran Hutan dan Lahan | 71 |
| Gempabumi | 44 |
| Cuaca Ekstrem | 14 |
| Gunungapi | 5 |
| Abrasi dan Akresi | 3 |
| Gerakan Tanah/Tanah Longsor | 1 |

### Perubahan kategori substantif
| Baris | Judul | Dari | Ke | Alasan |
|---:|---|---|---|---|
| 49 | M 4.5 - Banda Sea | Lainnya | Gempabumi | judul:Gempabumi |
| 50 | M 4.9 - 68 km WSW of San Juan del Sur, Nicaragua | Lainnya | Gempabumi | judul:Gempabumi |
| 51 | M 4.5 - Fiji region | Lainnya | Gempabumi | judul:Gempabumi |
| 52 | M 5.1 - 129 km SSE of Kokopo, Papua New Guinea | Lainnya | Gempabumi | judul:Gempabumi |
| 53 | M 4.7 - 147 km SSW of Kokopo, Papua New Guinea | Lainnya | Gempabumi | judul:Gempabumi |
| 54 | M 5.2 - 71 km ESE of ‘Ohonua, Tonga | Lainnya | Gempabumi | judul:Gempabumi |
| 55 | M 4.5 - 0 km NE of Río Grande, Panama | Lainnya | Gempabumi | judul:Gempabumi |
| 56 | M 4.7 - 20 km SW of Sandy Point Town, Saint Kitts and Nevis | Lainnya | Gempabumi | judul:Gempabumi |
| 57 | M 4.6 - Carlsberg Ridge | Lainnya | Gempabumi | judul:Gempabumi |
| 58 | M 4.5 - Kermadec Islands, New Zealand | Lainnya | Gempabumi | judul:Gempabumi |
| 59 | M 5.2 - 55 km NNW of Ruteng, Indonesia | Lainnya | Gempabumi | judul:Gempabumi |
| 510 | Gubernur Lampung Alihkan KBM ke Daring Akibat Sebaran Abu Anak Krakatau | Lainnya | Gunungapi | isi:Gunungapi |

Penyeragaman nama kategori tanpa perubahan makna: **38 baris** (Gempa Bumi -> Gempabumi, Gunung Api -> Gunungapi, Gerakan Tanah / Longsor -> Gerakan Tanah/Tanah Longsor).

### Lainnya berindikasi di luar 8 kategori

| Baris | Judul | Indikasi |
|---:|---|---|
| 39 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 40 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 41 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 42 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 43 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 44 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 45 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 46 | Green forest fire notification in Indonesia | indikasi_karhutla_di_luar_8_kategori |
| 70 | Apa itu modifikasi cuaca? Ini cara kerja hujan buatan BMKG | indikasi_cuaca_ekstrem_di_luar_8_kategori |
| 119 | Merawat Lucipara, menjaga laut dan kehidupan masyarakat | indikasi_karhutla_di_luar_8_kategori |
| 134 | Foto Pilihan pekan ketiga Oktober 2026 | indikasi_karhutla_di_luar_8_kategori |
| 335 | Kualitas Udara Sumsel Diklaim Membaik usai Dilakukan OMC Dry Ice | indikasi_karhutla_di_luar_8_kategori |
| 345 | Palembang Kembali Diselimuti Kabut Asap Tebal Minggu Pagi | indikasi_karhutla_di_luar_8_kategori |
| 379 | Video: Kabut Asap RI Menggila, ASEAN Umumkan Status Siaga Tertinggi | indikasi_karhutla_di_luar_8_kategori |
| 547 | Prakiraan Cuaca Jakarta 19 Oktober: Jaksel dan Jaktim Berpotensi Hujan | indikasi_cuaca_ekstrem_di_luar_8_kategori |
| 576 | Kondisi Terkini Kabut Asap Palangka Raya Usai Diguyur Hujan | indikasi_karhutla_di_luar_8_kategori |
| 737 | Foto: Persiapan Operasi Modifikasi Cuaca di Palembang | indikasi_karhutla_di_luar_8_kategori |

## 3. Lokasi administratif

| Kolom | Sebelum terisi | Sesudah terisi |
|---|---:|---:|
| provinsi | 87 | 88 |
| kabupaten_kota | 34 | 40 |
| kecamatan | 0 | 0 |
| desa_kelurahan | 1 | 1 |
| alamat_detail | 13 | 7 |

Perubahan lokasi:
| Baris | Judul | Sebelum | Sesudah |
|---:|---|---|---|
| 12 | Gempa M5.7 29 km BaratLaut POHUWATO-GORONTALO | Gorontalo/ | Gorontalo/Kabupaten Pohuwato |
| 14 | Gempa M5.1 125 km Tenggara BITUNG-SULUT | Sulawesi Utara/ | Sulawesi Utara/Kota Bitung |
| 17 | Gempa M5.3 219 km TimurLaut TARAKAN-KALTARA | Kalimantan Utara/ | Kalimantan Utara/Kota Tarakan |
| 18 | Gempa M5.9 68 km BaratDaya CALANG-ACEHJAYA | / | Aceh/Kabupaten Aceh Jaya |
| 19 | Gempa M6.1 14 km BaratDaya KODI-SUMBABARATDAYA-NTT | Nusa Tenggara Timur/ | Nusa Tenggara Timur/Kabupaten Sumba Barat Daya |
| 24 | Gempa M5.1 33 km TimurLaut SARMI-PAPUA | Papua/ | Papua/Kabupaten Sarmi |
| 27 | Gempa M4.6 Pusat gempa berada di laut 49 km Barat KODI-SUMBABARATDAYA | Nusa Tenggara Barat/Kota Bima | Nusa Tenggara Timur/Kabupaten Sumba Barat Daya |

## 4. Alamat

Alamat yang hanya berupa frasa non-alamat dihapus. Alamat jalan yang masih didukung konteks dipertahankan.

| Baris | Alamat lama | Judul |
|---:|---|---|
| 187 | Jalan Desa Terpencil | Jabar Siapkan 18 Mobile Batching Plant untuk Bangun Jalan Desa Terpencil |
| 242 | Jalan Dievakuasi | Truk Tabrak Separator Jalan Dievakuasi, Lalin Arah Cawang Normal |
| 376 | Jalan Ditutup Sementara Saat Kunjungan Sekjen PBB 17-19 | Daftar Jalan Ditutup Sementara Saat Kunjungan Sekjen PBB 17-19 Oktober |
| 433 | Jalan Ditutup Sementara 19 | Ada Tamu Negara Penting, Cek Daftar Jalan Ditutup Sementara 19 Oktober |
| 470 | Jalan Terus | Wapres Lolos dari 3 Dakwaan, tapi Pemakzulan Jalan Terus |
| 533 | Jalan Pemberdayaan | Menko Muhaimin: Sekolah Rakyat Bukan Sekadar Pendidikan, tetapi Jalan Pemberdayaan |

## 5. Koordinat dan domain

| Status | Jumlah |
|---|---:|
| tersedia_sumber | 40 |
| tidak_ada | 747 |

| Verifikasi | Jumlah |
|---|---:|
| belum_diverifikasi | 40 |
| tidak_ada | 747 |

| Domain lokasi (perkiraan) | Jumlah |
|---|---:|
| indonesia | 74 |
| luar_indonesia | 9 |
| tidak_diketahui | 704 |

Tidak ada koordinat yang ditandai `terverifikasi_independen` karena tidak ada pembanding resmi independen dalam proses offline ini.

## 6. Duplikasi

| Jenis | Baris ditandai |
|---|---:|
| Judul | 10 |
| URL | 0 |

Duplikat hanya ditandai, tidak dihapus atau digabung.

## 7. Batas dan keterbatasan

- Tidak ada verifikasi koordinat independen; status tetap `belum_diverifikasi`.
- Tidak ada scraping atau geocoding online.
- Tidak ada perubahan pada `feeds.py`, konfigurasi sumber, atau CSV sumber.
- Baris Kebakaran Hutan dan Lahan/Cuaca Ekstrem lama dipertahankan dan diberi status di luar cakupan.
- Klasifikasi tetap heuristik dan belum menjadi keputusan kategori final yang tervalidasi manual.
- Stage 5 memperbaiki kualitas, tetapi dataset belum layak disebut tervalidasi penuh.

## 8. Pengujian

- Perintah: `python -m unittest -v test_category_detector test_location_extractor test_stage5_quality`
- Hasil: **25 test lulus** (Stage 2, Stage 3, dan Stage 5).

## Lampiran: kolom baru

- `kategori_asal`
- `kategori_berubah`
- `kategori_alasan`
- `status_cakupan`
- `domain_lokasi`
- `duplikat_judul`
- `duplikat_url`
- `duplikat_dengan`
- `catatan_stage5`
- `koordinat_verifikasi`
- `koordinat_domain`
