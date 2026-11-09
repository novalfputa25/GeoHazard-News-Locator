# Validasi Kualitas Data Stage 4

- Tanggal audit: 2026-10-30 12:44 UTC
- Sumber: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261029T143308Z.csv`
- SHA-256 sumber: `5d1d3832e41fe6641ebedf4fe35c03a81aedf77d3bd3661e26ba91f6ffc7a6eb`
- Jumlah baris data: **787**
- Jumlah kolom: **19**
- Mode: read-only; tanpa scraping, tanpa geocoding online, tanpa perubahan CSV.

## 1. Ringkasan hasil audit

- Provinsi terisi: **87 baris (11.05%)**, dengan **29 provinsi unik**.
- Kabupaten/kota terisi: **34 baris (4.32%)**, dengan **22 kabupaten/kota unik**.
- Koordinat lengkap: **40 baris (5.08%)**; parsial **0**; invalid numerik/rentang **0**.
- Koordinat terverifikasi independen: **0**; semua 40 koordinat baru berstatus ditemukan dari sumber dan belum diverifikasi terhadap kejadian.
- Kelompok temuan: **12**; baris unik yang tersentuh minimal satu flag: **770 dari 787 (97.84%)**. Angka baris ini tumpang tindih dan bukan jumlah masalah independen.
- **Kesimpulan awal:** dataset belum layak disebut tervalidasi; layak sebagai kandidat untuk review manual, bukan untuk analisis spasial final.

## 2. Statistik kelengkapan data

| Kolom / kondisi | Terisi | Persentase |
|---|---|---|
| provinsi | 87 | 11.05% |
| kabupaten_kota | 34 | 4.32% |
| kecamatan | 0 | 0.00% |
| desa_kelurahan | 1 | 0.13% |
| latitude | 40 | 5.08% |
| longitude | 40 | 5.08% |
| latitude + longitude lengkap | 40 | 5.08% |

Catatan: 689 baris tidak memiliki satu pun kolom lokasi administratif; 98 baris memiliki minimal satu kolom lokasi administratif.

## 3. Statistik koordinat

| Kondisi | Jumlah | Persentase |
|---|---|---|
| Kosong (latitude dan longitude kosong) | 747 | 94.92% |
| Parsial (salah satu kosong) | 0 | 0.00% |
| Lengkap | 40 | 5.08% |
| Bukan angka | 0 | 0.00% |
| Latitude di luar -90..90 | 0 | 0.00% |
| Longitude di luar -180..180 | 0 | 0.00% |
| Nilai 0,0 | 0 | 0.00% |

| koordinat_sumber | Jumlah | Catatan |
|---|---|---|
| URL BMKG | 29 | Koordinat dari parameter URL BMKG |
| isi BMKG | 0 | Tidak ditemukan pada dataset ini |
| isi USGS | 11 | Koordinat dari teks isi USGS |
| lainnya/kosong | 0 | Perlu review |

Rentang nilai: latitude -30.127 sampai 17.253; longitude -178.659 sampai 152.616. Pasangan koordinat unik: 40 dari 40 baris berkoordinat.

**Status verifikasi:** 0 dari 40 koordinat diverifikasi independen. Nilai yang lolos pemeriksaan angka/rentang tidak otomatis membuktikan koordinat tersebut adalah episenter atau lokasi kejadian yang benar.

## 4. Statistik lokasi administratif

| Kondisi | Jumlah | Persentase |
|---|---|---|
| Provinsi terisi | 87 | 11.05% |
| Kabupaten/kota terisi | 34 | 4.32% |
| Provinsi dan kabupaten/kota terisi | 34 | 4.32% |
| Provinsi terisi tanpa kabupaten/kota | 53 | 6.73% |
| Provinsi kosong | 700 | 88.95% |
| Seluruh kolom lokasi administratif kosong | 689 | 87.55% |
| Koordinat lengkap tanpa provinsi | 12 | 1.52% |
| Koordinat lengkap tanpa kabupaten/kota | 25 | 3.18% |

**Provinsi terbanyak:**

| Provinsi | Jumlah baris |
|---|---|
| Kalimantan Tengah | 11 |
| DKI Jakarta | 10 |
| Nusa Tenggara Timur | 8 |
| Jawa Barat | 7 |
| Sumatera Selatan | 6 |
| Aceh | 4 |
| Sulawesi Tengah | 3 |
| Sulawesi Utara | 3 |
| Sulawesi Selatan | 3 |
| Jawa Timur | 3 |

**Kabupaten/kota terbanyak:**

| Kabupaten/kota | Jumlah baris |
|---|---|
| Kota Palangka Raya | 4 |
| Kota Bogor | 3 |
| Kota Palembang | 3 |
| Kota Jambi | 2 |
| Kabupaten Manggarai | 2 |
| Kabupaten Sukabumi | 2 |
| Kabupaten Sumba Barat Daya | 2 |
| Kabupaten Enrekang | 2 |
| Kabupaten Belitung | 1 |
| Kabupaten Morowali Utara | 1 |

## 5. Distribusi kategori

| Kategori | Jumlah | Persentase |
|---|---|---|
| Lainnya | 661 | 83.99% |
| Kebakaran Hutan dan Lahan | 71 | 9.02% |
| Gempa Bumi | 33 | 4.19% |
| Cuaca Ekstrem | 14 | 1.78% |
| Gunung Api | 4 | 0.51% |
| Abrasi dan Akresi | 3 | 0.38% |
| Gerakan Tanah / Longsor | 1 | 0.13% |

Jumlah kategori unik: **7**. Kategori `Lainnya` mencakup 661 baris (83.99%), sehingga sebagian besar dataset belum memiliki kategori geohazard spesifik.

## 6. Pemeriksaan konsistensi

### 6.1 Kategori vs judul

- Kategori spesifik yang judulnya tidak memuat kata kunci kategori: **2 baris**.
  - baris data 160: `Polri tindaklanjuti arahan Presiden siapkan Polisi Khusus Kehutanan`
  - baris data 368: `Aksi Penyelamatan Orangutan di Sebuah Kebun Kalimantan Tengah`
- Kategori `Lainnya` yang judulnya memuat indikasi kuat karhutla/asap: **11 baris**; dengan indikasi hazard yang lebih luas (termasuk cuaca/modifikasi): **14 baris**.
  - baris data 39: `Green forest fire notification in Indonesia`
  - baris data 40: `Green forest fire notification in Indonesia`
  - baris data 41: `Green forest fire notification in Indonesia`
  - baris data 42: `Green forest fire notification in Indonesia`
  - baris data 43: `Green forest fire notification in Indonesia`
  - baris data 44: `Green forest fire notification in Indonesia`
  - baris data 45: `Green forest fire notification in Indonesia`
  - baris data 46: `Green forest fire notification in Indonesia`
  - baris data 70: `Apa itu modifikasi cuaca? Ini cara kerja hujan buatan BMKG`
  - baris data 345: `Palembang Kembali Diselimuti Kabut Asap Tebal Minggu Pagi`
  - baris data 379: `Video: Kabut Asap RI Menggila, ASEAN Umumkan Status Siaga Tertinggi`
  - baris data 547: `Prakiraan Cuaca Jakarta 19 Oktober: Jaksel dan Jaktim Berpotensi Hujan`
  - baris data 576: `Kondisi Terkini Kabut Asap Palangka Raya Usai Diguyur Hujan`
  - baris data 737: `Foto: Persiapan Operasi Modifikasi Cuaca di Palembang`

### 6.2 Lokasi judul vs isi

- Kandidat output provinsi yang tidak muncul di judul: **0 baris**.
- Kandidat judul dan isi menyebut provinsi yang berbeda: **1 baris**. Ini hanya heuristic tingkat provinsi, bukan bukti konflik.
  - baris data 197: `Mobil Satgas TNI Terjun ke Jurang Yalimo Papua, 4 Prajurit Gugur`; judul: Papua; isi: Papua Pegunungan; output: `(kosong)`

### 6.3 Duplikasi URL dan judul

- URL non-kosong: **787 unik**; grup URL duplikat: **0**; baris tambahan: **0**.
- Judul dinormalisasi: **779 unik**; grup judul duplikat: **2**; baris terlibat: **10**; baris tambahan: **8**.
  - 8x `green forest fire notification in indonesia`
  - 2x `pengacara kamaruddin simanjuntak meninggal dunia`

## 7. Daftar masalah yang ditemukan

| No | Temuan | Jumlah | Dampak | Prioritas |
|---|---|---|---|---|
| 1 | Kategori Lainnya dominan | 661 baris | Distribusi kategori tidak spesifik | Tinggi |
| 2 | Provinsi kosong | 700 baris | Lokasi administratif tidak dapat dipakai | Tinggi |
| 3 | Provinsi terisi tanpa kabupaten/kota | 53 baris | Lokasi hanya sampai tingkat provinsi | Sedang |
| 4 | Koordinat tanpa provinsi | 12 baris | Koordinat ada, lokasi administratif kosong | Tinggi |
| 5 | Koordinat tanpa kabupaten/kota | 25 baris | Koordinat ada, lokasi belum lengkap | Sedang |
| 6 | alamat_detail terisi tetapi provinsi kosong | 11 baris | Indikasi alamat palsu/tidak lengkap | Sedang |
| 7 | Koordinat belum diverifikasi independen | 40 baris | Status hanya tersedia dari sumber | Tinggi |
| 8 | Indikasi berita luar Indonesia | 9 baris | Perlu pemisahan domain Indonesia/luar | Sedang |
| 9 | Kategori Lainnya dengan indikasi kuat hazard | 11 baris | Kemungkinan kategori kurang tepat | Tinggi |
| 10 | Judul Karhutla tanpa kata kunci hazard | 2 baris | Perlu review judul vs isi | Rendah |
| 11 | Duplikasi judul | 10 baris / 2 grup | Perlu deduplikasi berbasis sumber/URL | Sedang |
| 12 | CALANG-ACEHJAYA lokasi kosong | 1 baris | Toponimi BMKG menempel tanpa spasi | Sedang |

**Jumlah kelompok masalah: 12.** **Baris unik dengan minimal satu flag: 770/787.** **Baris tanpa flag: 17.**

## 8. Contoh baris yang perlu diperiksa manual

### 8.1 Koordinat lengkap tetapi provinsi kosong

- baris data 18: `Gempa M5.9 68 km BaratDaya CALANG-ACEHJAYA`; sumber `URL BMKG`; lat `4.56`, lon `94.97`
- baris data 49: `M 4.5 - Banda Sea`; sumber `isi USGS`; lat `-6.337`, lon `129.929`
- baris data 50: `M 4.9 - 68 km WSW of San Juan del Sur, Nicaragua`; sumber `isi USGS`; lat `11.123`, lon `-86.482`
- baris data 51: `M 4.5 - Fiji region`; sumber `isi USGS`; lat `-20.927`, lon `-178.659`
- baris data 52: `M 5.1 - 129 km SSE of Kokopo, Papua New Guinea`; sumber `isi USGS`; lat `-5.457`, lon `152.616`
- baris data 53: `M 4.7 - 147 km SSW of Kokopo, Papua New Guinea`; sumber `isi USGS`; lat `-5.605`, lon `151.841`
- baris data 54: `M 5.2 - 71 km ESE of ‘Ohonua, Tonga`; sumber `isi USGS`; lat `-21.541`, lon `-174.296`
- baris data 55: `M 4.5 - 0 km NE of Río Grande, Panama`; sumber `isi USGS`; lat `7.724`, lon `-81.33`
- baris data 56: `M 4.7 - 20 km SW of Sandy Point Town, Saint Kitts and Nevis`; sumber `isi USGS`; lat `17.253`, lon `-63.007`
- baris data 57: `M 4.6 - Carlsberg Ridge`; sumber `isi USGS`; lat `1.452`, lon `66.987`
- baris data 58: `M 4.5 - Kermadec Islands, New Zealand`; sumber `isi USGS`; lat `-30.127`, lon `-177.384`
- baris data 59: `M 5.2 - 55 km NNW of Ruteng, Indonesia`; sumber `isi USGS`; lat `-8.145`, lon `120.273`

### 8.2 `alamat_detail` terisi tetapi provinsi kosong

- baris data 187: `Jabar Siapkan 18 Mobile Batching Plant untuk Bangun Jalan Desa Terpencil`; alamat `Jalan Desa Terpencil`
- baris data 202: `Logam Besar Misterius Ditemukan di Kebun Sawit Kotim Kalteng`; alamat `Jalan Sampit-Pangkalan Bun`
- baris data 214: `Pemotor di Bogor Tewas Terpental Usai Hantam Trotoar`; alamat `Jalan Raya Jakarta-Bogor mengakibatkan satu korban meninggal`
- baris data 242: `Truk Tabrak Separator Jalan Dievakuasi, Lalin Arah Cawang Normal`; alamat `Jalan Dievakuasi`
- baris data 249: `Lalin di Grogol arah Tomang Macet Imbas Mobil Tabrak Separator Busway`; alamat `Jalan S Parman`
- baris data 250: `Truk Tabrak Separator Jalan di MT Haryono, Lalin Arah Cawang Padat`; alamat `Jl. Letjen MT Haryono`
- baris data 376: `Daftar Jalan Ditutup Sementara Saat Kunjungan Sekjen PBB 17-19 Oktober`; alamat `Jalan Ditutup Sementara Saat Kunjungan Sekjen PBB 17-19`
- baris data 433: `Ada Tamu Negara Penting, Cek Daftar Jalan Ditutup Sementara 19 Oktober`; alamat `Jalan Ditutup Sementara 19`
- baris data 470: `Wapres Lolos dari 3 Dakwaan, tapi Pemakzulan Jalan Terus`; alamat `Jalan Terus`
- baris data 494: `DPRD Kota Bogor Fasilitasi Solusi Relokasi Pedagang Tanaman Hias Jalan Semeru`; alamat `Jalan Semeru`
- baris data 533: `Menko Muhaimin: Sekolah Rakyat Bukan Sekadar Pendidikan, tetapi Jalan Pemberdayaan`; alamat `Jalan Pemberdayaan`

### 8.3 Indikasi berita luar Indonesia

- baris data 50: `M 4.9 - 68 km WSW of San Juan del Sur, Nicaragua`; sumber `isi USGS`; lat `11.123`, lon `-86.482`
- baris data 51: `M 4.5 - Fiji region`; sumber `isi USGS`; lat `-20.927`, lon `-178.659`
- baris data 52: `M 5.1 - 129 km SSE of Kokopo, Papua New Guinea`; sumber `isi USGS`; lat `-5.457`, lon `152.616`
- baris data 53: `M 4.7 - 147 km SSW of Kokopo, Papua New Guinea`; sumber `isi USGS`; lat `-5.605`, lon `151.841`
- baris data 54: `M 5.2 - 71 km ESE of ‘Ohonua, Tonga`; sumber `isi USGS`; lat `-21.541`, lon `-174.296`
- baris data 55: `M 4.5 - 0 km NE of Río Grande, Panama`; sumber `isi USGS`; lat `7.724`, lon `-81.33`
- baris data 56: `M 4.7 - 20 km SW of Sandy Point Town, Saint Kitts and Nevis`; sumber `isi USGS`; lat `17.253`, lon `-63.007`
- baris data 57: `M 4.6 - Carlsberg Ridge`; sumber `isi USGS`; lat `1.452`, lon `66.987`
- baris data 58: `M 4.5 - Kermadec Islands, New Zealand`; sumber `isi USGS`; lat `-30.127`, lon `-177.384`

Catatan: 2 baris USGS lain tanpa provinsi berjudul wilayah Indonesia (`Banda Sea`, `Ruteng`) dan perlu review terpisah.

### 8.4 Kasus khusus CALANG-ACEHJAYA

- baris data 18: `Gempa M5.9 68 km BaratDaya CALANG-ACEHJAYA`
  - Kategori: `Gempa Bumi`; sumber: `BMKG`
  - Provinsi: `(kosong)`; kabupaten/kota: `(kosong)`
  - Koordinat: `4.56`, `94.97`; sumber: `URL BMKG`
  - URL: `https://www.bmkg.go.id/gempabumi/?t=2026-10-03T23%3A37%3A31%2B00%3A00&lat=4.56+LU&lon=94.97+BT&mag=5.9`
  - Judul/isi menulis `CALANG-ACEHJAYA` tanpa spasi; tidak ada nama administratif terpisah yang dapat dipastikan dari data. Perlu verifikasi manual.

### 8.5 Kategori Lainnya dengan indikasi hazard

- baris data 39: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 40: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 41: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 42: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 43: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 44: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 45: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 46: `Green forest fire notification in Indonesia`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 70: `Apa itu modifikasi cuaca? Ini cara kerja hujan buatan BMKG`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 345: `Palembang Kembali Diselimuti Kabut Asap Tebal Minggu Pagi`; kategori `Lainnya`; provinsi `Sumatera Selatan`
- baris data 379: `Video: Kabut Asap RI Menggila, ASEAN Umumkan Status Siaga Tertinggi`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 547: `Prakiraan Cuaca Jakarta 19 Oktober: Jaksel dan Jaktim Berpotensi Hujan`; kategori `Lainnya`; provinsi `(kosong)`
- baris data 576: `Kondisi Terkini Kabut Asap Palangka Raya Usai Diguyur Hujan`; kategori `Lainnya`; provinsi `Kalimantan Tengah`
- baris data 737: `Foto: Persiapan Operasi Modifikasi Cuaca di Palembang`; kategori `Lainnya`; provinsi `(kosong)`

### 8.6 Contoh provinsi terisi tanpa kabupaten/kota

- baris data 2: `Hujan Lebat disertai Petir di Kalimantan Selatan`; provinsi `Kalimantan Selatan`
- baris data 3: `Hujan Lebat disertai Petir di Kep. Riau`; provinsi `Kepulauan Riau`
- baris data 5: `Hujan Lebat disertai Petir di Sulawesi Tengah`; provinsi `Sulawesi Tengah`
- baris data 6: `Hujan Lebat disertai Petir di Sumatera Utara`; provinsi `Sumatera Utara`
- baris data 7: `Hujan Lebat disertai Petir di Kalimantan Timur`; provinsi `Kalimantan Timur`
- baris data 8: `Hujan Lebat disertai Petir di Aceh`; provinsi `Aceh`
- baris data 9: `Hujan Lebat disertai Petir di Riau`; provinsi `Riau`
- baris data 11: `Gempa M5.3 60 km TimurLaut LABUANBAJO-NTT`; provinsi `Nusa Tenggara Timur`
- baris data 12: `Gempa M5.7 29 km BaratLaut POHUWATO-GORONTALO`; provinsi `Gorontalo`
- baris data 14: `Gempa M5.1 125 km Tenggara BITUNG-SULUT`; provinsi `Sulawesi Utara`

### 8.7 Contoh duplikasi judul

- **8 baris** dengan judul `green forest fire notification in indonesia`
  - baris data 39; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032893`
  - baris data 40; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032887`
  - baris data 41; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032778`
  - baris data 42; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032747`
  - baris data 43; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032817`
  - baris data 44; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032802`
  - baris data 45; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032797`
  - baris data 46; sumber `GDACS`; URL `https://www.gdacs.org/report.aspx?eventtype=WF&eventid=1032798`
- **2 baris** dengan judul `pengacara kamaruddin simanjuntak meninggal dunia`
  - baris data 220; sumber `detikcom`; URL `https://news.detik.com/berita/d-8713429/pengacara-kamaruddin-simanjuntak-meninggal-dunia`
  - baris data 642; sumber `Media Indonesia`; URL `https://mediaindonesia.com/politik-dan-hukum/946008/pengacara-kamaruddin-simanjuntak-meninggal-dunia`

## 9. Rekomendasi perbaikan

1. **Verifikasi koordinat secara manual/independen** terhadap sumber resmi kejadian; jangan mengubah `tersedia_sumber` menjadi status terverifikasi tanpa bukti. Tambahkan kolom status verifikasi dan metode verifikasi pada tahap berikutnya.
2. **Pisahkan berita luar Indonesia** dari berita Indonesia berdasarkan metadata sumber, bukan hanya koordinat. Tinjau 9 baris USGS yang judulnya menyebut lokasi luar Indonesia.
3. **Perbaiki ekstraksi toponimi BMKG yang menempel** seperti `ACEHJAYA`, `KAB-SUKABUMI`, `POHUWATO`, dan `SUMBABARATDAYA`; tangani spasi, tanda hubung, dan singkatan tanpa mengarang nama.
4. **Perketat ekstraksi `alamat_detail`**: saat ini 11 baris hanya memiliki alamat yang tidak didukung provinsi, misalnya `Jalan Terus`, `Jalan Desa Terpencil`, dan `Jalan Dievakuasi`. Gunakan penanda alamat eksplisit dan blokir frasa yang bukan alamat.
5. **Review kategori**: 8 baris GDACS `Green forest fire notification in Indonesia` dan 3 baris bertema kabut asap masih `Lainnya`; perlu ditinjau terhadap aturan kategori. Jangan mengubah klasifikasi pada audit ini.
6. **Review duplikasi**: 8 baris GDACS memiliki judul sama tetapi URL/event ID berbeda; 2 baris `Pengacara Kamaruddin Simanjuntak Meninggal Dunia` berasal dari sumber berbeda. Jangan menghapus; gunakan `source_id`, URL, dan hash isi untuk penandaan duplikat.
7. **Tambahkan kolom jejak audit** (`source_id`, `duplicate_of`, `duplicate_reason`, status verifikasi koordinat) pada dataset yang dihasilkan ulang dari scraper baru; dataset 19 kolom ini berasal dari CSV lama yang belum memiliki kolom tersebut.
8. **Tetapkan quality gate** sebelum handoff: persentase `Lainnya` maksimum, kelengkapan provinsi/kabupaten minimum, jumlah koordinat terverifikasi minimum, dan batas duplikasi judul.

## 10. Kesimpulan kelayakan

Dataset **belum layak dinyatakan siap serah sebagai data tervalidasi**. Kelengkapan lokasi administratif rendah (87 baris provinsi, 34 baris kabupaten/kota), 689 baris tidak memiliki lokasi administratif sama sekali, 83,99% berlabel `Lainnya`, dan 40 koordinat baru berasal dari sumber tanpa verifikasi independen.

Dataset masih dapat digunakan sebagai **kandidat/eksplorasi** dengan disclaimer, tetapi memerlukan review manual dan perbaikan pipeline sebelum dipakai untuk analisis spasial, pemetaan, atau pelaporan resmi. Tidak ada CSV sumber atau kode produksi yang diubah dalam audit ini; laporan ini adalah artefak baru.

## Lampiran: file dan integritas

- Sumber: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261029T143308Z.csv`
- SHA-256: `5d1d3832e41fe6641ebedf4fe35c03a81aedf77d3bd3661e26ba91f6ffc7a6eb`
- Kolom: judul, published_time, event_time, sumber, kategori, provinsi, kabupaten_kota, kecamatan, desa_kelurahan, dusun_kampung, rw, rt, alamat_detail, url, isi_berita, latitude, longitude, koordinat_status, koordinat_sumber
- File laporan: `reports/validasi_kualitas_data_stage4.md`
- Tidak ada request internet, scraping, geocoding, atau perubahan data.
