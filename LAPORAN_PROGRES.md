# Laporan Progres - GeoHazard-News-Locator

Tanggal laporan: **2026-11-04**
Status terakhir: **pipeline terpadu tahap 1 berjalan; rangkaian FIX 02-05 selesai; sisa isu geographic scope dan materialisasi dokumen**

## 1. Ringkasan

- Pipeline terpadu (`geohazard_pipeline`) sudah menghasilkan run terakhir `RUN-20261103T160737Z` dan diimpor ke SQLite.
- Seluruh 7 sumber aktif merespons HTTP 200.
- Dataset baseline final tetap 787 baris dan 51 kolom (SHA-256 `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06`).
- Rangkaian perbaikan pilot FIX 02 sampai FIX 05 selesai tanpa mengubah event, kategori, baseline, atau raw payload.
- 11 event masih `tidak_diketahui` karena belum ada polygon batas wilayah Indonesia yang sah.
- 3 record `bmkg_gempa_dirasakan` sudah terkonfirmasi terkait event yang ada, tetapi belum dimaterialisasi menjadi `document` dan link pendukung.

## 2. Pipeline terpadu (Stage 1)

Run terakhir: `data/pipeline/RUN-20261103T160737Z`

| Item | Nilai |
|---|---:|
| Mulai | 2026-11-03T16:07:37Z |
| Selesai | 2026-11-03T16:07:53Z |
| Sumber aktif | 7 |
| `event` | 30 |
| `document` | 75 |
| `document_classification` | 75 |
| `document_event_link` | 35 |
| `event_assertion` | 241 |
| `event_attribute` | 107 |
| `event_location` | 30 |
| `event_time` | 30 |
| `category` | 30 |
| `event_relation` | 0 |
| `location_mention` | 35 |
| `raw_payload` | 7 |
| `source` | 7 |
| `verification` | 30 |
| `change_log` | 732 |
| `document_duplicate` | 0 |
| `import_log` | 0 |

Status sumber:

| Sumber | HTTP | Parsed | Selected |
|---|---:|---:|---:|
| `antaranews_warta_bumi` | 200 | 20 | 20 |
| `mongabay_indonesia` | 200 | 20 | 20 |
| `bmkg_autogempa` | 200 | 1 | 1 |
| `bmkg_gempa_terkini` | 200 | 15 | 15 |
| `bmkg_gempa_dirasakan` | 200 | 15 | 15 |
| `gdacs_all` | 200 | 4 | 4 |
| `usgs_m45` | 200 | 0 | 0 |

Catatan: `usgs_m45` merespons 200 tetapi tidak mengembalikan item pada run ini.

Database: `database/geohazard.db` (SQLite, 1.982.464 byte, diimpor 2026-11-03 23:08).

## 3. Rangkaian perbaikan data pilot

### FIX 02 - Relasi kandidat duplikat BMKG-USGS
- Fix ID: `FIX-EVENT-RELATION-20261103T053822Z`
- Relasi sebelum/sesudah: 0 / 2
- Event sebelum/sesudah: 20 / 20
- Tidak ada merge, hapus event, atau perubahan baseline.
- Relasi bersifat kandidat, bukan klaim `same_event`.

### FIX 03 - Koreksi geographic scope
- Fix ID: `FIX-GEOGRAPHIC-SCOPE-20261103T055509Z`
- Geographic scope dipisahkan dari category scope.
- Hasil: `ya=9`, `tidak=0`, `tidak_diketahui=11`.
- Koreksi menghentikan penggunaan bbox pilot sebagai batas nasional.

### FIX 04 - Review manual geographic scope
- Fix ID: `FIX-GEOGRAPHIC-REVIEW-20261103T061354Z`
- 11 event direview memakai bukti raw BMKG/USGS.
- Keputusan: semua tetap `tidak_diketahui`.
- Perubahan status: 0; `change_log` tetap 386.
- Dua relasi FIX 02 tetap utuh.

### FIX 05 - Audit document event link
- Status: audit read-only, belum ada perubahan data atau kode.
- 3 record `bmkg_gempa_dirasakan` terkonfirmasi terkait event yang sudah ada:
  - Oksibil -> `EVT-BMKG-72D9473D8378`
  - Tanimbar/FFB -> `EVT-BMKG-FFB357F335AE`
  - Gunungkidul -> `EVT-BMKG-608A37F640B2`
- Ketiganya belum punya baris `document`, sehingga belum bisa dihubungkan.
- Rekomendasi: materialisasi dokumen pendukung dan link `supporting` pada fix terpisah.

## 4. Tahap kualitas data (Stage 5.x)

- Baseline final: 787 baris, 51 kolom.
- Stage 5.4 (ekstraksi event time): 787 -> 787 baris, 36 -> 39 kolom.
- `event_time` terisi 64 baris:
  - 51 baris tanggal + jam
  - 13 baris tanggal saja
- `perlu_review`: 14 baris; `tidak_tersedia`: 709 baris.
- Proses non-destruktif; kategori, lokasi, dan data historis tidak diubah.

## 5. Pengujian

- Test terarah FIX 02-05 dan baseline lulus (mis. 48 test OK).
- Full suite: 122 test dijalankan, 121 lulus, 1 error lama:
  - `ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'`
- Error tersebut tidak terkait FIX 02-05.

## 6. Artefak utama

- `reports/FIX_02_EVENT_RELATION.md`
- `reports/FIX_03_GEOGRAPHIC_SCOPE.md`
- `reports/FIX_04_GEOGRAPHIC_REVIEW.md`
- `reports/FIX_05_DOCUMENT_EVENT_LINK_AUDIT.md`
- `reports/ekstraksi_event_time_stage5_4.md`
- `data/pipeline/RUN-20261103T160737Z/`
- `database/geohazard.db`
- `database/schema.sql`

## 7. Batasan dan kendala

- Repository belum memiliki polygon batas wilayah Indonesia yang berlisensi dan dapat dipertanggungjawabkan.
- Bbox pilot bukan batas nasional dan tidak dipakai untuk memaksa status.
- Feed BMKG/USGS/GDACS adalah jendela terbatas, bukan arsip.
- Kategori berita adalah klasifikasi dokumen, bukan bukti kejadian.
- Lisensi/redistribusi sumber belum diverifikasi.
- `robots` BMKG tidak terbaca; pipeline memakai laju rendah tanpa mengklaim izin.
- Event dari baseline diimpor sebagai kandidat, bukan fakta terverifikasi.

## 8. Langkah berikutnya

1. Materialisasi 3 dokumen `bmkg_gempa_dirasakan` (Oksibil, Tanimbar/FFB, Gunungkidul) dan tambahkan link `supporting`.
2. Perbaiki aturan pemilihan record agar tidak hanya memakai `parsed_items[:10]`.
3. Tambahkan polygon batas wilayah Indonesia sebelum menaikkan status 11 event `tidak_diketahui`.
4. Perbaiki error lama `test_scraper` (`get_soup`).
5. Tambahkan test regresi untuk materialisasi dokumen dan integritas link.
