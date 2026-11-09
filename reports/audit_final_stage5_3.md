# Audit Final Stage 5.3

- Tanggal audit: 2026-11-01
- Dataset: `data/geohazard_news_located_20261101T140913Z_stage5_2.csv`
- SHA-256 dataset: `a954df014dd7f6e03051381fb75b9c451bd3e740ba20378d96c05489be860343`
- Pembanding: `data/geohazard_news_located_20261030T125936Z_stage5.csv`
- SHA-256 pembanding: `4a0c3377bddc1672e32e2e1dd6ed313e3a9c2702f64c3d0cbc8f313c9d189f0f`
- Mode: **read-only**. Tidak ada perubahan pada CSV, dataset historis, atau kode produksi.
- Metode: pembacaan CSV, pemeriksaan schema dan nilai kosong, parsing tiga format tanggal, exact match gazetteer, cross-tab kategori/lokasi, dan pemeriksaan duplikasi. Tidak ada scraping atau geocoding.

## Status audit

**Lulus untuk integritas struktur. Layak bersyarat sebagai baseline pengembangan. Belum siap untuk analitik temporal atau klaim lokasi administratif presisi.**

Alasannya: struktur 787 x 36 konsisten dan tidak ada perubahan tak disengaja, tetapi `event_time` kosong 100%, seluruh lokasi administratif belum terverifikasi independen, dan ada 85 baris dengan kategori di luar daftar 9 label target.

## 1. Ringkasan eksekutif

- Jumlah baris tetap **787**; jumlah kolom **36**.
- URL kosong **0**, URL duplikat **0**, judul kosong **0**, isi berita kosong **0**.
- Tidak ada nilai `None` akibat baris CSV rusak.
- Perubahan dari Stage 5 hanya pada `domain_lokasi` (**93 baris**) dan penambahan **6 kolom** Stage 5.2; kolom lama lain tidak berubah.
- `event_time` kosong pada **787/787 baris**.
- `domain_lokasi=tidak_diketahui` pada **679 baris**; `provinsi` kosong pada **699 baris**; `kabupaten_kota` kosong pada **747 baris**.
- Seluruh **88 baris** yang memiliki lokasi administratif masih berstatus belum terverifikasi: **81** `belum_diverifikasi` dan **7** `perlu_verifikasi`.
- Kategori di luar daftar 9 label: **85 baris** (`Cuaca Ekstrem` 14, `Kebakaran Hutan dan Lahan` 71). Kategori `Lainnya` mencakup **649 baris**, terdiri dari 632 belum terklasifikasi dan 17 di luar cakupan.
- Empat kategori target tidak memiliki baris: Tsunami, Likuefaksi, Penurunan Muka Tanah, Semburan Gas dan Lumpur.
- Duplikasi judul: **10 baris dalam 2 kelompok**; duplikasi isi berita eksak: **4 baris dalam 2 kelompok**; duplikasi URL: **0**.
- Format `published_time` campuran: 727 RFC 2822, 40 ISO 8601, dan 20 format Indonesia (`DD Mon YYYY`); semuanya dapat diparse setelah normalisasi.
- Tidak ada tanggal publikasi di masa depan; rentang publikasi 2026-04-30 sampai 2026-10-19.

## 2. Integritas struktur dan perubahan data

| Pemeriksaan | Hasil | Status |
|---|---:|---|
| Baris | 787 | Lulus |
| Kolom | 36 | Lulus |
| Baris dengan jumlah field tidak konsisten | 0 | Lulus |
| Nilai `None` | 0 | Lulus |
| URL kosong | 0 | Lulus |
| URL unik | 787 | Lulus |
| Judul kosong | 0 | Lulus |
| Isi berita kosong | 0 | Lulus |
| `sumber` kosong | 0 | Lulus |
| `kategori` kosong | 0 | Lulus |
| `published_time` kosong | 0 | Lulus |
| `event_time` kosong | 787 | Perlu perhatian |
| Hash sumber Stage 5 tetap | Ya | Lulus |
| Perubahan kolom lama selain `domain_lokasi` | 0 | Lulus |

Perbandingan Stage 5 -> Stage 5.2:

| Perubahan | Jumlah | Evaluasi |
|---|---:|---|
| Kolom baru Stage 5.2 | 6 | Sesuai rancangan |
| Kolom lama dihapus | 0 | Lulus |
| `domain_lokasi` berubah | 93 | Sesuai laporan Stage 5.2 |
| Kolom lama lain berubah | 0 | Lulus |
| Urutan URL berubah | 0 | Lulus |
| Judul berubah | 0 | Lulus |
| Isi berita berubah | 0 | Lulus |

Kesimpulan integritas: tidak ditemukan perubahan data yang tidak disengaja. Perubahan yang ada sesuai dengan fungsi Stage 5.2, yaitu koreksi domain dan penambahan metadata audit.

## 3. Inventaris 36 kolom

| No | Kolom | Kosong | Catatan |
|---:|---|---:|---|
| 1 | `judul` | 0 | Wajib; unik 779 |
| 2 | `published_time` | 0 | Tiga format tanggal |
| 3 | `event_time` | 787 | Tidak tersedia terstruktur |
| 4 | `sumber` | 0 | 16 sumber |
| 5 | `kategori` | 0 | 7 nilai unik |
| 6 | `provinsi` | 699 | 29 provinsi valid |
| 7 | `kabupaten_kota` | 747 | 26 nama valid |
| 8 | `kecamatan` | 787 | Kosong seluruhnya |
| 9 | `desa_kelurahan` | 786 | Satu nilai mencurigakan |
| 10 | `dusun_kampung` | 787 | Kosong seluruhnya |
| 11 | `rw` | 787 | Kosong seluruhnya |
| 12 | `rt` | 787 | Kosong seluruhnya |
| 13 | `alamat_detail` | 780 | 7 terisi |
| 14 | `url` | 0 | 787 unik |
| 15 | `isi_berita` | 0 | Unik 785 |
| 16 | `latitude` | 747 | 40 koordinat |
| 17 | `longitude` | 747 | 40 koordinat |
| 18 | `koordinat_status` | 0 | 40 tersedia, 747 tidak ada |
| 19 | `koordinat_sumber` | 747 | 29 BMKG, 11 USGS |
| 20 | `koordinat_verifikasi` | 0 | Tidak ada yang terverifikasi |
| 21 | `koordinat_domain` | 0 | 31 Indonesia, 9 luar, 747 tidak diketahui |
| 22 | `kategori_asal` | 0 | 7 nilai unik |
| 23 | `kategori_berubah` | 0 | 50 `ya`, 737 `tidak` |
| 24 | `kategori_alasan` | 0 | 10 nilai unik |
| 25 | `status_cakupan` | 0 | 53 dalam, 102 luar, 632 belum |
| 26 | `domain_lokasi` | 0 | 99 Indonesia, 9 luar, 679 tidak diketahui |
| 27 | `duplikat_judul` | 0 | 10 `ya` |
| 28 | `duplikat_url` | 0 | 0 `ya` |
| 29 | `duplikat_dengan` | 777 | 10 terisi |
| 30 | `catatan_stage5` | 721 | 66 terisi |
| 31 | `domain_lokasi_sebelum` | 0 | Jejak audit |
| 32 | `domain_lokasi_basis` | 0 | 59 provinsi, 40 koordinat, 9 judul, 679 tidak diketahui |
| 33 | `lokasi_verifikasi` | 0 | 81 belum, 7 perlu, 699 tidak ada |
| 34 | `lokasi_basis` | 0 | 81 warisan, 7 rujukan toponimi, 699 tidak ada |
| 35 | `lokasi_risiko` | 0 | 4 tinggi, 3 sedang, 780 tidak dinilai |
| 36 | `catatan_stage5_2` | 686 | 101 terisi |

Catatan: kolom alamat, koordinat, dan `event_time` yang kosong bukan otomatis kesalahan struktur. Namun kolom tersebut membatasi kedalaman analisis.

## 4. Audit kategori

Distribusi kategori:

| Kategori | Jumlah | Di target 9 label? |
|---|---:|---|
| Gempabumi | 44 | Ya |
| Lainnya | 649 | Ya, tetapi tidak spesifik |
| Kebakaran Hutan dan Lahan | 71 | Tidak |
| Cuaca Ekstrem | 14 | Tidak |
| Gunungapi | 5 | Ya |
| Abrasi dan Akresi | 3 | Ya |
| Gerakan Tanah/Tanah Longsor | 1 | Ya |
| Tsunami | 0 | Ya, tetapi tidak ada baris |
| Likuefaksi | 0 | Ya, tetapi tidak ada baris |
| Penurunan Muka Tanah | 0 | Ya, tetapi tidak ada baris |
| Semburan Gas dan Lumpur | 0 | Ya, tetapi tidak ada baris |

Temuan kategori:

- **85 baris (10,8%)** memakai kategori di luar daftar 9 label: `Cuaca Ekstrem` 14 dan `Kebakaran Hutan dan Lahan` 71.
- **632 baris (80,3%)** berstatus `tidak_terklasifikasi`; **17 baris** berstatus `di_luar_8_kategori`, sehingga total `Lainnya` adalah 649.
- `status_cakupan`: 53 `dalam_8_kategori`, 102 `di_luar_8_kategori`, 632 `tidak_terklasifikasi`.
- `kategori_berubah=ya` pada 50 baris: 38 perubahan normalisasi label (misalnya `Gempa Bumi` -> `Gempabumi`) dan 12 perubahan substantif dari `Lainnya` (11 ke `Gempabumi`, 1 ke `Gunungapi`).
- Tidak ditemukan label kategori yang rusak, kosong, atau di luar nilai yang diketahui. Yang ada adalah kategori di luar kontrak 9 label.
- Ketiadaan Tsunami, Likuefaksi, Penurunan Muka Tanah, dan Semburan Gas dan Lumpur tidak otomatis berarti kesalahan; bisa berarti tidak ada berita yang memenuhi bukti. Namun keempat kategori itu belum teruji oleh data.

Jangan mengubah kategori secara otomatis. Perlu keputusan kontrak: pertahankan dua kategori tambahan, atau map ke `Lainnya` dengan jejak `kategori_asal`.

## 5. Audit lokasi

### 5.1 Konsistensi domain dan administratif

| Domain | Jumlah | Punya provinsi | Tanpa provinsi | Punya kab/kota |
|---|---:|---:|---:|---:|
| `indonesia` | 99 | 88 | 11 | 40 |
| `luar_indonesia` | 9 | 0 | 9 | 0 |
| `tidak_diketahui` | 679 | 0 | 679 | 0 |

- **0** baris memiliki `kabupaten_kota` tanpa `provinsi`.
- **0** baris `domain_lokasi=tidak_diketahui` yang masih memiliki provinsi.
- **0** baris `domain_lokasi=luar_indonesia` yang memiliki provinsi.
- 11 baris `domain_lokasi=indonesia` tanpa provinsi: 9 berbasis judul `in Indonesia` dan 2 berbasis koordinat.
- 48 baris hanya memiliki provinsi tanpa kabupaten/kota; ini merupakan lokasi presisi provinsi, bukan lokasi kabupaten.
- Seluruh 29 nama provinsi dan 26 nama kabupaten/kota yang terisi cocok persis dengan gazetteer. Ini menunjukkan konsistensi penamaan, bukan bukti bahwa lokasi kejadian benar.

Distribusi `lokasi_verifikasi`:

| Status | Jumlah | Basis |
|---|---:|---|
| `belum_diverifikasi` | 81 | `warisan_stage3` |
| `perlu_verifikasi` | 7 | `rujukan_toponimi` |
| `tidak_ada` | 699 | Lokasi tidak tersedia |

**Seluruh 88 baris yang memiliki lokasi administratif belum terverifikasi independen.** Tidak ada baris dengan status `terverifikasi`.

### 5.2 Tujuh baris fokus

| Baris | Provinsi/Kabupaten | Risiko | Catatan | Evaluasi |
|---:|---|---|---|---|
| 12 | Gorontalo/Kabupaten Pohuwato | sedang | `lokasi_rujukan;jarak_29_km;batas_admin_perlu_verifikasi` | Nama valid; batas pusat gempa belum terbukti |
| 14 | Sulawesi Utara/Kota Bitung | tinggi | `lokasi_rujukan;jarak_125_km;batas_admin_perlu_verifikasi` | Jarak jauh; risiko tinggi wajar, tetapi batas belum terbukti |
| 17 | Kalimantan Utara/Kota Tarakan | tinggi | `lokasi_rujukan;jarak_219_km;batas_admin_perlu_verifikasi` | Jarak sangat jauh; jangan dipakai sebagai titik administrasi |
| 18 | Aceh/Kabupaten Aceh Jaya | tinggi | `lokasi_rujukan;jarak_68_km;batas_admin_perlu_verifikasi` | Nama valid; pusat gempa belum terbukti di dalam kabupaten |
| 19 | Nusa Tenggara Timur/Kabupaten Sumba Barat Daya | sedang | `lokasi_rujukan;jarak_14_km;batas_admin_perlu_verifikasi` | Jarak dekat; tetap perlu verifikasi batas |
| 24 | Papua/Kabupaten Sarmi | sedang | `lokasi_rujukan;jarak_33_km;batas_admin_perlu_verifikasi` | Nama valid; batas belum terbukti |
| 27 | Nusa Tenggara Timur/Kabupaten Sumba Barat Daya | tinggi | `lokasi_rujukan;epicenter_di_laut;batas_admin_perlu_verifikasi` | Pusat gempa dinyatakan di laut 49 km barat Kodi; jangan anggap kabupaten sebagai epicenter |

Konsistensi risiko:

- `lokasi_risiko=tinggi` hanya pada 4 baris: 14, 17, 18, 27.
- `lokasi_risiko=sedang` hanya pada 3 baris: 12, 19, 24.
- Semua 7 baris `perlu_verifikasi` memiliki catatan `lokasi_rujukan` dan `batas_admin_perlu_verifikasi`.
- Tidak ada baris berisiko tinggi/sedang yang kehilangan catatan.
- Arti ambang risiko belum didokumentasikan sebagai aturan formal. Label risiko konsisten dengan catatan, tetapi belum dapat diaudit ulang tanpa definisi ambang.

### 5.3 Koordinat

| Pemeriksaan | Hasil |
|---|---:|
| Baris dengan latitude/longitude | 40 |
| Koordinat berstatus tersedia | 40 |
| Koordinat terverifikasi | 0 |
| Koordinat belum diverifikasi | 40 |
| Sumber BMKG | 29 |
| Sumber USGS | 11 |
| Domain koordinat Indonesia | 31 |
| Domain koordinat luar Indonesia | 9 |
| Di luar bounding box kasar Indonesia | 9 |
| Di dalam bounding box kasar Indonesia | 31 |

Sembilan koordinat di luar rentang Indonesia adalah baris 50-58 dan semuanya `domain_lokasi=luar_indonesia`. Tiga puluh satu koordinat lain berada di dalam bounding box kasar, tetapi **tidak satu pun diverifikasi independen**. Bounding box bukan batas hukum dan bukan bukti lokasi kejadian.

### 5.4 Anomali field lokasi

- Baris 216 memiliki `desa_kelurahan=Banjir`. Nilai ini tampak berasal dari kata umum di judul, bukan nama desa/kelurahan; perlu dibersihkan pada proses berikutnya.
- Ada 7 `alamat_detail`; 5 di antaranya tidak memiliki provinsi: baris 202, 214, 249, 250, dan 494.
- `kecamatan`, `dusun_kampung`, `rw`, dan `rt` kosong seluruhnya; `desa_kelurahan` kosong pada 786 baris. Dataset ini tidak memiliki lokasi sub-kabupaten yang lengkap.

## 6. Audit waktu

### 6.1 `published_time`

| Pemeriksaan | Hasil |
|---|---:|
| Kosong | 0 |
| RFC 2822 | 727 |
| ISO 8601 | 40 |
| Format Indonesia `DD Mon YYYY` | 20 |
| Tidak dapat diparse setelah normalisasi | 0 |
| Publikasi di masa depan | 0 |
| Rentang minimum | 2026-04-30T13:07:47+00:00 |
| Rentang maksimum | 2026-10-19T07:07:24+00:00 |
| Zona waktu WIB (+0700) | 668 |
| Zona waktu WITA (+0800) | 3 |
| Zona waktu UTC (+0000) | 116 |

Format Indonesia berasal dari 20 baris Mongabay, misalnya baris 768: `19 Okt 2026 02:17:05 +0000`. Format ini valid secara semantik, tetapi tidak kompatibel dengan parser tanggal standar. Untuk aplikasi, normalisasi ke ISO 8601 UTC diperlukan.

Duplikasi timestamp publikasi: 19 kelompok, melibatkan 40 baris, dengan 21 baris berlebih. Semua kelompok memiliki judul berbeda; ini bukan bukti duplikasi berita, melainkan kemungkinan publikasi bersamaan.

### 6.2 `event_time`

- Kosong pada **787/787 baris (100%)**.
- Tidak ada nilai tidak valid karena tidak ada nilai sama sekali.
- Waktu kejadian tidak boleh diisi dari `published_time` tanpa bukti eksplisit dari sumber.
- Beberapa `isi_berita` BMKG memuat waktu kejadian di narasi, tetapi belum diekstrak menjadi field terstruktur. Ini adalah keterbatasan, bukan izin untuk menebak.

## 7. Audit duplikasi

| Pemeriksaan | Hasil |
|---|---:|
| URL kosong | 0 |
| URL duplikat | 0 |
| Judul kosong | 0 |
| Judul duplikat | 10 baris |
| Kelompok judul duplikat | 2 |
| Isi berita kosong | 0 |
| Isi berita duplikat eksak | 4 baris |
| Kelompok isi duplikat eksak | 2 |

Kelompok duplikat:

| Kelompok | Baris | Evaluasi |
|---|---|---|
| Judul `Green forest fire notification in Indonesia` | 39-46 (8 baris) | Bukan baris identik; URL/event ID GDACS berbeda. Jangan hapus berdasarkan judul. |
| Judul `Pengacara Kamaruddin Simanjuntak Meninggal Dunia` | 220 dan 642 | URL dan sumber berbeda; waktu berbeda 49 detik. Kemungkinan berita berbeda tentang kejadian yang sama, bukan duplikat baris. |
| Isi berita eksak | 42 dan 43 | URL/event ID berbeda (`1032747` vs `1032817`); konten GDACS generik sama. |
| Isi berita eksak | 44 dan 45 | URL/event ID berbeda (`1032802` vs `1032797`); konten GDACS generik sama. |

Tidak ada duplikat URL dan tidak ada baris yang identik pada seluruh field. Penghapusan tidak dapat dibenarkan hanya dari judul atau isi generik. Untuk deduplikasi aplikasi, gunakan URL, ID event sumber, waktu, dan sumber secara bersama.

## 8. Tabel temuan

| ID | Tingkat | Temuan | Jumlah | Bukti/contoh | Dampak |
|---|---|---|---:|---|---|
| F-01 | Tinggi | `event_time` tidak tersedia | 787 baris (100%) | Semua baris, termasuk 27 | Tidak ada analitik waktu kejadian |
| F-02 | Tinggi | Lokasi administratif belum terverifikasi | 88 baris | 81 `belum_diverifikasi`, 7 `perlu_verifikasi` | Tidak boleh dipakai untuk klaim batas admin |
| F-03 | Tinggi | Cakupan kategori belum sesuai kontrak | 649 `Lainnya`; 85 di luar 9 label | `Lainnya` 632 belum terklasifikasi; Cuaca 14, Karhutla 71 | Filter kategori tidak lengkap |
| F-04 | Tinggi | Domain/lokasi tidak diketahui | 679 domain; 699 provinsi kosong | Baris 401, 629, 737 | Banyak berita tidak dapat dipetakan |
| F-05 | Sedang | Format tanggal campuran | 60 baris non-RFC | 40 ISO, 20 format Indonesia; baris 10, 768 | Parser aplikasi harus normalisasi |
| F-06 | Sedang | Koordinat belum diverifikasi | 40 baris | 31 Indonesia, 9 luar; semua `belum_diverifikasi` | Titik tidak boleh dianggap valid |
| F-07 | Rendah | Duplikasi judul/isi | 10 judul; 4 isi | Baris 39-46, 220/642, 42/43, 44/45 | Risiko double-count jika dedup naif |
| F-08 | Rendah | Anomali alamat/desa | 1 desa; 5 alamat tanpa provinsi | Baris 216; 202, 214, 249, 250, 494 | Presisi lokasi rendah |
| P-01 | Lulus | Struktur dan integritas dasar | 787 x 36 | URL unik 787, tidak ada blank kritis | Baseline struktur aman |
| P-02 | Lulus | Tidak ada perubahan tak disengaja | 0 kolom lama selain domain | Hanya `domain_lokasi` 93 + 6 kolom baru | Jejak Stage 5.2 konsisten |
| P-03 | Lulus | Nama wilayah cocok gazetteer | 29 provinsi, 26 kab/kota | Semua exact match | Penamaan konsisten |

## 9. Jumlah data bermasalah

Angka di bawah adalah jumlah baris per isu dan **tidak saling eksklusif**; satu baris dapat muncul di beberapa isu.

| Isu | Baris | Persentase |
|---|---:|---:|
| `event_time` kosong | 787 | 100,0% |
| `provinsi` kosong | 699 | 88,8% |
| `kabupaten_kota` kosong | 747 | 94,9% |
| `domain_lokasi=tidak_diketahui` | 679 | 86,3% |
| Kategori `Lainnya` | 649 | 82,5% |
| Kategori di luar 9 label | 85 | 10,8% |
| Lokasi administratif belum terverifikasi | 88 | 11,2% |
| Lokasi `perlu_verifikasi` | 7 | 0,9% |
| Koordinat belum diverifikasi | 40 | 5,1% |
| Tanggal non-RFC 2822 | 60 | 7,6% |
| Judul duplikat | 10 | 1,3% |
| Isi berita duplikat eksak | 4 | 0,5% |
| URL duplikat | 0 | 0,0% |

## 10. Contoh baris yang perlu diperiksa

| Baris | Temuan | Alasan |
|---:|---|---|
| 27 | Episentrum di laut | `epicenter_di_laut`; kabupaten hanya rujukan, bukan titik pusat gempa |
| 14 | Jarak 125 km | Lokasi berisiko tinggi; batas administrasi belum terbukti |
| 17 | Jarak 219 km | Jarak sangat jauh; jangan dipakai sebagai koordinat kabupaten |
| 18 | Jarak 68 km | Nama wilayah valid, tetapi pusat gempa belum terbukti di dalam kabupaten |
| 42/43 | Isi berita identik | Event ID GDACS berbeda; jangan hapus tanpa pemeriksaan sumber |
| 220/642 | Judul sama | Sumber/URL berbeda; kemungkinan sindikasi berita, bukan duplikat baris |
| 216 | `desa_kelurahan=Banjir` | Kata umum di judul, bukan nama desa |
| 10 | Tanggal ISO 8601 | Perlu normalisasi tanggal |
| 768 | Tanggal format Indonesia | `19 Okt 2026...`; parser standar gagal |
| 1 | Kategori di luar kontrak | `Cuaca Ekstrem` |
| 89 | Kategori di luar kontrak | `Kebakaran Hutan dan Lahan` |
| 401 | Domain tidak diketahui | Frasa `di Indonesia` bukan bukti lokasi kejadian |
| 629 | Domain tidak diketahui | Berita WNI di Sri Lanka; bukan kejadian di Indonesia |
| 737 | Domain tidak diketahui | Palembang disebut, tetapi provinsi/kabupaten tidak terisi |

## 11. Kategori dan lokasi yang belum dapat dipastikan

Kategori:

- `Lainnya` 649 baris: 632 tanpa bukti kategori target, 17 di luar cakupan.
- Empat kategori target belum memiliki baris: Tsunami, Likuefaksi, Penurunan Muka Tanah, Semburan Gas dan Lumpur.
- 85 baris memakai label di luar kontrak 9 label (`Cuaca Ekstrem` 14 dan `Kebakaran Hutan dan Lahan` 71). Label tersebut tidak boleh diubah otomatis tanpa keputusan produk.

Lokasi:

- 679 baris `domain_lokasi=tidak_diketahui`.
- 699 baris tanpa provinsi dan 747 baris tanpa kabupaten/kota.
- 11 baris Indonesia tanpa provinsi: 9 berbasis judul dan 2 berbasis koordinat.
- 48 baris hanya sampai presisi provinsi.
- 7 baris fokus telah ditandai, tetapi batas administrasi pusat gempa belum terbukti.
- 81 baris lokasi warisan Stage 3 belum diverifikasi.
- 40 koordinat belum diverifikasi; 9 di antaranya berada di luar Indonesia.
- Tidak ada bukti independen bahwa kabupaten/kota pada 7 baris fokus merupakan lokasi pusat gempa.

## 12. Rekomendasi sebelum integrasi

Prioritas P0:

1. Jangan menampilkan atau mengklaim dataset ini sebagai data tervalidasi. Gunakan istilah "terklasifikasi", "terindikasi", atau "belum diverifikasi".
2. Tetapkan kontrak kategori: 9 label target saja, atau tambah `Cuaca Ekstrem` dan `Kebakaran Hutan dan Lahan` secara eksplisit. Jangan map otomatis tanpa jejak.
3. Jangan menggunakan `provinsi`/`kabupaten_kota` sebagai epicenter atau batas kejadian. Untuk 7 baris fokus, gunakan status `perlu_verifikasi` dan tampilkan catatan.
4. Jangan mengisi `event_time` dari `published_time`. Tambahkan field bukti waktu kejadian dan biarkan null jika tidak ada bukti eksplisit.

Prioritas P1:

5. Normalisasi `published_time` ke ISO 8601 UTC; simpan nilai asli di field mentah dan tangani format Indonesia.
6. Tambahkan validasi schema dan test integritas: 787 baris baseline, 36 kolom, URL unik, judul/isi tidak kosong, kategori dalam kontrak, tanggal parseable, koordinat dalam rentang, dan konsistensi domain.
7. Verifikasi 7 baris fokus dan 81 lokasi warisan Stage 3 terhadap sumber resmi; simpan bukti verifikasi dan jangan mengandalkan nama gazetteer saja.
8. Pisahkan presisi lokasi menjadi `point`, `kabupaten`, `provinsi`, dan `tidak_diketahui`; jangan mencampur domain kejadian dengan validitas administratif.

Prioritas P2:

9. Deduplikasi berbasis URL + ID event + waktu + sumber, bukan judul. Pertahankan baris 39-46 sebagai event GDACS berbeda dan baris 220/642 sebagai sindikasi yang perlu ditinjau.
10. Perbaiki ekstraksi `desa_kelurahan` agar kata umum seperti "Banjir" tidak masuk; validasi alamat terhadap konteks provinsi/kabupaten.
11. Dokumentasikan ambang `lokasi_risiko` dan alasan `tinggi`/`sedang` agar audit berikutnya dapat menguji konsistensi secara formal.
12. Tambahkan indikator kualitas per baris untuk kategori, lokasi, waktu, dan koordinat sebelum data dipakai di aplikasi.

## 13. Batas audit

- Audit ini read-only; tidak ada CSV, dataset historis, atau kode produksi yang diubah.
- Tidak ada geocoding, scraping, atau pencarian sumber online.
- Validasi koordinat hanya menggunakan bounding box kasar dan konsistensi internal; tidak ada verifikasi independen.
- Exact match gazetteer membuktikan nama wilayah valid, bukan membuktikan lokasi kejadian.
- Duplikasi diperiksa dari URL, judul, dan isi eksak; kemiripan semantik berita tidak dinilai.
- Kategori diperiksa dari nilai dan metadata yang ada; bukti teks lengkap tidak diverifikasi ulang di audit ini.
- Status "layak bersyarat" berarti dataset dapat dipakai sebagai baseline pengembangan dan eksplorasi, bukan untuk keputusan operasional atau klaim geospasial presisi.

## 14. Kesimpulan

Dataset Stage 5.2 konsisten secara struktur: 787 baris, 36 kolom, tidak ada URL duplikat, tidak ada blank pada field kritis, dan tidak ada perubahan tak disengaja dari Stage 5. Namun dataset belum siap untuk integrasi analitik penuh karena `event_time` kosong 100%, seluruh lokasi administratif belum terverifikasi, cakupan kategori belum memenuhi kontrak 9 label, dan banyak lokasi masih `tidak_diketahui`.

Keputusan yang disarankan: **gunakan untuk pengembangan awal dan monitoring eksploratif; tahan fitur analitik waktu, pemetaan presisi, dan klaim validasi sampai P0/P1 diselesaikan.**
