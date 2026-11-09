# Pipeline Item Selection

Status: selesai  
Tanggal: 2026-11-04  
Lingkup: seleksi item pipeline, pagination opt-in, metrik manifest, dan pengujian.  
Catatan: laporan ini dibuat tanpa mengubah kode, database, atau baseline.

## 1. Tujuan Perubahan

- Menghapus batas tetap yang memotong item sebelum diproses, terutama batas 10 item pada pilot dan batas default 100 item pada runner/CLI.
- Memisahkan jumlah item yang berhasil diparse, dipilih, dan dimasukkan ke tabel run.
- Menambahkan batas item per sumber tanpa menimpa konfigurasi feed secara global.
- Menambahkan pagination opt-in untuk feed yang benar-benar menyediakan halaman berikutnya.
- Menambahkan deduplikasi item per sumber dan pencatatan jumlah duplikat.
- Menjaga provenance raw payload per halaman serta delay/timeout untuk request live.
- Menjaga kompatibilitas dengan pipeline stage 12 dan hasil FIX06.

## 2. Daftar File yang Diubah

| File | Perubahan |
|---|---|
| `geohazard_pipeline/runner.py` | Default `max_items=None`, seleksi setelah parsing, dedup per sumber, pagination, delay antar-request live, metrik manifest baru. |
| `geohazard_pipeline/parsers.py` | Menghapus penghentian parser berdasarkan `max_items` pada `parse_gdacs` dan `parse_news_rss`; parser mengembalikan seluruh item. |
| `geohazard_pipeline/fetch.py` | `read_offline_payload`, `save_raw`, dan `raw_payload_row` menerima `page_number` untuk payload halaman ke-2 dan seterusnya. |
| `geohazard_pipeline/util.py` | `load_active_feed_configs` hanya memakai `max_items` global jika feed tidak punya nilai `max_items` sendiri. |
| `run_pipeline.py` | `--max-items` default `None`; menambah `--source-max-items SOURCE=LIMIT` dan `--delay`. |
| `feeds.py` | Dokumentasi opsi `max_items` dan `pagination` per feed. |
| `scripts/pilot_collect_official_geohazard.py` | `MAX_ITEMS_PER_SOURCE` menjadi `None`; limit pilot configurable per sumber; catatan ringkasan tidak lagi menyebut batas 10 item. |
| `test_pipeline_item_selection.py` | Tes baru untuk seleksi tanpa limit, limit per sumber, override limit, pagination, dedup, dan import idempotent. |

Database `database/geohazard.db` dan baseline `data/geohazard_news_final_20261101T150501Z.csv` tidak diubah.

## 3. Mekanisme Seleksi Item Sebelum dan Sesudah Perubahan

### Sebelum

- `run_pipeline()` memakai default `max_items=100`.
- `load_active_feed_configs(max_items)` menimpa `max_items` semua feed dengan nilai global.
- Runner memotong item dengan `items = items[: config.get("max_items", max_items)]` sebelum item diproses.
- `parse_gdacs` dan `parse_news_rss` juga berhenti saat mencapai `max_items`.
- Pilot memakai `MAX_ITEMS_PER_SOURCE = 10` dan `parsed_items[:MAX_ITEMS_PER_SOURCE]`.
- CLI `run_pipeline.py --max-items` default `100`.
- Manifest mencatat `items_parsed` sama dengan `items_selected` karena pemotongan terjadi sebelum pencatatan.

### Sesudah

- `run_pipeline()` memakai default `max_items=None`, artinya seluruh item yang berhasil diparse dipertimbangkan.
- Parser mengembalikan seluruh item; seleksi dipusatkan di runner.
- Item dideduplikasi per sumber berdasarkan `external_id`, `canonical_url`, `document_url`, atau `title`.
- Seleksi dilakukan setelah parsing dan dedup.
- Urutan prioritas limit:
  1. `--source-max-items SOURCE=LIMIT`
  2. `max_items` pada konfigurasi feed
  3. `--max-items` global
  4. tanpa limit
- Manifest mencatat:
  - `items_parsed`: seluruh item hasil parsing, termasuk duplikat antarhalaman.
  - `items_selected`: item unik yang dipilih setelah dedup dan limit.
  - `items_imported`: item yang dimasukkan ke tabel run.
  - `items_duplicates`: item yang dibuang karena duplikat.
  - `pages_fetched`, `pages_succeeded`, `max_items`, dan `stop_reason`.
- Delay live diterapkan antar-request, termasuk antar-sumber dan antarhalaman. Offline replay tidak memakai delay.
- Pilot tidak lagi memotong pada 10 item; limit dapat diatur lewat `max_items` pada `SOURCE_CONFIG`.

## 4. Mekanisme Pagination

Pagination bersifat opt-in melalui kunci `pagination` pada konfigurasi feed. Tanpa kunci ini, pipeline hanya mengambil satu halaman.

Contoh konfigurasi:

```python
{
    "id": "contoh_feed",
    "url": "https://example.com/feed",
    "tipe": "rss",
    "max_items": 50,
    "pagination": {
        "type": "query",
        "param": "page",
        "max_pages": 3,
    },
    "aktif": True,
}
```

Tipe pagination yang didukung:

- `query`: menambahkan parameter halaman, misalnya `?page=2`; parameter query lain dipertahankan.
- `template`: memakai template khusus dengan placeholder `{page}` dan `{url}`.
- `path`: menambahkan `/page/<n>/` ke URL dasar.

Perilaku runner:

- Halaman 1 memakai URL asli.
- Halaman berikutnya dibuat sesuai tipe pagination dan `max_pages`.
- Setiap halaman disimpan sebagai raw payload terpisah, misalnya `source_id_p2.xml`.
- Item dari semua halaman dideduplikasi sebelum seleksi.
- Pengambilan halaman berhenti jika:
  - limit item per sumber sudah tercapai (`stop_reason=max_items`);
  - halaman berikutnya tidak menghasilkan item baru (`stop_reason=no_new_items`);
  - fetch gagal (`stop_reason=fetch_error`).

Feed aktif saat ini tidak dikonfigurasi dengan pagination karena belum ada endpoint yang terbukti mendukungnya. Pengujian pagination dilakukan dengan fixture sintetis.

## 5. Hasil Pengujian

### Tes baru

Perintah:

```powershell
.\.venv\Scripts\python.exe -m unittest test_pipeline_item_selection.py -v
```

Hasil: **6/6 lulus**.

Cakupan:

- Semua item dipilih saat tidak ada limit.
- Limit per sumber diterapkan setelah parsing.
- Limit per sumber mengalahkan limit global.
- Pagination mengambil beberapa halaman, mendeteksi duplikat, dan menyimpan raw payload per halaman.
- Pagination berhenti saat limit tercapai.
- Import item terpilih bersifat idempotent.

### Tes pipeline existing

Perintah:

```powershell
.\.venv\Scripts\python.exe -m unittest test_pipeline_stage12.py test_pipeline_item_selection.py -v
```

Hasil: **11/11 lulus**.

### Full suite

Perintah:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Hasil: **142 tes dijalankan, 141 lulus, 1 error lama**.

Error yang tersisa:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

Error tersebut berasal dari `test_scraper.py` dan sudah ada sebelum perubahan ini; bukan regresi dari Pipeline Item Selection.

### Replay offline seluruh sumber aktif

Replay memakai raw run `RUN-20261103T160737Z`:

- 7 sumber berhasil diproses.
- 75 dokumen dihasilkan.
- `issues` kosong.
- Tidak ada limit global yang diterapkan, sehingga `items_parsed == items_selected == items_imported`.

## 6. Hasil Pengujian CLI

Perintah yang diuji:

```powershell
$out = Join-Path $env:TEMP "opencode\cli-selection"
.\.venv\Scripts\python.exe run_pipeline.py `
  --offline `
  --raw-dir data\pipeline\RUN-20261103T160737Z\raw `
  --output-root $out `
  --run-id RUN-CLI-SELECTION `
  --delay 0 `
  --source-max-items mongabay_indonesia=5 `
  --source-max-items antaranews_warta_bumi=7
```

Hasil:

| Sumber | Parsed | Selected | Imported | Stop reason |
|---|---:|---:|---:|---|
| `mongabay_indonesia` | 20 | 5 | 5 | `max_items` |
| `antaranews_warta_bumi` | 20 | 7 | 7 | `max_items` |

Kedua sumber tidak menghasilkan error. Hasil ini membuktikan bahwa limit per sumber melalui CLI bekerja dan tidak lagi memotong item sebelum parsing.

## 7. Keterbatasan yang Masih Ada

- Belum ada feed aktif yang terbukti mendukung pagination. Mongabay `?paged=2` mengembalikan item yang sama, ANTARA `?page=2` juga mengembalikan item yang sama, sedangkan BMKG/USGS/GDACS tidak menyediakan pagination pada endpoint saat ini.
- Pagination baru mendukung `query`, `template`, dan `path`; belum ada auto-discovery `rel=next`, cursor, offset, atau pagination berbasis JavaScript.
- `items_imported` berarti item yang dimasukkan ke tabel run, bukan jumlah baris yang benar-benar di-insert ke SQLite. Import database tetap ditangani oleh `import_run_dir`.
- Feed BMKG/USGS/GDACS adalah jendela data terbatas, bukan arsip historis.
- Delay hanya berlaku untuk request live; replay offline tidak memakai delay.
- Lisensi dan redistribusi sumber masih belum diverifikasi.
- Error `test_scraper.py` masih menjadi kegagalan full suite yang sudah ada sebelumnya.
- Pengujian pagination dilakukan dengan fixture sintetis karena belum ada sumber aktif yang bisa diuji secara nyata.

## 8. Cara Menjalankan Pipeline dengan Opsi `--max-items` dan `--source-max-items`

### Tanpa limit

Mengambil seluruh item yang tersedia dari setiap feed aktif:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py
```

### Limit global

Membatasi fallback maksimum item per sumber:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py --max-items 50
```

### Limit per sumber

Dapat diulang untuk beberapa sumber:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py `
  --source-max-items mongabay_indonesia=50 `
  --source-max-items antaranews_warta_bumi=30
```

Prioritas limit:

1. `--source-max-items`
2. `max_items` pada feed di `feeds.py`
3. `--max-items`
4. tanpa limit

### Offline replay dengan limit per sumber

```powershell
.\.venv\Scripts\python.exe run_pipeline.py `
  --offline `
  --raw-dir data\pipeline\RUN-20261103T160737Z\raw `
  --output-root data\pipeline `
  --source-max-items mongabay_indonesia=20 `
  --delay 0
```

### Live fetch dengan delay dan timeout

```powershell
.\.venv\Scripts\python.exe run_pipeline.py `
  --max-items 100 `
  --delay 1.5 `
  --timeout 30
```

### Opsional: impor hasil run ke SQLite

Default pipeline tidak mengimpor ke database. Gunakan `--database` jika ingin mengimpor hasil run:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py `
  --offline `
  --raw-dir data\pipeline\RUN-20261103T160737Z\raw `
  --database database\geohazard.db
```

### Menjalankan tes

```powershell
.\.venv\Scripts\python.exe -m unittest test_pipeline_item_selection.py -v
.\.venv\Scripts\python.exe -m unittest test_pipeline_stage12.py test_pipeline_item_selection.py -v
```
