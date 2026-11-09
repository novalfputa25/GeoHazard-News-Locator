# Audit Kualitas Dataset Final

Tanggal audit: **2026-11-02**  
File: `data/geohazard_news_final_20261101T150501Z.csv`  
Mode: read-only terhadap baseline; tidak ada perubahan data.

## 1. Identitas baseline

| Atribut | Nilai |
|---|---|
| SHA-256 | `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06` |
| Baris | 787 |
| Kolom | 51 |
| URL unik | 787 |
| Field wajib kosong | 0 (`judul`, `published_time`, `sumber`, `kategori`, `url`, `isi_berita`) |
| Primary path | `dataset_baseline.PRIMARY_DATASET_PATH` |

Verifikasi:

```powershell
& ".venv\Scripts\python.exe" -c "import dataset_baseline; print(dataset_baseline.verify_dataset())"
& ".venv\Scripts\python.exe" -m unittest -q test_dataset_baseline
```

Hasil terakhir: hash sesuai, 787 baris, 51 kolom, dan **3 tes lulus**. File ini adalah **baseline rilis**, bukan dataset operasional yang sudah tervalidasi.

## 2. Ringkasan eksekutif

- Integritas struktural baik: tidak ada field wajib kosong dan tidak ada URL duplikat.
- Kualitas isi lemah untuk analisis mendalam: 755 dari 787 baris memiliki `isi_berita` di bawah 300 karakter; median 149 karakter.
- Kategorisasi belum siap operasional: 734 baris (93,3%) berlabel `Lainnya`; 632 di antaranya benar-benar belum terklasifikasi, 102 berada di luar 8 kategori.
- Hanya 53 baris (6,7%) masuk 8 kategori target; Tsunami, Likuefaksi, Penurunan Muka Tanah, dan Semburan tidak memiliki baris.
- Hanya 64 baris memiliki `event_time`; 723 baris tidak memiliki waktu kejadian yang dapat dipakai.
- Hanya 40 baris memiliki koordinat; semuanya belum diverifikasi dan 9 berada di luar Indonesia.
- Provenance tidak lengkap: 16 label sumber, 7 feed aktif, tanpa `source_id`, `collected_at`, `run_id`, `source_type`, atau `data_type`.
- Dataset layak sebagai **baseline audit**, belum layak sebagai **dataset kejadian final/operasional**.

## 3. Integritas struktural

| Uji | Hasil | Status |
|---|---|---|
| Jumlah baris | 787 | Lulus |
| Jumlah kolom | 51 | Lulus |
| URL unik | 787/787 | Lulus |
| Field wajib kosong | 0 | Lulus |
| Hash baseline | Sesuai kontrak | Lulus |
| Unit test baseline | 3/3 lulus | Lulus |

Tidak ditemukan baris kosong total, URL kosong, atau pelanggaran kontrak baseline.

## 4. Kualitas isi

| Metrik `isi_berita` | Nilai |
|---|---:|
| Jumlah | 787 |
| Rata-rata | 163,6 karakter |
| Median | 149 karakter |
| Minimum | 40 karakter |
| Maksimum | 1.828 karakter |
| Di bawah 300 karakter | 755 (95,9%) |
| Kuartil 1 | 120 karakter |
| Kuartil 3 | 162 karakter |

Implikasi:

- Sebagian besar isi adalah ringkasan feed, bukan artikel penuh.
- Ekstraksi lokasi dan waktu dari isi memiliki bahan terbatas.
- Jangan menganggap `isi_berita` sebagai teks lengkap untuk analisis causa atau dampak.
- Untuk verifikasi kejadian, prioritaskan field sumber/structured feed dan buka URL secara manual bila perlu.

## 5. Kategorisasi

### 5.1 Distribusi kategori final

| Kategori | Baris | Persentase |
|---|---:|---:|
| Lainnya | 734 | 93,3% |
| Gempabumi | 44 | 5,6% |
| Gunungapi | 5 | 0,6% |
| Abrasi dan Akresi | 3 | 0,4% |
| Gerakan Tanah/Tanah Longsor | 1 | 0,1% |
| Tsunami | 0 | 0,0% |
| Likuefaksi | 0 | 0,0% |
| Penurunan Muka Tanah | 0 | 0,0% |
| Semburan Gas dan Lumpur | 0 | 0,0% |

### 5.2 Status cakupan

| Status | Baris | Arti |
|---|---:|---|
| `tidak_terklasifikasi` | 632 | Tidak masuk 8 kategori dan belum dapat dipetakan |
| `di_luar_8_kategori` | 102 | Di luar ruang lingkup: Karhutla 71, Cuaca Ekstrem 14, Lainnya 17 |
| `dalam_8_kategori` | 53 | Masuk salah satu dari 8 kategori target |

### 5.3 Asal dan aksi kategori

| `kategori_asal` | Baris |
|---|---:|
| Lainnya | 661 |
| Kebakaran Hutan dan Lahan | 71 |
| Gempa Bumi | 33 |
| Cuaca Ekstrem | 14 |
| Gunung Api | 4 |
| Abrasi dan Akresi | 3 |
| Gerakan Tanah / Longsor | 1 |

| `kategori_final_aksi` | Baris |
|---|---:|
| dipertahankan | 702 |
| dipetakan_ke_lainnya | 85 |

Penjelasan penting:

- `kategori_final` **734 Lainnya** terdiri dari **632 belum terklasifikasi + 102 di luar 8 kategori**.
- 85 baris dipetakan ke `Lainnya`: 71 Karhutla + 14 Cuaca Ekstrem; 17 baris luar kategori sudah berlabel `Lainnya` sejak awal.
- `kategori_asal` dan `kategori_sebelum_final` harus dipertahankan agar keputusan pemetaan dapat diaudit.
- Jangan menyimpulkan “mayoritas data adalah bencana geologi”; mayoritas justru belum terklasifikasi atau di luar cakupan.

## 6. Waktu

### 6.1 `published_time`

| Atribut | Nilai |
|---|---|
| Terisi | 787/787 |
| Format RFC 2822 | 727 |
| Format ISO 8601 | 40 |
| Format Indonesia | 20 |
| Rentang | 2026-04-30T13:07:47+00:00 sampai 2026-10-19T14:40:00+08:00 |

`published_time` adalah waktu publikasi, **bukan** waktu kejadian.

### 6.2 `event_time`

| Status | Baris |
|---|---:|
| `terekstrak` | 51 |
| `tanggal_saja` | 13 |
| `perlu_review` | 14 |
| `tidak_tersedia` | 709 |

| `event_time_jenis` | Baris |
|---|---:|
| `aktual` | 42 |
| `prediksi_nowcast` | 9 |
| `tanggal_saja` | 13 |
| `tidak_diketahui` | 723 |

Rincian:

- `event_time` terisi: **64 baris** (51 terekstrak + 13 tanggal saja).
- 42 aktual: BMKG 29, USGS 11, GDACS 1, Mongabay 1.
- 9 nowcast/prediksi: semuanya BMKG dan berada di `Lainnya`; jangan dianggap waktu aktual.
- 13 tanggal saja: 1 Gempabumi, 2 Gunungapi, 10 Lainnya.
- 723 tidak diketahui: 709 tanpa kandidat + 14 kandidat yang perlu review.
- 14 `perlu_review` sebagian besar berasal dari berita Karhutla/Cuaca dan satu kandidat Gunungapi (Sinabung); jangan mengisi otomatis.

### 6.3 Dampak

- 91,9% baris tidak memiliki waktu kejadian.
- Data tidak cocok untuk analisis frekuensi, time series, atau klaim “kejadian pada tanggal tertentu” tanpa verifikasi.
- Untuk 8 kategori target, waktu aktual hanya tersedia untuk 41 Gempabumi dan 1 Gerakan Tanah.

## 7. Lokasi dan koordinat

### 7.1 Kelengkapan administratif

| Field | Terisi | Persentase |
|---|---:|---:|
| `provinsi` | 88 | 11,2% |
| `kabupaten_kota` | 40 | 5,1% |
| `kecamatan` | 0 | 0,0% |
| `desa_kelurahan` | 0 | 0,0% |
| `dusun_kampung` | 0 | 0,0% |
| `rw` | 0 | 0,0% |
| `rt` | 0 | 0,0% |
| `alamat_detail` | 7 | 0,9% |

### 7.2 Hubungan dan presisi lokasi

| `lokasi_hubungan` | Baris |
|---|---:|
| `tidak_diketahui` | 679 |
| `rujukan_admin_belum_verifikasi` | 59 |
| `titik_kejadian_terindikasi` | 40 |
| `domain_disebut_dalam_judul` | 9 |

| `lokasi_presisi` | Baris |
|---|---:|
| `tidak_diketahui` | 679 |
| `provinsi` | 40 |
| `titik_terindikasi` | 40 |
| `kabupaten_kota` | 19 |
| `domain_negara` | 9 |

| `lokasi_verifikasi` | Baris |
|---|---:|
| `tidak_ada` | 699 |
| `belum_diverifikasi` | 81 |
| `perlu_verifikasi` | 7 |

### 7.3 Koordinat

| Atribut | Nilai |
|---|---|
| Baris dengan koordinat | 40 (5,1%) |
| Tanpa koordinat | 747 |
| Sumber | 29 URL BMKG; 11 isi USGS |
| Domain | 31 Indonesia; 9 luar Indonesia |
| Status verifikasi | 40 `belum_diverifikasi` |
| Latitude | -30,127 sampai 17,253 |
| Longitude | -178,659 sampai 152,616 |

Implikasi:

- Tidak semua koordinat berada di Indonesia; 9 baris USGS adalah gempa global.
- Koordinat belum divalidasi terhadap lokasi kejadian atau batas administrasi.
- Jangan menampilkan koordinat sebagai “lokasi pasti” tanpa verifikasi.
- 679 baris tidak memiliki hubungan lokasi yang dapat dipakai.

## 8. Duplikasi

| Jenis | Baris | Kelompok | Catatan |
|---|---:|---:|---|
| Judul | 10 | 2 kelompok utama | 8 GDACS berjudul sama; 2 berita detikcom/Media Indonesia berjudul sama |
| Isi | 4 | 2 kelompok | Semua GDACS; dua pasang isi identik |
| URL | 0 | 0 | Tidak ada URL duplikat |

Keputusan:

- Semua baris dipertahankan; deduplikasi tidak dilakukan pada baseline.
- Untuk dataset baru, deduplikasi harus memakai `event_id`/sumber/waktu, bukan hanya judul atau isi.
- Jangan menghapus duplikat hanya untuk menaikkan persentase kategori.

## 9. Provenance

Dataset memiliki 16 label sumber, sedangkan `feeds.py` hanya mengaktifkan 7 feed:

| Sumber | Baris |
|---|---:|
| detikcom | 100 |
| CNN Indonesia | 100 |
| CNBC Indonesia | 100 |
| Media Indonesia | 100 |
| ANTARA | 97 |
| Tempo | 50 |
| Liputan6 | 50 |
| BMKG | 38 |
| SINDOnews | 30 |
| kumparan | 25 |
| BBC Indonesia | 21 |
| ANTARA Jatim | 20 |
| Mongabay | 20 |
| Republika | 15 |
| USGS | 11 |
| GDACS | 10 |

Keterbatasan:

- Tidak ada `source_id`, `source_type`, `data_type`, `collected_at`, `run_id`, `event_id`, `raw_payload`, atau `license`.
- Label `sumber` tidak membedakan feed resmi, berita, portal, dan agregator.
- Tidak dapat diketahui kapan baris diambil, dari feed mana, atau apakah ada perubahan setelah publikasi.
- 13 feed RSS historis di register tidak aktif; jangan menganggap seluruh 16 label sebagai sumber yang masih dipantau.

## 10. Kandidat underclassification dan review manual

Kandidat jelas:

- **“Status Gunung Sinabung Turun dari Level Siaga Jadi Waspada”** (CNN Indonesia) masih `Lainnya`; secara topik termasuk Gunungapi. Perlu review manual, bukan reklasifikasi otomatis.
- **“Ada daratan baru di dekat Anak Krakatau, ini penjelasan ahli”** (ANTARA) masih `Lainnya`; apakah ini kejadian gunung api atau fenomena geologi lain perlu verifikasi.
- Tidak ada penambahan otomatis untuk kedua baris di baseline.

Temuan tsunami:

- 15 baris Gempabumi menyebut “tsunami”, semuanya berkategori Gempabumi.
- Tidak ada kejadian tsunami terpisah yang dapat dihitung dari data ini.
- Field “Potensi” BMKG tidak sama dengan kejadian tsunami.

Temuan duplikasi GDACS:

- 8 baris “Green forest fire notification in Indonesia” adalah duplikat judul Karhutla; bukan kejadian geologi target.
- Jangan memakai duplikasi ini untuk menambah hitungan kategori.

## 11. Kesiapan kualitas

| Dimensi | Status | Alasan |
|---|---|---|
| Integritas file | Baik | Hash, jumlah baris/kolom, URL unik, field wajib |
| Kelengkapan teks | Lemah | 95,9% isi <300 karakter |
| Kategorisasi | Belum siap | 93,3% `Lainnya`; 80,3% belum terklasifikasi |
| Cakupan kategori | Sangat lemah | 4 dari 8 kategori kosong; 6,7% baris target |
| Waktu kejadian | Lemah | 91,9% tidak diketahui |
| Lokasi | Lemah | 5,1% koordinat; semua belum diverifikasi |
| Provenance | Belum memadai | Tidak ada source/run/raw payload |
| Duplikasi | Terkendali | 10 judul, 4 isi, 0 URL; dipertahankan |
| Kesiapan operasional | Belum | Perlu sumber resmi, izin, dan validasi |

## 12. Rekomendasi

1. Pertahankan baseline apa adanya; jangan menimpa atau “membersihkan” dengan penghapusan massal.
2. Tambahkan field provenance sebelum membuat dataset baru.
3. Pisahkan `Lainnya` yang belum terklasifikasi dari `Lainnya` yang memang di luar cakupan.
4. Review manual kandidat Sinabung dan baris berita yang memiliki tanggal kejadian eksplisit.
5. Jangan memakai `published_time` sebagai `event_time`.
6. Validasi 40 koordinat dan tandai 9 koordinat luar Indonesia.
7. Perbaiki cakupan melalui sumber resmi/izin, bukan dengan menambah berita umum.
8. Gunakan quality gate di `reports/RENCANA_FINALISASI_DATASET.md` sebelum rilis baru.

## 13. Kesimpulan

Dataset final memiliki integritas struktural yang baik dan dapat dijadikan baseline audit. Namun, kualitas kategori, waktu, lokasi, dan provenance belum memenuhi syarat untuk dataset kejadian operasional. Status yang tepat adalah:

> **Baseline audit yang stabil, belum menjadi dataset bencana geologi yang lengkap dan tervalidasi.**
