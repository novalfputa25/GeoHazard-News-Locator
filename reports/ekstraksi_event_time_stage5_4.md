# Ekstraksi Event Time Stage 5.4

- Tanggal proses: 2026-11-01 14:45 UTC
- Sumber: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261101T140913Z_stage5_2.csv`
- SHA-256 sumber sebelum: `a954df014dd7f6e03051381fb75b9c451bd3e740ba20378d96c05489be860343`
- SHA-256 sumber sesudah: `a954df014dd7f6e03051381fb75b9c451bd3e740ba20378d96c05489be860343`
- Sumber tidak berubah: **True**
- Keluaran: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261101T144531Z_stage5_4.csv`
- SHA-256 keluaran: `bb1bc6d4343d2b8bb1982677d09a1e6f4183dc5032f1845335299bc38c5c20db`
- Mode: non-destruktif; kategori, lokasi, dan data historis tidak diubah.

## 1. Ringkasan

- Baris: **787 -> 787** (tidak ada baris dihapus).
- Kolom: **36 -> 39**.
- `event_time` terisi: **64 baris**; kosong: **723 baris**.
- `event_time` berisi tanggal saja: **13 baris**.
- `event_time` berisi tanggal dan jam: **51 baris**.
- `perlu_review`: **14 baris**.
- `tidak_tersedia`: **709 baris**.
- Waktu publikasi tersedia: **787 baris**.
- Kolom selain `event_time` dan tiga kolom baru berubah: **0 sel**.

## 1a. Jawaban audit

- Memiliki `event_time` yang dipakai: **64 baris** (51 tanggal+jam, 13 tanggal saja).
- Menyebut jam kejadian eksplisit: **51 baris**.
- Tanpa `event_time` yang aman: **723 baris** (709 tanpa kandidat, 14 perlu review).
- Hanya memiliki `published_time` dan tidak punya kandidat event: **709 baris**.
- BMKG: **38/38 terekstrak**.
- USGS: **11/11 terekstrak**.
- GDACS: **1 terekstrak, 8 tanggal saja, 1 tanpa tanggal**.
- Berita umum: **1 terekstrak, 5 tanggal saja, 14 perlu review**.

## 2. Integritas

| Pemeriksaan | Hasil |
|---|---:|
| Baris sumber | 787 |
| Baris keluaran | 787 |
| Kolom sumber | 36 |
| Kolom keluaran | 39 |
| URL unik | 787 |
| Hash sumber tetap | True |
| Judul duplikat | 10 |
| URL duplikat | 0 |

Kolom baru:

- `event_time_status`
- `event_time_basis`
- `event_time_evidence`

## 3. Distribusi status

| Status | Jumlah |
|---|---:|
| terekstrak | 51 |
| tanggal_saja | 13 |
| perlu_review | 14 |
| tidak_tersedia | 709 |

| Basis | Jumlah |
|---|---:|
| bmkg_nowcast | 9 |
| bmkg_tanggal | 29 |
| gdacs_judul | 1 |
| gdacs_start | 8 |
| isi_berita | 5 |
| isi_berita_tanpa_zona | 1 |
| kandidat_bukan_waktu_kejadian | 8 |
| kandidat_rentang_tanggal | 1 |
| kandidat_tanggal_tanpa_tahun | 5 |
| tidak_ada_bukti | 624 |
| tidak_ada_tanggal_kejadian | 85 |
| usgs_time | 11 |

## 4. Status per sumber

| Sumber / status | Jumlah |
|---|---:|
| ANTARA / tidak_tersedia | 97 |
| ANTARA Jatim / tidak_tersedia | 20 |
| BBC Indonesia / tidak_tersedia | 21 |
| BMKG / terekstrak | 38 |
| CNBC Indonesia / tanggal_saja | 1 |
| CNBC Indonesia / tidak_tersedia | 99 |
| CNN Indonesia / perlu_review | 6 |
| CNN Indonesia / tanggal_saja | 1 |
| CNN Indonesia / tidak_tersedia | 93 |
| GDACS / tanggal_saja | 8 |
| GDACS / terekstrak | 1 |
| GDACS / tidak_tersedia | 1 |
| Liputan6 / perlu_review | 1 |
| Liputan6 / tanggal_saja | 2 |
| Liputan6 / tidak_tersedia | 47 |
| Media Indonesia / perlu_review | 1 |
| Media Indonesia / tidak_tersedia | 99 |
| Mongabay / perlu_review | 2 |
| Mongabay / tanggal_saja | 1 |
| Mongabay / terekstrak | 1 |
| Mongabay / tidak_tersedia | 16 |
| Republika / perlu_review | 1 |
| Republika / tidak_tersedia | 14 |
| SINDOnews / tidak_tersedia | 30 |
| Tempo / perlu_review | 2 |
| Tempo / tidak_tersedia | 48 |
| USGS / terekstrak | 11 |
| detikcom / tidak_tersedia | 100 |
| kumparan / perlu_review | 1 |
| kumparan / tidak_tersedia | 24 |

## 5. Bukti yang dipakai

- BMKG: waktu eksplisit pada `Tanggal:` atau kalimat nowcast `akan terjadi pada ... WIB/WITA/WIT`.
- USGS: waktu eksplisit `Time ... UTC`.
- GDACS: tanggal mulai kebakaran atau waktu gempa pada judul; tanggal saja tidak diberi jam.
- Berita umum: hanya tanggal/jam yang dekat dengan peristiwa hazard dan bukan tanggal kebijakan, laporan, promo, atau tenggat.
- Tidak ada penggunaan `published_time` sebagai `event_time`.

Contoh hasil `terekstrak`:

| Baris | Sumber | event_time | Bukti |
|---:|---|---|---|
| 1 | BMKG | 2026-10-19T13:50:00+07:00 | akan terjadi pada 19 October 2026, 13:50 WIB |
| 2 | BMKG | 2026-10-19T14:52:00+08:00 | akan terjadi pada 19 October 2026, 14:52 WITA |
| 3 | BMKG | 2026-10-19T13:35:00+07:00 | akan terjadi pada 19 October 2026, 13:35 WIB |
| 4 | BMKG | 2026-10-19T13:00:00+07:00 | akan terjadi pada 19 October 2026, 13:00 WIB |
| 5 | BMKG | 2026-10-19T13:53:00+08:00 | akan terjadi pada 19 October 2026, 13:53 WITA |
| 6 | BMKG | 2026-10-19T12:40:00+07:00 | akan terjadi pada 19 October 2026, 12:40 WIB |
| 7 | BMKG | 2026-10-19T13:30:00+08:00 | akan terjadi pada 19 October 2026, 13:30 WITA |
| 8 | BMKG | 2026-10-19T12:13:00+07:00 | akan terjadi pada 19 October 2026, 12:13 WIB |

Contoh hasil `tanggal_saja`:

| Baris | Sumber | event_time | Bukti |
|---:|---|---|---|
| 39 | GDACS | 2026-10-12 | On 12/10/2026, a forest fire started |
| 40 | GDACS | 2026-10-07 | On 07/10/2026, a forest fire started |
| 41 | GDACS | 2026-10-05 | On 05/10/2026, a forest fire started |
| 42 | GDACS | 2026-10-04 | On 04/10/2026, a forest fire started |
| 43 | GDACS | 2026-10-04 | On 04/10/2026, a forest fire started |
| 44 | GDACS | 2026-10-03 | On 03/10/2026, a forest fire started |
| 45 | GDACS | 2026-10-03 | On 03/10/2026, a forest fire started |
| 46 | GDACS | 2026-10-01 | On 01/10/2026, a forest fire started |

Contoh hasil `perlu_review`:

| Baris | Sumber | Alasan | Bukti |
|---:|---|---|---|
| 290 | CNN Indonesia | kandidat_bukan_waktu_kejadian | ...di, sementara petugas berjibaku memadamkan api di tengah perpanjangan status tanggap darurat hingga 9 November 2026. |
| 301 | CNN Indonesia | kandidat_tanggal_tanpa_tahun | Asap tebal membubung di sebagian wilayah Sumatra Selatan pada Minggu (18/10). |
| 343 | CNN Indonesia | kandidat_bukan_waktu_kejadian | ...Tengger Semeru (BB TNBTS) resmi memberlakukan pembatasan akses wisata di kawasan Gunung Bromo mulai 17 Oktober 2026. |
| 345 | CNN Indonesia | kandidat_tanggal_tanpa_tahun | Kota Palembang kembali diselimuti kabut asap tebal pada Minggu (18/10) pagi setelah sempat menipis pada Sabtu (17/10) siang. |
| 349 | CNN Indonesia | kandidat_bukan_waktu_kejadian | Mulai 17 Oktober 2026, status Gunung Sinabung di Sumatera Utara diturunkan dari Siaga menjadi Waspada. |
| 368 | CNN Indonesia | kandidat_tanggal_tanpa_tahun | ...r 20 tahun berhasil diselamatkan dari kawasan terdampak kebakaran hutan dan lahan di Kalimantan Tengah, Rabu (1/10). |
| 477 | Tempo | kandidat_bukan_waktu_kejadian | Berdasarkan laporan harian Satgas PRR per 12 Oktober 2026, sebanyak 1.198 sumur bor telah selesai dibangun di Provinsi Aceh, Sumatera Utara, dan Sumat |
| 510 | Tempo | kandidat_rentang_tanggal | ...emerintah Provinsi Lampung mengalihkan kegiatan belajar mengajar menjadi pembelajaran daring pada 7-8 September 2026 sebagai langkah antisipasi ter |
| 568 | Liputan6 | kandidat_bukan_waktu_kejadian | BMKG memantau sebaran asap karhutla mulai menjauhi Jabodetabek sejak 17 Oktober 2026. Namun, kualitas udara di sejumlah titik Jakarta masih berada pad |
| 582 | Republika | kandidat_bukan_waktu_kejadian | ...ap kebakaran hutan dan lahan (karhutla) dari Kalimantan telah menjauhi wilayah Jakarta sejak Sabtu (17/10/2026). Meski demikian, kualitas udara... |

## 6. Batas

- 709 baris tidak memiliki tanggal/jam kejadian eksplisit; `event_time` dibiarkan kosong.
- 14 baris memiliki kandidat tanggal tetapi belum aman dipakai sebagai `event_time`.
- Tanggal tanpa tahun tidak ditebak; baris tersebut masuk `perlu_review`.
- Waktu tanpa zona waktu dinormalisasi tanpa offset dan ditandai `isi_berita_tanpa_zona`.
- Tanggal kebijakan, laporan, data, promo, tenggat, dan aktivitas non-hazard tidak dijadikan `event_time`.
- Tidak ada verifikasi online, scraping baru, atau geocoding.

## 7. Pengujian

- Perintah: `python -m unittest -q test_stage5_4_event_time`
- Hasil: 13 test Stage 5.4 lulus; 47 test terarah total lulus.
