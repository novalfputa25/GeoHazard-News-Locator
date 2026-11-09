# FIX 06 - Materialisasi Dokumen Pendukung BMKG Gempa Dirasakan

Tanggal: **2026-11-04**  
Database: `database/geohazard.db`  
Fix ID: `FIX06-MATERIALIZE-SUPPORTING-DOCUMENTS`  
Status: **selesai diimplementasikan dan diterapkan; idempotent; tidak membuat event baru**

## 1. Tujuan dan batas

FIX 06 mematerialisasi tiga record `bmkg_gempa_dirasakan` yang telah dikonfirmasi pada FIX 05 sebagai dokumen pendukung event yang sudah ada:

1. Oksibil
2. Tanimbar/FFB
3. Gunungkidul

Tujuan teknis:

- Membuat baris `document` untuk record yang belum ada.
- Membuat baris `document_event_link` bertipe `supporting`.
- Mempertahankan event yang sudah ada tanpa membuat event baru.
- Menjaga provenance raw payload dan ID deterministik.
- Menjaga baseline, kategori, waktu event, lokasi event, dan hasil FIX sebelumnya.
- Menjadikan proses aman dijalankan berulang.

Batas yang dipertahankan:

- Tidak membuat event baru.
- Tidak menggabungkan event.
- Tidak mengubah kategori bahaya atau `category_scope`.
- Tidak mengubah `is_inside_indonesia` atau status cakupan geografis.
- Tidak mengubah baseline `data/geohazard_news_final_20261101T150501Z.csv`.
- Tidak menimpa raw payload.
- Tidak mengubah skema database.

## 2. Implementasi

Script baru:

- `scripts/fix06_materialize_supporting_documents.py`

Pengujian baru:

- `test_fix06_supporting_documents.py`

Cara kerja script:

1. Mencari record target pada raw payload run pipeline dan pilot.
2. Menghitung ulang `document_id` dan `event_id` memakai fungsi identitas pipeline.
3. Memastikan event target sudah ada; jika tidak ada, proses dibatalkan.
4. Memastikan `source` dan `raw_payload` tersedia.
5. Membuat `document` dan `document_classification` bila belum ada.
6. Membuat `document_event_link` dengan `relevance=supporting` dan `is_primary=tidak`.
7. Menambahkan `event_assertion` dan `location_mention` bila belum ada.
8. Mencatat perubahan ke `change_log` dan `import_log`.
9. Memvalidasi invariant sebelum commit.
10. Mendukung `--dry-run` dan aman dijalankan berulang.

## 3. Jumlah data sebelum dan sesudah

| Tabel | Sebelum | Sesudah | Selisih |
|---|---:|---:|---:|
| `document` | 862 | 863 | +1 |
| `document_event_link` | 80 | 81 | +1 |
| `event` | 75 | 75 | 0 |
| `raw_payload` | 7 | 8 | +1 |
| `document_classification` | 862 | 863 | +1 |
| `event_assertion` | 442 | 449 | +7 |
| `location_mention` | 35 | 36 | +1 |
| `change_log` | 2777 | 2789 | +12 |
| `import_log` | 2 | 3 | +1 |

Hanya Gunungkidul yang baru dimaterialisasi oleh FIX 06. Oksibil dan Tanimbar sudah menjadi dokumen dan link `supporting` pada `RUN-20261103T160737Z`.

## 4. Hasil relasi tiga target

| Label | `document_id` | `event_id` | `link_id` | Relevance | Primary | Status |
|---|---|---|---|---|---|---|
| Oksibil | `DOC-f887636094654d53` | `EVT-BMKG-72D9473D8378` | `LINK-133FB0A62DE5` | `supporting` | `tidak` | sudah ada |
| Tanimbar/FFB | `DOC-cfd2f5df338e302d` | `EVT-BMKG-FFB357F335AE` | `LINK-0954F9130615` | `supporting` | `tidak` | sudah ada |
| Gunungkidul | `DOC-57dbfb14c6cc3343` | `EVT-BMKG-608A37F640B2` | `LINK-F86F218D04FB` | `supporting` | `tidak` | dimaterialisasi |

Judul dokumen:

- Oksibil: `Gempa M6 - Pusat gempa berada di darat 153 km tenggara Oksibil`
- Tanimbar/FFB: `Gempa M6.4 - Pusat gempa berada di laut 60 km Baratlaut Larat-Kep.Tanimbar`
- Gunungkidul: `Gempa M5.4 - Pusat gempa berada di laut 137 km Selatan Gunungkidul`

## 5. Provenance

| Label | Raw payload | Run dokumen | Path raw | SHA-256 |
|---|---|---|---|---|
| Oksibil | `RAW-bmkg_gempa_dirasakan-20261103T160737Z-30d334eb` | `RUN-20261103T160737Z` | `data/pipeline/RUN-20261103T160737Z/raw/bmkg_gempa_dirasakan.xml` | `30d334eb921ea9b097029b8295a3ee1e22d26685e1979a830fd90e72cdbf5328` |
| Tanimbar/FFB | `RAW-bmkg_gempa_dirasakan-20261103T160737Z-30d334eb` | `RUN-20261103T160737Z` | `data/pipeline/RUN-20261103T160737Z/raw/bmkg_gempa_dirasakan.xml` | `30d334eb921ea9b097029b8295a3ee1e22d26685e1979a830fd90e72cdbf5328` |
| Gunungkidul | `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | `PILOT-20261102T110641Z` | `data/pilot/runs/PILOT-20261102T110641Z/raw/bmkg_gempa_dirasakan.xml` | `9b1bc264382d54c9b69471412159d1f96c05741598c4f39047bf430e64c2c47b` |

Gunungkidul memakai raw pilot karena record tersebut tidak ada pada raw `RUN-20261103T160737Z`. Raw payload pilot ditambahkan ke database agar foreign key `document_raw_payload_id` valid dan provenance tetap lengkap.

External ID:

- Oksibil: `bmkg_gempa_dirasakan|2026-10-29T03:26:49+00:00|-5.4500|141.9000|6.0`
- Tanimbar/FFB: `bmkg_gempa_dirasakan|2026-10-28T22:06:47+00:00|-6.3400|130.5200|6.4`
- Gunungkidul: `bmkg_gempa_dirasakan|2026-10-27T14:43:13+00:00|-9.2000|110.3900|5.4`

## 6. Validasi

Semua pemeriksaan FIX 06 lulus:

| Pemeriksaan | Hasil |
|---|---|
| Tiga dokumen target ada tepat satu | lulus |
| Tiga link target ada tepat satu | lulus |
| Semua link target `supporting` dan bukan primary | lulus |
| Tidak ada duplikasi dokumen target | lulus |
| Tidak ada duplikasi link target | lulus |
| Jumlah dan ID event tidak berubah | lulus |
| Kategori tidak berubah | lulus |
| `event_time` tidak berubah | lulus |
| `event_location` tidak berubah | lulus |
| Raw payload lama tidak berubah | lulus |
| Baseline tetap 787 baris x 51 kolom | lulus |
| SHA-256 baseline tidak berubah | lulus |
| `PRAGMA foreign_key_check` bersih | lulus |

Run kedua pada database aktual menghasilkan:

```text
Document: 863 -> 863; Link: 81 -> 81; Event: 75 -> 75
Inserted: {}
```

Artinya proses idempotent dan tidak menambah data ganda.

## 7. Pengujian

| Perintah | Hasil |
|---|---|
| `.\.venv\Scripts\python.exe -m unittest test_fix06_supporting_documents.py -v` | 9/9 OK |
| `.\.venv\Scripts\python.exe -m unittest test_pipeline_stage12.py -v` | 5/5 OK |
| `.\.venv\Scripts\python.exe -m unittest discover -p "test_*.py" -v` | 135 OK, 1 error lama |

Error pada full suite berasal dari `test_scraper.py`:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

Error tersebut tidak terkait FIX 06 dan tidak berasal dari perubahan pada laporan ini.

## 8. File yang dibuat atau diubah

Dibuat:

- `scripts/fix06_materialize_supporting_documents.py`
- `test_fix06_supporting_documents.py`
- `reports/FIX_06_SUPPORTING_DOCUMENTS.md`

Diubah:

- `database/geohazard.db`

Tidak diubah:

- Baseline final.
- Raw payload yang sudah ada.
- Skema database.
- Output FIX 01 sampai FIX 05.

## 9. Cara menjalankan

Validasi tanpa commit:

```powershell
.\.venv\Scripts\python.exe scripts\fix06_materialize_supporting_documents.py --database database\geohazard.db --dry-run
```

Terapkan:

```powershell
.\.venv\Scripts\python.exe scripts\fix06_materialize_supporting_documents.py --database database\geohazard.db
```

Jalankan tes:

```powershell
.\.venv\Scripts\python.exe -m unittest test_fix06_supporting_documents.py -v
```

## 10. Kesimpulan

FIX 06 berhasil mematerialisasi Gunungkidul sebagai dokumen pendukung dan mempertahankan Oksibil serta Tanimbar yang sudah ada. Ketiga record kini memiliki link `supporting` ke event yang sama, tanpa event baru, tanpa merge, tanpa perubahan baseline, dan tanpa duplikasi. Database akhir memiliki 863 dokumen, 81 link, 75 event, dan 8 raw payload.
