# FIX 07 - Relevansi Berita dan Pemisahan dari Kategori

Tanggal: **2026-11-05**  
Fix ID: `FIX-RELEVANCE-20261105`  
Status: **classifier relevansi, schema, backfill, dan filter dashboard selesai; data lama dipertahankan**

## 1. Tujuan dan batas

FIX 07 memisahkan dua pertanyaan yang sebelumnya tercampur:

1. Apakah dokumen benar-benar membahas geohazard?
2. Jika relevan, termasuk kategori geohazard yang mana?

Sebelumnya dashboard memakai seluruh dokumen aktif. Akibatnya berita umum, satwa, politik, ekonomi, cuaca, kebakaran hutan, dan artikel rekreasi ikut tampil. FIX 07 menambahkan status relevansi eksplisit dan hanya menampilkan dokumen berstatus `relevan`.

Batas yang dipertahankan:

- Tidak menghapus dokumen, event, relasi, raw payload, atau baris klasifikasi lama.
- Tidak mengubah baseline `data/geohazard_news_final_20261101T150501Z.csv`.
- Tidak mengubah `document`, `document_classification`, `event`, `category`, atau `document_event_link`.
- Dashboard tetap read-only.
- Kategori lama tetap disimpan; relevansi adalah status terpisah.
- Dokumen `perlu_review` tidak ditampilkan sebagai berita sampai direview manual.

## 2. Akar masalah

Audit data aktif menemukan:

| Temuan | Jumlah |
|---|---:|
| Dokumen aktif | 863 |
| Klasifikasi `Lainnya` | 778 |
| `Lainnya` dengan scope `unclassified` | 672 |
| `Lainnya` dengan scope `out_of_scope` | 106 |
| `Gempabumi` | 76 |
| `Gunungapi` | 5 |
| `Abrasi dan Akresi` | 3 |
| `Gerakan Tanah` | 1 |

`Lainnya` bukan berarti otomatis relevan. Sebagian besar justru berita umum: satwa/lingkungan, politik/ekonomi, pendidikan, olahraga, rekreasi, banjir, kekeringan, karhutla, dan cuaca ekstrem. Sebaliknya, ada dokumen yang secara kategori sudah benar tetapi konteksnya bukan geohazard, misalnya berita hukum tentang dana bencana gempa.

Contoh kasus yang diperbaiki:

```text
Adik eks Kepala BNPB diduga gunakan dana bencana gempa NTT
```

Judul mengandung kata `gempa`, tetapi konteksnya adalah dugaan korupsi. Sebelum patch, dokumen ini bisa lolos sebagai berita gempa. Setelah patch menjadi `tidak_relevan` dengan basis `konteks_non_geohazard`.

## 3. Aturan relevansi

Classifier baru: `relevance.py`, versi `fix07-context-v1`.

Status:

| Status | Makna | Tampil di dashboard |
|---|---|---|
| `relevan` | Dokumen membahas geohazard/konteks geologi yang didukung bukti | Ya |
| `tidak_relevan` | Tidak ada konteks geohazard, atau konteksnya di luar scope | Tidak |
| `perlu_review` | Sinyal geologi ada, tetapi bukti peristiwa/konteks belum cukup | Tidak |

Aturan utama:

- Kategori 8 geohazard dipakai lebih dulu melalui `detect_category_detail`.
- `Lainnya` hanya dipakai jika ada konteks geologi yang jelas, misalnya fenomena daratan baru atau proses geologi lain.
- Out-of-scope eksplisit: banjir, kekeringan, karhutla, cuaca ekstrem, hujan lebat, petir, angin puting beliung, gelombang tinggi, kabut asap.
- Konteks non-geohazard eksplisit: satwa/lingkungan umum, konservasi, sampah, mangrove tanpa proses abrasi, politik, ekonomi, hukum, olahraga, hiburan, pendidikan, teknologi, agama, dan rekreasi.
- Metafora `gempa saham`, `gempa politik`, dan sejenisnya ditolak.
- Artikel edukasi tanpa peristiwa masuk `perlu_review`, bukan langsung `relevan` atau `tidak_relevan`.
- Sumber resmi tidak otomatis relevan; peringatan cuaca resmi tetap `tidak_relevan` jika di luar 8 kategori.

## 4. Perubahan kode

| File | Perubahan |
|---|---|
| `relevance.py` | Classifier relevansi kontekstual, status, basis, evidence, confidence, versi. |
| `database/schema.sql` | Tabel `document_relevance` dan index status/kategori. |
| `geohazard_pipeline/schema.py` | Registry tabel/kolom/PK untuk `document_relevance`. |
| `geohazard_pipeline/build.py` | `build_document_relevance()` dari judul, ringkasan, kategori, dan sumber. |
| `geohazard_pipeline/runner.py` | Menulis relevansi setiap kali pipeline berjalan. |
| `geohazard_pipeline/baseline_import.py` | Mengisi relevansi untuk 787 baris baseline legacy. |
| `scripts/backfill_document_relevance.py` | Backfill idempotent, `--dry-run`, `--json`, tidak menimpa hasil review manual. |
| `dashboard/repository.py` | Semua query dokumen dan berita hanya memakai status `relevan`; statistik, kategori, tanggal, dan latest news ikut difilter. |
| `dashboard/templates/index.html` | Label statistik dan empty state menjelaskan bahwa berita yang tampil hanya yang relevan. |
| `test_relevance.py` | 12 test classifier dan idempotensi backfill. |
| `test_dashboard.py` | Expected count diperbarui dan assertion relevansi ditambahkan. |

Kolom `document_relevance`:

```text
document_id, relevance_status, relevance_category, relevance_basis,
relevance_confidence, relevance_evidence, classifier_version,
classified_at, review_status, reviewed_at, reviewed_by, relevance_notes
```

## 5. Migrasi dan keamanan data

Backup sebelum migrasi:

```text
database/backups/geohazard-pre-fix07-20261104T212440Z.db
```

Proses backfill:

1. Verifikasi SHA-256 baseline.
2. Membuat tabel/index jika belum ada.
3. Mengambil konteks dari baseline `isi_berita` atau raw payload.
4. Mengklasifikasi seluruh dokumen aktif.
5. Upsert hanya ke `document_relevance`.
6. Tidak menimpa baris dengan `review_status = 'reviewed'`.

Hash baseline setelah backfill tetap:

```text
be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06
```

Jumlah baris setelah backfill:

| Tabel | Jumlah |
|---|---:|
| `document` | 863 |
| `document_classification` | 863 |
| `document_relevance` | 863 |
| `event` | 75 |
| `document_event_link` | 81 |
| `raw_payload` | 8 |
| `event_assertion` | 449 |
| `location_mention` | 36 |
| `change_log` | 2789 |
| `import_log` | 3 |

Tidak ada dokumen/event yang dihapus. Backfill hanya menambah/mengubah baris relevansi.

## 6. Hasil klasifikasi

| Status | Sebelum | Sesudah |
|---|---:|---:|
| `relevan` | belum ada | 84 |
| `tidak_relevan` | belum ada | 777 |
| `perlu_review` | belum ada | 2 |
| Total | 863 | 863 |

Rincian dokumen relevan:

| Kategori | Dokumen relevan |
|---|---:|
| `Gempabumi` | 75 |
| `Gunungapi` | 5 |
| `Abrasi dan Akresi` | 3 |
| `Gerakan Tanah/Tanah Longsor` | 1 |
| `Lainnya` | 0 |

Rincian baseline vs pipeline:

| Kelompok | Relevan | Tidak relevan | Perlu review | Total |
|---|---:|---:|---:|---:|
| Baseline legacy | 52 | 734 | 1 | 787 |
| Pipeline | 32 | 43 | 1 | 76 |
| Total | 84 | 777 | 2 | 863 |

Dua dokumen `perlu_review` adalah duplikat artikel:

```text
Ada daratan baru di dekat Anak Krakatau, ini penjelasan ahli
```

Keduanya ditahan dari dashboard karena belum ada bukti peristiwa yang cukup.

Konteks pipeline yang tidak ditemukan: **32 dokumen**. Sebagian besar tetap dapat diklasifikasi dari judul dan kategori sumber. Angka ini dicatat sebagai batasan, bukan dianggap konteks lengkap.

## 7. Dampak dashboard

| Komponen | Sebelum | Sesudah |
|---|---:|---:|
| Total dokumen | 863 | 84 |
| Total event | 75 | 75 |
| Kategori berdata | 5 dari 9 | 5 dari 9 |
| Latest news | campuran relevan/tidak | hanya `relevan` |

Hasil filter utama:

| Filter | Dokumen | Event |
|---|---:|---:|
| Tanpa filter | 84 | 75 |
| `Gempabumi` | 75 | 68 |
| `Jawa Barat` | 7 | 7 |
| Oktober 2026 | 46 | 64 |

Contoh berita relevan yang tampil:

- `Gempa M5.7 193 km BaratDaya KAB-SUKABUMI-JABAR`
- `Gunung Anak Krakatau Erupsi, BMKG Pantau Sebaran Abu Vulkanik via Satelit`
- `Empat Penambang Emas Tewas Terimbun Longsor di Sumbar`
- `AHY dan Ahmad Luthfi Tanam Mangrove di Demak untuk Atasi Abrasi Pantura`

Contoh yang tidak lagi tampil:

- `Monyet Ekor Panjang Masuk Permukiman Warga`
- `Hujan Lebat disertai Petir di Riau`
- `Green forest fire notification in Indonesia`
- `Persib Bandung ...`
- `Konservasi Mangrove Clungup ...`
- `Adik eks Kepala BNPB diduga gunakan dana bencana gempa NTT`

## 8. Test dan verifikasi

```text
.venv\Scripts\python.exe -m unittest test_relevance.py -v
12 test, lulus semua

.venv\Scripts\python.exe -m unittest test_dashboard.py -v
11 test, lulus semua

.venv\Scripts\python.exe -m unittest discover -p "test_*.py" -v
179 test dijalankan; 178 lulus; 1 error lama test_scraper
```

Error lama yang tidak terkait FIX 07:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

Verifikasi tambahan:

- `latest_news` hanya berisi `relevance_status = 'relevan'`.
- Tabel relevansi mencakup seluruh 863 dokumen aktif.
- Backfill kedua tidak menggandakan baris.
- Baris yang sudah `reviewed` tidak ditimpa.
- `node --check dashboard/static/app.js` lulus.
- API dashboard dan halaman utama tetap merespons 200.

## 9. Batasan dan rekomendasi

Batasan:

- Relevansi tidak sama dengan geographic scope. Dokumen gempa internasional tetap dapat `relevan` sebagai kategori geohazard; filter Indonesia/luar Indonesia belum diterapkan di FIX 07.
- 32 dokumen pipeline tidak memiliki konteks tambahan dari raw payload; klasifikasi bertumpu pada judul dan kategori sumber.
- Dua dokumen edukasi geologi masih `perlu_review` dan perlu keputusan manual.
- Dashboard akan gagal jika dijalankan pada database lama yang belum memiliki tabel `document_relevance`. Jalankan backfill/migrasi lebih dulu.
- Pipeline baru harus selalu menulis `document_relevance`; jika tidak, dokumen baru tidak akan tampil.

Rekomendasi:

1. Review manual dua dokumen `perlu_review`.
2. Tambahkan aturan geographic scope ke tampilan berita jika dashboard memang hanya untuk kejadian Indonesia.
3. Pertahankan `relevance.py` sebagai satu sumber keputusan; jangan menduplikasi aturan filter di frontend.
4. Jalankan backfill ulang setelah impor besar, lalu bandingkan status dan kategori.
5. Tambahkan test regresi untuk judul berita baru yang sering muncul.

## 10. File terkait

- `relevance.py`
- `scripts/backfill_document_relevance.py`
- `database/schema.sql`
- `geohazard_pipeline/schema.py`
- `geohazard_pipeline/build.py`
- `geohazard_pipeline/runner.py`
- `geohazard_pipeline/baseline_import.py`
- `dashboard/repository.py`
- `dashboard/templates/index.html`
- `test_relevance.py`
- `test_dashboard.py`
- `database/backups/geohazard-pre-fix07-20261104T212440Z.db`
