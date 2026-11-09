# Laporan Pilot Pengumpulan Data Geohazard Resmi

Status: **pilot internal, bukan rilis publik**  
Run: `PILOT-20261102T110641Z`  
Sumber acuan: `data/pilot/runs/PILOT-20261102T110641Z/manifest.json`  
Baseline: `data/geohazard_news_final_20261101T150501Z.csv`

## 1. Tujuan dan batas

Pilot ini menguji jalur pengumpulan satu kali dari feed kejadian resmi yang aktif, menyimpannya sebagai snapshot mentah, menormalisasi record ke skema provenance, dan menjalankan validasi. Pilot **tidak** mengubah dataset baseline, tidak menggabungkan duplikat lintas sumber, dan tidak mengklaim cakupan delapan kategori.

Batas operasional:

- Maksimal 10 record per sumber.
- Satu GET per endpoint dengan jeda 1,2 detik dan timeout 30 detik.
- TLS tetap diverifikasi; tidak ada `verify=False`.
- Koordinat berstatus `source_coordinate`, bukan `verified`.
- Lisensi/izin redistribusi belum diverifikasi.
- Feed BMKG adalah jendela berjalan, bukan arsip historis.
- USGS adalah sumber resmi ilmiah internasional pendukung, bukan sumber resmi Indonesia.

## 2. Sumber yang dijalankan

| source_id | HTTP | Record tersedia | Dipilih | Dokumen | Event primer | Catatan |
|---|---:|---:|---:|---:|---:|---|
| `bmkg_autogempa` | 200 | 1 | 1 | 1 | 1 | Hanya gempa terbaru |
| `bmkg_gempa_terkini` | 200 | 15 | 10 | 10 | 10 | Dibatasi 10 |
| `bmkg_gempa_dirasakan` | 200 | 15 | 10 | 10 | 7 | Dibatasi 10; sebagian bergabung dengan record BMKG lain |
| `usgs_m45` | 200 | 22 | 2 | 2 | 2 | 20 entry di luar bbox Indonesia |

Semua sumber berstatus register `TERVERIFIKASI_AKTIF`. Status lisensi adalah `unverified`; robots BMKG `unreadable`; robots USGS `not_found`.

## 3. Hasil normalisasi

| Entitas | Jumlah |
|---|---:|
| `source` | 4 |
| `raw_payload` | 4 |
| `document` | 23 |
| `event` | 20 |
| `event_time` | 20 |
| `event_location` | 20 |
| `location_mention` | 20 |
| `category` | 20 |
| `document_event_link` | 23 |
| `event_assertion` | 140 |
| `event_attribute` | 59 |
| `verification` | 20 |
| `event_relation` | 0 |
| `change_log` | 373 |

Jumlah 20 event bukan jumlah kejadian fisik unik. Dua pasangan BMKG–USGS berdekatan waktu dan lokasi tetap dipisah sampai review manual. Rentang waktu record yang masuk adalah `2026-10-21T07:44:15+00:00` sampai `2026-11-02T09:58:58+00:00`.

Raw payload tersimpan per run:

| Sumber | Ukuran | SHA-256 (awal) |
|---|---:|---|
| `bmkg_autogempa` | 535 byte | `da8739ad4964027e...` |
| `bmkg_gempa_terkini` | 5.520 byte | `e5665e90cf097640...` |
| `bmkg_gempa_dirasakan` | 6.201 byte | `9b1bc264382d54c9...` |
| `usgs_m45` | 17.842 byte | `fbb7638a2198b07a...` |

## 4. Kandidat duplikat

| BMKG | USGS | Selisih waktu | Jarak | Tindakan |
|---|---|---:|---:|---|
| Tomohon M5.3 | `us7000tuuy` M5.1 | 4 detik | 22,2 km | Review manual; tidak digabung |
| Tanimbar M5.5 | `us7000tusv` M5.1 | 1 detik | 22,0 km | Review manual; tidak digabung |

Kandidat ini menunjukkan bahwa waktu dan lokasi berdekatan, tetapi magnitudo/kedalaman dapat berbeda. Penggabungan otomatis tidak dilakukan agar bukti dan parameter masing-masing sumber tidak hilang.

## 5. Cakupan kategori

| Kategori | Status pilot | Event |
|---|---|---:|
| Gempabumi | Tercakup | 20 |
| Tsunami | Hanya atribut potensi BMKG | 0 |
| Gunungapi | Tidak tercakup | 0 |
| Gerakan Tanah/Tanah Longsor | Tidak tercakup | 0 |
| Likuefaksi | Tidak tercakup | 0 |
| Abrasi dan Akresi | Tidak tercakup | 0 |
| Penurunan Muka Tanah | Tidak tercakup | 0 |
| Semburan Gas dan Lumpur | Tidak tercakup | 0 |

Pilot ini **tidak boleh** diklaim mencakup delapan kategori. Tsunami belum menjadi event mandiri karena belum ada feed kejadian tsunami resmi; field `Potensi` BMKG tetap disimpan sebagai atribut.

## 6. Keputusan provenance penting

- Waktu BMKG diambil dari field `DateTime`, bukan dari waktu pengambilan feed.
- Waktu USGS diambil dari `summary Time`; `updated` hanya disimpan sebagai `document_updated_at`.
- BMKG tidak menyediakan URL halaman stabil per record. URL dokumen memakai feed dan fragmen `#record=<external_id>`; raw payload tetap menjadi bukti utama.
- `event_id` BMKG dibentuk dari hash waktu, koordinat, dan magnitudo; `event_id` USGS memakai ID native.
- Satu event memiliki tepat satu link primer; record BMKG lain menjadi pendukung.
- Verifikasi BMKG dan USGS dicatat `official`, tetapi sumber USGS tetap ditandai sebagai internasional pendukung.
- Perubahan record dicatat append-only melalui `change_log`; tidak ada data baseline yang diubah.

## 7. Isu dan risiko

| ID | Tingkat | Isu | Dampak |
|---|---|---|---|
| `LIC-01` | P1 | Lisensi/izin redistribusi belum diverifikasi | Pilot belum layak dipublikasikan/diredistribusikan |
| `ROB-01` | P1 | robots.txt BMKG tidak terbaca | Tidak boleh menganggap robots sebagai izin |
| `GAP-01` | P1 | Hanya Gempabumi tercakup | Klaim delapan kategori tidak sah |
| `URL-01` | P2 | Tidak ada URL BMKG per record | Tautan tidak dapat dibuka per kejadian |
| `WIN-01` | P2 | Feed BMKG adalah jendela terbatas | Pilot bukan arsip historis |
| `DUP-01` | P2 | Dua kandidat duplikat BMKG–USGS | Hitungan event dapat berlebih tanpa review |

## 8. Output

Direktori run: `data/pilot/runs/PILOT-20261102T110641Z/`

- `raw/` — empat payload mentah.
- `tables/*.csv` — 14 tabel sesuai urutan entitas skema.
- `pilot_duplicate_candidates.csv`
- `pilot_source_summary.csv`
- `pilot_category_gaps.csv`
- `pilot_issues.csv`
- `pilot_validation_results.csv`
- `pilot_quality_gates.csv`
- `pilot_summary.json`
- `manifest.json` — hash dan ukuran seluruh output.

Pointer run terbaru: `data/pilot/LATEST.json`.

## 9. Kesimpulan

Jalur pilot berhasil mengambil, menyimpan, menormalisasi, dan memvalidasi 23 dokumen resmi menjadi 20 event Gempabumi dengan provenance lengkap. Baseline tidak berubah. Hasil ini cukup untuk evaluasi internal arsitektur data, tetapi **belum cukup untuk rilis publik** karena lisensi, izin, duplikasi lintas sumber, dan tujuh kategori yang belum tercakup.

Langkah berikutnya:

1. Review manual dua kandidat duplikat.
2. Selesaikan lisensi dan izin sumber.
3. Cari sumber resmi untuk tujuh kategori yang belum tercakup.
4. Rancang snapshot berkala dengan retensi yang sah.
