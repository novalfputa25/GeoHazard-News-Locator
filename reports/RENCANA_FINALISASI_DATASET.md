# Rencana Finalisasi Dataset

Tanggal: **2026-11-02**  
Status: rencana; belum ada perubahan pada dataset, kode, atau konfigurasi sumber.  
Acuan: `reports/FINAL_AUDIT_SUMBER_DATA.md`, `reports/MATRIKS_CAKUPAN_8_KATEGORI.md`, `reports/AUDIT_KUALITAS_DATASET_FINAL.md`.

## 1. Tujuan

Menghasilkan dataset kejadian geologi yang:

1. Hanya memakai sumber yang sah, terverifikasi, dan memiliki dasar penggunaan.
2. Membedakan kejadian resmi dari berita, peta risiko, dan publikasi.
3. Memiliki provenance yang dapat diaudit sampai tingkat sumber dan run.
4. Memiliki waktu dan lokasi yang dapat diverifikasi, bukan hasil tebakan.
5. Mencakup 8 kategori sesuai bukti, atau secara eksplisit menyatakan kategori yang belum tersedia.
6. Dirilis sebagai versi baru tanpa menimpa baseline.

## 2. Prinsip yang tidak boleh dilanggar

- Baseline `data/geohazard_news_final_20261101T150501Z.csv` bersifat **immutable**.
- Jangan membuat database/backend/frontend pada tahap ini.
- Jangan mengaktifkan sumber `PERLU_IZIN` tanpa izin tertulis.
- Jangan mengakali robots, login, CAPTCHA, atau rate limit.
- Jangan mengisi waktu/lokasi/koordinat dengan asumsi.
- Jangan mengubah `published_time` menjadi `event_time`.
- Jangan menganggap berita, peta risiko, atlas, atau dashboard sebagai feed kejadian.
- Jangan menghapus duplikat atau baris sulit hanya untuk memperbaiki statistik.
- Jangan menyatakan “8 kategori lengkap” tanpa bukti kejadian untuk setiap kategori.

## 3. Kondisi awal

| Aspek | Kondisi saat ini |
|---|---|
| Baseline | 787 baris × 51 kolom; hash terverifikasi; 3 tes lulus |
| Feed aktif | 7: BMKG 3 XML, USGS, GDACS, ANTARA, Mongabay |
| Register | 54 baris: 7 aktif, 25 manual, 14 perlu izin, 6 belum tersedia, 2 tidak sesuai |
| Kategori target | 53 baris; 4 kategori kosong |
| `event_time` | 64 terisi; 723 tidak diketahui |
| Koordinat | 40; semua belum diverifikasi; 9 di luar Indonesia |
| Provenance | 16 label sumber; tanpa `source_id`, `collected_at`, `run_id`, `data_type` |
| Kesiapan | Baseline audit; belum operasional |

## 4. Urutan finalisasi

### Fase 0 — Freeze dan baseline evidence

Tujuan: memastikan titik awal tidak berubah.

Aksi:

1. Catat hash, jumlah baris/kolom, dan hasil tes baseline.
2. Simpan salinan read-only atau manifest hash.
3. Tetapkan bahwa semua pekerjaan berikutnya menghasilkan file baru.
4. Jangan mengubah `PRIMARY_DATASET_PATH` pada fase ini.

Output:

- Manifest baseline.
- Catatan verifikasi hash.
- Daftar file baru yang akan dibuat.

Exit criteria:

- `verify_dataset()` mengembalikan hash dan dimensi yang sama.
- Tidak ada perubahan pada file baseline.

### Fase 1 — Izin, lisensi, dan keputusan sumber

Tujuan: memisahkan “bisa diakses” dari “boleh dipakai”.

Aksi:

1. Ajukan izin tertulis ke PVMBG/Badan Geologi untuk:
   - API PVMBG (`vsi.esdm.go.id`);
   - Portal MBG (`field-reports`, gempa merusak, SIGAB, gunung api);
   - MAGMA (informasi letusan, laporan, level, VONA).
2. Minta konfirmasi BNPB tentang DIBI:
   - apakah ada API individual;
   - apakah ada ekspor resmi;
   - apakah dashboard boleh dipakai untuk data turunan.
3. Minta klarifikasi Portal Satu Data BNPB yang mengembalikan 403.
4. Audit lisensi ANTARA, Mongabay, dan 13 feed berita historis.
5. Tentukan status setiap sumber di register: aktif, manual, perlu izin, belum tersedia, atau tidak sesuai.

Output:

- Surat/izin atau catatan penolakan.
- Register yang diperbarui dengan tanggal dan bukti.
- Keputusan sumber per kategori.

Exit criteria:

- Tidak ada sumber `PERLU_IZIN` yang diaktifkan.
- Setiap sumber baru memiliki dasar penggunaan yang jelas.
- Sumber yang tidak diizinkan tetap nonaktif.

### Fase 2 — Kontrak sumber dan skema data

Tujuan: membuat data baru dapat diaudit sejak titik masuk.

Aksi:

1. Tambahkan field provenance wajib:
   - `record_id`
   - `source_id`
   - `source_name`
   - `source_type` (`official_structured`, `news`, `risk_map`, `publication`, `gazetteer`)
   - `data_type` (`event_feed`, `report`, `map`, `article`)
   - `source_url`
   - `collected_at`
   - `run_id`
   - `event_id`
   - `raw_payload_path`
   - `raw_payload_hash`
   - `license`
2. Tambahkan field kualitas:
   - `event_time_precision`
   - `event_time_basis`
   - `event_time_confidence`
   - `coordinate_source`
   - `coordinate_confidence`
   - `location_relation`
   - `scope_status`
   - `category_basis`
3. Pertahankan field lama untuk kompatibilitas; jangan rename massal.
4. Buat pemetaan eksplisit dari field lama ke field baru.
5. Tetapkan `event_id` hanya untuk kejadian, bukan artikel.
6. Tetapkan aturan bahwa satu artikel tidak otomatis menjadi satu kejadian.

Output:

- Skema baru.
- Data dictionary.
- Aturan pemetaan.
- Contoh payload per sumber.

Exit criteria:

- 100% baris baru memiliki `source_id`, `collected_at`, `run_id`, `data_type`, dan `raw_payload_hash`.
- Tidak ada baris baru tanpa `license` atau status penggunaan.
- Skema tidak merusak field baseline.

### Fase 3 — Stabilisasi sumber yang sudah aktif

Tujuan: memaksimalkan sumber yang sudah sah sebelum menambah sumber baru.

Aksi:

1. BMKG:
   - gunakan `autogempa`, `gempaterkini`, `gempadirasakan`;
   - simpan snapshot XML mentah;
   - ambil `DateTime`, koordinat, magnitudo, kedalaman, wilayah, dan potensi tsunami;
   - jangan memperlakukan potensi tsunami sebagai kejadian tsunami.
2. USGS:
   - gunakan Atom M4.5+ sebagai pendukung;
   - filter Indonesia untuk analisis nasional;
   - simpan `event_id` USGS;
   - tandai 9 koordinat luar Indonesia.
3. GDACS:
   - gunakan sebagai sinyal awal, bukan sumber resmi Indonesia;
   - filter Indonesia;
   - hormati batas laju;
   - tandai duplikasi Karhutla.
4. ANTARA/Mongabay:
   - perlakukan sebagai berita pendukung;
   - jangan jadikan bukti tunggal kejadian;
   - audit lisensi sebelum menyimpan isi penuh.

Output:

- Konektor/snapshot yang stabil.
- Contoh data per sumber.
- Log laju dan kegagalan.

Exit criteria:

- 7 feed aktif tetap 200 pada uji terkontrol.
- Tidak ada pelanggaran robots.
- Semua baris baru punya provenance.
- Berita dan feed resmi terpisah.

### Fase 4 — Sumber resmi tambahan dan izin

Tujuan: menutup kategori yang belum memiliki feed kejadian.

Aksi:

1. Jika izin diberikan:
   - gunakan Portal MBG untuk Gerakan Tanah dan Gempa Merusak;
   - gunakan PVMBG/MAGMA untuk Gunungapi;
   - validasi field, timestamp, koordinat, dan tingkat kejadian.
2. Jika izin tidak diberikan:
   - jangan gunakan data tersebut;
   - catat sebagai `BELUM_TERSEDIA` atau `PERLU_IZIN`.
3. Untuk Tsunami:
   - pertahankan sebagai atribut potensi pada gempa;
   - cari feed resmi tsunami terpisah hanya jika ada bukti.
4. Untuk Likuefaksi, Abrasi, Penurunan Muka Tanah, dan Semburan:
   - lakukan riset sumber resmi/daerah;
   - jangan mengotomatiskan peta risiko atau PDF.

Output:

- Sumber baru yang sah atau keputusan “belum tersedia”.
- Matriks cakupan yang diperbarui.

Exit criteria:

- Setiap kategori memiliki status sumber yang eksplisit.
- Tidak ada kategori yang disebut “tercakup” hanya karena berita/peta risiko.
- Sumber baru lulus uji akses dan review field.

### Fase 5 — Ekstraksi waktu dan lokasi

Tujuan: meningkatkan kualitas tanpa mengarang.

Aksi waktu:

1. Ekstrak `event_time` hanya dari:
   - field terstruktur sumber resmi;
   - tanggal/jam eksplisit di isi berita;
   - dokumen resmi.
2. Simpan bukti (`event_time_evidence`).
3. Bedakan aktual, tanggal saja, rentang, dan nowcast/prediksi.
4. Jangan memakai `published_time`.
5. Review manual 14 kandidat yang ada.

Aksi lokasi:

1. Bedakan lokasi kejadian dari lokasi administratif yang disebut.
2. Validasi koordinat terhadap sumber dan batas wilayah.
3. Tandai confidence: terverifikasi, indikasi, belum diverifikasi.
4. Jangan melakukan geocoding dari judul tanpa verifikasi.
5. Jangan memakai gazetteer pihak ketiga sebagai bukti kejadian.
6. Tandai 9 koordinat luar Indonesia.

Output:

- Aturan ekstraksi.
- Log review manual.
- Tingkat confidence per baris.

Exit criteria:

- 100% `event_time` memiliki bukti.
- 100% koordinat memiliki sumber dan status verifikasi.
- Tidak ada perubahan otomatis pada baseline.

### Fase 6 — Kategorisasi dan entity resolution

Aksi kategori:

1. Gunakan 8 kategori resmi + `Lainnya`.
2. Pisahkan `scope_status`:
   - `dalam_8_kategori`;
   - `di_luar_8_kategori`;
   - `tidak_terklasifikasi`.
3. Jangan memetakan Karhutla/Cuaca Ekstrem ke kategori geologi.
4. Review manual kandidat Sinabung dan kandidat serupa.
5. Simpan alasan perubahan kategori.

Aksi deduplikasi:

1. Gunakan `source_id + event_id` sebagai kunci utama.
2. Untuk berita, gunakan URL, judul, waktu, dan entitas.
3. Jangan menghapus duplikat yang memiliki provenance berbeda tanpa catatan.
4. Pertahankan kelompok duplikat GDACS sebagai bukti, bukan sebagai event tambahan.

Output:

- Log keputusan kategori.
- Log deduplikasi.
- Dataset kandidat.

Exit criteria:

- 0 URL duplikat.
- Semua duplikat judul/isi direview.
- Tidak ada kategori di luar kontrak.
- Setiap perubahan kategori memiliki alasan.

### Fase 7 — Quality gate dan release kandidat

Buat file baru:

`data/geohazard_news_<YYYYMMDDTHHMMSSZ>.csv`

Jangan menimpa baseline. Buat manifest berisi hash, jumlah baris/kolom, daftar sumber, izin, dan status gate.

Quality gate:

| Gate | Syarat | Gagal jika |
|---|---|---|
| G0 Baseline | Baseline lama tidak berubah | Hash/baris/kolom berubah |
| G1 Provenance | 100% baris baru punya `source_id`, `collected_at`, `run_id`, `data_type`, `raw_payload_hash` | Ada field kosong |
| G2 Required fields | 100% `judul`, `sumber`, `url`, `kategori` terisi | Ada field wajib kosong |
| G3 Kategori | 100% kategori dalam kontrak; out-of-scope terpisah | Ada kategori liar atau pencampuran |
| G4 Waktu | 100% `event_time` punya bukti; nowcast ditandai | Ada waktu hasil tebakan |
| G5 Lokasi | 100% koordinat punya sumber/confidence | Ada koordinat tanpa asal |
| G6 Duplikasi | 0 URL duplikat; duplikat lain direview | Ada duplikasi tanpa catatan |
| G7 Cakupan | Setiap kategori punya status register + bukti | Klaim tercakup tanpa sumber resmi |
| G8 Release | Hash/manifest/tests tersedia | Tidak ada manifest |

Output:

- Dataset kandidat.
- Manifest.
- Laporan gate.
- Daftar kegagalan.

Exit criteria:

- Semua gate P0 lulus atau diberi pengecualian tertulis.
- Dataset kandidat tidak menimpa baseline.

### Fase 8 — Validasi, persetujuan, dan publikasi

Aksi:

1. Review independen terhadap sampel baris per kategori.
2. Bandingkan distribusi kategori/waktu/lokasi dengan baseline.
3. Uji ulang semua sumber yang dipakai.
4. Pastikan izin/lisensi masih berlaku.
5. Setujui atau tolak rilis.
6. Jika disetujui, perbarui `PRIMARY_DATASET_PATH` secara eksplisit dan catat di changelog.
7. Jika ditolak, pertahankan baseline dan catat alasan.

Exit criteria:

- Ada keputusan rilis tertulis.
- Ada changelog dan audit trail.
- Tidak ada perubahan diam-diam.

## 5. Prioritas kerja

### P0 — blocker

- Freeze baseline dan manifest.
- Izin PVMBG/Portal MBG/MAGMA.
- Konfirmasi DIBI/BNPB dan Portal Satu Data.
- Kebijakan lisensi berita.
- Skema provenance.

### P1 — kualitas inti

- Stabilkan BMKG/USGS/GDACS.
- Pisahkan event feed, berita, peta risiko.
- Validasi waktu dan koordinat.
- Deduplikasi berbasis event.
- Review kandidat kategori.

### P2 — perluasan cakupan

- Riset sumber resmi untuk Likuefaksi, Abrasi, Penurunan Muka Tanah, Semburan.
- Evaluasi laporan daerah/BNPB/KKP/Badan Geologi.
- Jangan menambah scraper umum sebagai solusi.

## 6. Keputusan yang harus diambil

1. Apakah `Lainnya` akan dipertahankan sebagai fallback, atau diganti menjadi `di_luar_8_kategori` + `tidak_terklasifikasi` di kolom terpisah?
2. Apakah berita diizinkan masuk dataset final sebagai baris pendukung, atau hanya sebagai sinyal yang harus diverifikasi?
3. Apakah kategori tanpa feed resmi boleh dirilis dengan status “belum tersedia”, atau harus menunggu?
4. Berapa definisi minimum “satu kejadian” untuk sumber yang memiliki banyak titik per laporan, seperti Portal MBG?
5. Siapa yang menyetujui aktivasi sumber baru dan perubahan `PRIMARY_DATASET_PATH`?

Rekomendasi:

- Pertahankan `Lainnya` hanya sebagai fallback tampilan, tetapi simpan `scope_status` terpisah.
- Berita hanya pendukung; bukan bukti tunggal.
- Kategori tanpa sumber resmi dirilis dengan status eksplisit, bukan diklaim lengkap.
- Satu kejadian harus memiliki `event_id` atau kombinasi sumber+waktu+lokasi yang disepakati.
- Aktivasi sumber dan perubahan primary path memerlukan persetujuan tertulis.

## 7. Verifikasi teknis

Jalankan sebelum dan sesudah pekerjaan:

```powershell
& ".venv\Scripts\python.exe" -c "import dataset_baseline; print(dataset_baseline.verify_dataset())"
& ".venv\Scripts\python.exe" -m unittest -q test_dataset_baseline
& ".venv\Scripts\python.exe" feeds.py
```

Hasil yang diharapkan untuk baseline saat ini:

- hash `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06`;
- 787 baris;
- 51 kolom;
- 3 tes lulus;
- 7 feed aktif.

## 8. Risiko dan mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Izin PVMBG/BNPB tidak turun | Kategori tetap kosong | Rilis dengan status belum tersedia; jangan pakai data tanpa izin |
| Sumber berubah format | Parser gagal | Snapshot mentah, validasi skema, alert |
| Berita dianggap kejadian | False event | Pisahkan `source_type`/`data_type`; review |
| Waktu publikasi dianggap waktu kejadian | Analisis salah | Gate G4; bukti wajib |
| Koordinat salah/global | Peta menyesatkan | Validasi, confidence, filter domain |
| Duplikasi GDACS | Hitungan berlebih | Dedup berbasis event; review |
| Scope creep ke 20+ kategori | Data tidak konsisten | Kontrak 8 kategori + fallback |
| Scraping agresif | Blokir/legal | Rate limit, robots, izin |
| Baseline tertimpa | Kehilangan audit trail | File baru + manifest + hash |

## 9. Exit criteria final

Dataset baru hanya boleh dirilis jika:

1. Baseline lama masih utuh dan terverifikasi.
2. Semua sumber baru punya izin/status yang jelas.
3. Semua baris baru punya provenance lengkap.
4. Tidak ada klaim kategori tanpa bukti sumber.
5. Waktu dan koordinat punya bukti/confidence.
6. Duplikasi dan out-of-scope tercatat.
7. Quality gate dan manifest tersedia.
8. Ada persetujuan rilis tertulis.

Jika salah satu belum terpenuhi, statusnya tetap **baseline audit**, bukan dataset final tervalidasi.

## 10. Ringkasan tindakan berikutnya

1. Freeze baseline dan catat hash.
2. Kirim permintaan izin PVMBG/Badan Geologi dan klarifikasi BNPB/DIBI.
3. Audit lisensi ANTARA/Mongabay/feed historis.
4. Finalkan skema provenance dan aturan kategori.
5. Stabilkan BMKG/USGS/GDACS.
6. Review 14 kandidat `event_time` dan kandidat Sinabung.
7. Bangun dataset kandidat baru, jalankan gate, lalu putuskan rilis.
