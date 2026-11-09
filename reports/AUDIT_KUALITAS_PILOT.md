# Audit Kualitas Pilot Pengumpulan Data Geohazard

Tanggal audit: **2026-11-02**  
Mode: **read-only, tanpa request eksternal**  
Run yang diaudit: `PILOT-20261102T110641Z`  
Status audit: **lulus teknis dengan catatan; belum layak publikasi**  
Keputusan yang direkomendasikan: **B — lanjut untuk evaluasi internal dengan perbaikan wajib**

## 1. Ringkasan eksekutif

- Pilot berhasil menyimpan 4 raw payload, 23 dokumen resmi, dan 20 event Gempabumi dengan rantai provenance yang dapat ditelusuri.
- Seluruh 21 output yang tercatat di manifest memiliki hash dan ukuran yang cocok. Empat raw payload juga cocok dengan hash di `raw_payload.csv`.
- Seluruh 14 tabel memiliki header yang sama persis dengan field dictionary. Semua field wajib terisi, seluruh primary ID unik, dan tidak ditemukan orphan atau pelanggaran foreign key.
- Angka pada `reports/PILOT_PENGUMPULAN_DATA.md` sesuai dengan kondisi aktual run.
- Baseline tidak berubah: `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06`, 787 baris × 51 kolom.
- Tidak ditemukan temuan **P0**. Ada **3 temuan P1**, **4 temuan P2**, dan **2 temuan P3**.
- Pilot layak dipakai untuk evaluasi internal, tetapi **tidak layak dipublikasikan atau diredistribusikan** sampai lisensi/izin, semantik atribut tsunami, duplikasi lintas sumber, dan keputusan scope diselesaikan.

Lima masalah utama:

1. Lisensi/izin redistribusi belum terverifikasi dan robots BMKG tidak terbaca.
2. Sepuluh event memiliki atribut bernama `tsunami_potential` dengan nilai `Tidak berpotensi tsunami`.
3. Dua pasangan BMKG–USGS kemungkinan besar merupakan event yang sama, tetapi belum direlasikan dan belum direview.
4. Satu event BMKG berada di luar bbox pilot, tetapi tetap memiliki `category_scope=in_scope`.
5. Dokumen pendukung BMKG tidak menghasilkan assertion; dua nilai `Dirasakan` pada dokumen pendukung tidak terangkat ke atribut event.

## 2. Ruang lingkup dan metode

Audit mencakup:

- integritas file, hash, ukuran, jumlah record, dan keterbacaan CSV/JSON/XML;
- kesesuaian header, field wajib, ID, foreign key, dan orphan;
- rantai provenance dari sumber sampai assertion/verification;
- kesesuaian waktu, lokasi, kategori, status verifikasi, duplikasi, dan hak penggunaan;
- pembandingan laporan pilot dengan data aktual dan baseline.

Metode:

- re-parse independen atas raw XML/Atom dan seluruh tabel CSV;
- verifikasi SHA-256 file dan output manifest;
- pemeriksaan relasional terhadap seluruh tabel;
- pemeriksaan semantik terhadap nilai atribut, judul, lokasi, dan status;
- tanpa scraper, tanpa geocoding, tanpa merge, dan tanpa perubahan dataset/kode/konfigurasi.

Batasan audit:

- Hanya satu run yang masih tersedia, sehingga append-only lintas run tidak dapat diuji.
- Kesesuaian lisensi dan hak publikasi tidak dapat dibuktikan dari file lokal.
- Identitas fisik dua kandidat duplikat tidak dapat dipastikan tanpa katalog independen.
- Delapan aturan validasi memang tidak relevan pada pilot satu-run: `R-LEG-01` sampai `R-LEG-04`, `R-REL-01` sampai `R-REL-03`, dan `R-DUP-01`.

## 3. Inventaris run, file, dan hash

Metadata run:

| Item | Nilai |
|---|---|
| Run ID | `PILOT-20261102T110641Z` |
| Schema | `1.0.0` |
| Mulai | `2026-11-02T11:06:41.602667+00:00` |
| Selesai | `2026-11-02T11:06:53.621313+00:00` |
| Script | `scripts/pilot_collect_official_geohazard.py` |
| Baseline | `data/geohazard_news_final_20261101T150501Z.csv` |
| Jumlah file dalam run | 26 |
| Manifest SHA-256 | `fc772cfc26e03d06c905aa1076a08e0ea9af66b55caf1009091f101cc12fcbd7` |
| `LATEST.json` SHA-256 | `8c132c9a1985c863675ae9847c3fe67b7ea430b0d345eeed31e7377eefbd33de` |

Seluruh 21 output manifest cocok. Ringkasan output:

| File | Baris | Byte | SHA-256 |
|---|---:|---:|---|
| `tables/source.csv` | 4 | 1.969 | `01ec96d165ef638900463d91d3f010919f63b37e710dedbed1832888ebf298cc` |
| `tables/raw_payload.csv` | 4 | 1.667 | `49c9999322e405c7c612fd2ca764d409c341a13c46209c549d3db040859b4525` |
| `tables/document.csv` | 23 | 19.914 | `e4d8121c9bb36af103f5d10e8dcb2a3b5fd61347b120bbd29e0f185badacc930` |
| `tables/event.csv` | 20 | 3.932 | `dbfa6d732e5b66bd92adc783608e844b7b4c4ec471be3d0fd13db77cb51e4eff` |
| `tables/event_time.csv` | 20 | 4.115 | `81cbe69ad498f89eb29dcbf7711876a2cced9514b45f8efa50641ac6e977d0e4` |
| `tables/location_mention.csv` | 20 | 5.356 | `df0720aac3707eb64e4ef93858d20b4ffce70d943049effeb76ca372f728052b` |
| `tables/event_location.csv` | 20 | 7.008 | `61465f8e74d47b1729c073ddacc1e82b7cca7cc5c5295aa3710f5673cfa069c3` |
| `tables/category.csv` | 20 | 4.384 | `d0675f06b96510c59eb2105112a2278ca4110e81d3e207a8cbf67faa4b06cbf1` |
| `tables/document_event_link.csv` | 23 | 5.418 | `e2320ef31cf1fad9e16ebf8e1da771f64ed3b6303dbc4e8e95fcf660073de071` |
| `tables/event_assertion.csv` | 140 | 33.817 | `d97f5009840d5ed72f931ea2eecf157015210894f91166e63183bf9312573f8d` |
| `tables/event_relation.csv` | 0 | 129 | `4db1d798d714f51df21ee48dca2395aa5a447ef03723e5e9aeea0459107942d2` |
| `tables/verification.csv` | 20 | 3.805 | `9ea6d4199f3fe8fd22306f3157c8a615ce2dc687923e975790ab6cd3808e28eb` |
| `tables/change_log.csv` | 373 | 68.715 | `b9ddf1e96a384350fb9ddff4c1dccc37cd85469986c2ac187b2ffdc6bc413c37` |
| `tables/event_attribute.csv` | 59 | 7.409 | `e21d08c42ce5498d47f04afbf56da21f8b0d0879258f1f10c4f09757e6e28c4b` |
| `pilot_duplicate_candidates.csv` | 2 | 600 | `b3d8bb90c8ca3e8708b53ecdb5c70a6c686d1b5ebbdda3a5aeb5c0e2e09f386e` |
| `pilot_source_summary.csv` | 4 | 362 | `7d65fa3be5e6b43fd11ce5528c593e97ad1ed0dfe0b3e5c0a6006557ac07f5ca` |
| `pilot_category_gaps.csv` | 8 | 1.706 | `c5bd70fc17703c68b8524c24ff30fec1db446169822cc5cf8a935c216599fbb8` |
| `pilot_issues.csv` | 6 | 1.271 | `2487966c551e4c55d16ac6e4b155881e4f7c71a55df0cf9f8e36dea65a12a202` |
| `pilot_validation_results.csv` | 59 | 4.781 | `ee52d21f47015b94a9f9182c38df3937f61893fce3a898cfc0dd4064e3c77b92` |
| `pilot_quality_gates.csv` | 11 | 1.413 | `88976290db8484e7427c977ec0dfad4f1523da1c1836e02d90853e37df2ecc1a` |
| `pilot_summary.json` | — | 2.265 | `bbff24964b4d9c671558da1a89c08930dda675904d8667641b3907eff5be83c9` |

Raw payload:

| File | Byte | SHA-256 | HTTP | Content-Type |
|---|---:|---|---:|---|
| `raw/bmkg_autogempa.xml` | 535 | `da8739ad4964027e25358ad4768505c64e6119b58c8bce10fdc6dbe4aca0a515` | 200 | `text/xml` |
| `raw/bmkg_gempa_terkini.xml` | 5.520 | `e5665e90cf097640eb5d9790536366ef6e4329c7f9dcd9c9170b44ea01673e7b` | 200 | `text/xml` |
| `raw/bmkg_gempa_dirasakan.xml` | 6.201 | `9b1bc264382d54c9b69471412159d1f96c05741598c4f39047bf430e64c2c47b` | 200 | `text/xml` |
| `raw/usgs_m45.atom` | 17.842 | `fbb7638a2198b07a9bdd1531b1b3712b4e14b662e1bc416086e3f04fb7b116f0` | 200 | `application/atom+xml; charset=utf-8` |

Seluruh raw payload dapat diparse sebagai XML/Atom. Tidak ada halaman error HTTP yang tersimpan sebagai payload.

## 4. Perbandingan laporan pilot dengan kondisi aktual

| Klaim laporan | Kondisi aktual | Status |
|---|---|---|
| 4 sumber | 4 sumber | Sesuai |
| 23 dokumen | 23 dokumen | Sesuai |
| 20 event | 20 event | Sesuai |
| 140 assertion | 140 assertion | Sesuai |
| 59 atribut | 59 atribut | Sesuai |
| 373 change log | 373 change log | Sesuai |
| `event_relation` 0 | Header-only, 0 record | Sesuai |
| Raw size/hash | Cocok seluruhnya | Sesuai |
| Rentang waktu `2026-10-21T07:44:15+00:00` sampai `2026-11-02T09:58:58+00:00` | Cocok | Sesuai |
| Dua kandidat duplikat: 4 detik/22,2 km dan 1 detik/22,0 km | Cocok | Sesuai |
| USGS 22 entry, 20 di luar bbox, 2 dipilih | Cocok | Sesuai |
| Baseline tidak berubah | Hash sama | Sesuai |
| Gate G1 lulus dengan catatan | Cocok | Sesuai |

Tidak ada angka pada laporan pilot yang bertentangan dengan data aktual.

Catatan dokumentasi: `docs/MASTER_SOURCE_REGISTER.csv` mencatat 21 entry USGS pada saat audit register, sedangkan raw pilot berisi 22 entry. Ini adalah snapshot feed yang berubah, bukan discrepancy data pilot; laporan pilot sudah memakai angka aktual 22.

## 5. Integritas baseline

| Item | Nilai |
|---|---|
| Path | `data/geohazard_news_final_20261101T150501Z.csv` |
| SHA-256 | `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06` |
| Ukuran | 625.249 byte |
| Baris data | 787 |
| Kolom | 51 |

Hasil: **LULUS**. Baseline tidak berubah, tidak ada baris baseline yang dimasukkan ke run pilot, dan tes `python -m unittest -v test_dataset_baseline` lulus 3/3.

## 6. Skema dan integritas tabel

- 14 tabel tersedia dan dapat diparse.
- 14 header cocok persis dengan `docs/PROVENANCE_FIELD_DICTIONARY.csv`.
- Seluruh field berstatus `wajib` terisi pada seluruh baris.
- Seluruh primary ID unik; tidak ada duplikasi ID pada 4 source, 4 raw payload, 23 dokumen, 20 event, 140 assertion, dan 373 change log.
- `change_log` berisi 373 operasi `create` dan tidak memiliki `create` ganda untuk target yang sama.
- Jumlah `create` sama dengan total record: 4 source + 4 raw + 23 dokumen + 20 event + 20 waktu + 20 lokasi + 20 mention + 20 kategori + 23 link + 140 assertion + 20 verification + 59 atribut = 373.
- `event_relation.csv` hanya memiliki header dan 0 record. Ini sesuai desain pilot yang tidak membuat relasi antar-event.

Hasil: **LULUS**.

## 7. Relasi, foreign key, dan provenance

Pemeriksaan orphan/foreign key:

| Relasi | Orphan |
|---|---:|
| `raw_payload.source` | 0 |
| `document.source` | 0 |
| `document.raw_payload` | 0 |
| `document_event_link.document` | 0 |
| `document_event_link.event` | 0 |
| `event_time.event` | 0 |
| `event_location.event` | 0 |
| `location_mention.event` | 0 |
| `location_mention.document` | 0 |
| `category.event` | 0 |
| `event_assertion.event` | 0 |
| `event_assertion.document` | 0 |
| `event_assertion.source` | 0 |
| `event_attribute.event` | 0 |
| `event_attribute.source` | 0 |
| `verification.event` | 0 |
| `event.primary_source` | 0 |

Pemeriksaan kelengkapan:

- Setiap event memiliki tepat 1 `event_time`, 1 `event_location`, 1 `location_mention`, 1 kategori primer, 1 verification, dan 1 link primer.
- Setiap event memiliki 7 assertion: waktu, latitude, longitude, nama lokasi, kategori, magnitudo, dan kedalaman.
- Seluruh 23 dokumen terhubung sedikitnya ke satu event.
- Seluruh 140 assertion dan 59 atribut memiliki sumber yang terdaftar.
- Rantai BMKG dapat ditelusuri dari `source → raw_payload → document → document_event_link → event → event_assertion/event_attribute → verification`.
- Rantai USGS dapat ditelusuri dengan pola yang sama dan memakai ID native `us7000tuuy` serta `us7000tusv`.

Hasil: **LULUS**, dengan catatan bahwa assertion dan atribut hanya berasal dari dokumen primer; lihat temuan `AUD-06`.

## 8. Waktu

- Seluruh 20 event memakai `event_time_precision=second`, `event_time_kind=actual`, `event_time_status=extracted`, `event_time_basis=official_field`, `event_time_timezone=Etc/UTC`, dan `event_time_confidence=high`.
- Waktu BMKG berasal dari field `DateTime`, bukan waktu pengambilan feed. Contoh: `DateTime=2026-11-02T08:13:10+00:00` dengan `Jam=15:13:10 WIB`.
- Waktu USGS berasal dari `summary Time`, bukan `updated`. Contoh `EVT-USGS-7000tuuy`: event time `2026-11-02T08:13:14+00:00`, `document_updated_at=2026-11-02T08:27:49.040000+00:00`.
- `document_published_at` kosong pada seluruh 23 dokumen, sehingga tidak ada waktu publikasi yang disalahgunakan sebagai waktu kejadian.
- `document_updated_at` hanya terisi pada 2 dokumen USGS; 21 dokumen BMKG tidak memiliki nilai dan tidak diisi dengan event time.
- Tidak ada `event_time_candidate_text`, `event_time_start`, `event_time_end`, atau `event_time_review_reason` yang terisi; tidak ada konflik waktu yang perlu review.
- Rentang waktu event aktual: `2026-10-21T07:44:15+00:00` sampai `2026-11-02T09:58:58+00:00`.

Hasil: **LULUS**. Tidak ada bukti publikasi atau pembaruan dokumen dipakai sebagai waktu kejadian.

## 9. Lokasi

- Seluruh 20 event memiliki `event_location` dan `location_mention`.
- Seluruh koordinat berstatus `source_coordinate`, `coordinate_precision=point`, dan `coordinate_confidence=high`; tidak ada klaim `verified`.
- Field admin (`province`, `kabupaten_kota`, `kecamatan`, `desa_kelurahan`) kosong pada seluruh 20 event. Ini sesuai batas pilot yang tidak melakukan geocoding, bukan kegagalan validasi.
- 19 event memiliki `is_inside_indonesia=ya`; 1 event memiliki `tidak`.
- Event di luar bbox: `EVT-BMKG-72D9473D8378`, `bmkg_gempa_terkini`, koordinat `-5.4500, 141.9000`, judul `Gempa M6 - 153 km Tenggara OKSIBIL-PAPUAPGNGN`.
- Bbox pilot adalah `[-11, 6, 95, 141]`; koordinat tersebut berada di luar bbox. Status `tidak` hanya berarti di luar bbox pilot, bukan kesimpulan hukum bahwa lokasi berada di luar Indonesia.
- Nilai `mention_normalized` saat ini identik dengan `mention_text`; belum ada normalisasi gazetteer. Ini tidak mengubah koordinat dan tidak boleh dibaca sebagai verifikasi lokasi.

Hasil: **LULUS DENGAN CATATAN**. Tidak ada koordinat yang bertentangan dengan raw, tetapi event di luar bbox tetap berstatus `category_scope=in_scope`; lihat `AUD-05`.

## 10. Kategori dan cakupan

- Seluruh 20 event memiliki satu kategori primer `Gempabumi`.
- Tidak ada event Tsunami mandiri; atribut potensi BMKG tidak diubah menjadi event terpisah.
- Tujuh kategori lain tidak tercakup: Gunungapi, Gerakan Tanah/Tanah Longsor, Likuefaksi, Abrasi dan Akresi, Penurunan Muka Tanah, Semburan Gas dan Lumpur, serta Tsunami sebagai event mandiri.
- Pilot tidak boleh diklaim mencakup delapan kategori. Ini adalah batasan cakupan yang sudah dinyatakan dengan benar di laporan pilot.

Atribut potensi BMKG:

- 10 event memiliki `tsunami_potential` dengan nilai `Tidak berpotensi tsunami`.
- 1 event memiliki `bmkg_potential_note` dengan nilai `Gempa ini dirasakan untuk diteruskan pada masyarakat`.
- Nama atribut `tsunami_potential` untuk nilai negasi berisiko dibaca sebagai flag potensi tsunami positif. Ini adalah temuan semantik `AUD-02`.

Hasil: **LULUS UNTUK KATEGORI GEMPABUMI; PERINGATAN UNTUK SEMANTIK ATRIBUT TSUNAMI DAN KLAIM CAKUPAN**.

## 11. Duplikasi dan identitas event

Dua kandidat duplikat:

| BMKG | USGS | Waktu | Magnitudo | Kedalaman | Jarak | Selisih waktu |
|---|---|---|---|---:|---:|---:|
| `EVT-BMKG-5989CC896238` Tomohon | `EVT-USGS-7000tuuy` | 08:13:10 vs 08:13:14 | 5.3 vs 5.1 | 148 vs 196,65 km | 22,2 km | 4 detik |
| `EVT-BMKG-8102A3842AA3` Tanimbar | `EVT-USGS-7000tusv` | 00:53:11 vs 00:53:10 | 5.5 vs 5.1 | 130 vs 93,55 km | 22,0 km | 1 detik |

Penilaian:

- Bukti lokal mendukung **kemungkinan besar event yang sama**, terutama karena selisih waktu 1–4 detik dan jarak sekitar 22 km.
- Perbedaan magnitudo 0,2–0,4 dan kedalaman 36–49 km menunjukkan perbedaan solusi sumber, bukan bukti bahwa event berbeda.
- Identitas fisik belum dapat dipastikan tanpa katalog independen atau review manual.
- Pilot benar tidak menggabungkan otomatis dan mempertahankan identitas masing-masing sumber.
- Namun relasi kandidat hanya dicatat di `pilot_duplicate_candidates.csv`; `event_relation.csv` kosong dan `event_group_id` kosong pada seluruh 20 event. Konsumen tabel normalisasi tidak melihat relasi kandidat tersebut.
- Dengan demikian, 20 event adalah **20 event record**, bukan 20 kejadian fisik unik. Jika kedua pasangan sama, jumlah kejadian fisik dapat turun menjadi 18.

Hasil: **LULUS UNTUK LARANGAN MERGE OTOMATIS; PERINGATAN UNTUK RELASI YANG BELUM DIPERSISTENSIKAN**.

## 12. Status verifikasi

- Seluruh 20 event memiliki `event_status=confirmed`, `event_verification_status=official`, dan `event_verification_level=official`.
- Seluruh verification memakai `verification_method=official_record`, `verification_source_count=1`, dan `manual_review=tidak`.
- `verified_at` dan `verified_by` kosong karena belum ada verifikasi manual; field ini opsional.
- Status `confirmed` sah menurut schema karena berasal dari rekaman resmi, bukan dari berita.
- Namun `official` tidak sama dengan `corroborated`: tidak ada event yang memiliki dua sumber independen yang direlasikan. Dua pasangan BMKG–USGS yang mungkin saling menguatkan belum direlasikan.
- Kategori juga berstatus `category_review_status=not_reviewed` pada seluruh event.

Hasil: **LULUS DENGAN CATATAN**. Jangan menuliskan bahwa event telah “dikonfirmasi independen” atau “dikorroborasi”; gunakan “rekaman resmi” atau “official record”.

## 13. Hak penggunaan dan kelayakan publikasi

- Seluruh 4 sumber memiliki `source_license_status=unverified`, `source_license=belum_diverifikasi`, dan `source_terms_url` kosong.
- HTTP 200 bukan izin redistribusi. Robots BMKG berstatus `unreadable`; robots USGS `not_found`. Keduanya tidak boleh dianggap sebagai izin.
- Tidak ada bukti lisensi, persetujuan atribusi, atau izin publikasi di repository.
- Pilot aman digunakan sebagai bahan evaluasi internal yang terbatas, tetapi belum layak dipublikasikan, diredistribusikan, atau dijadikan produk publik.
- Selain hak penggunaan, publikasi juga terhalang oleh duplikasi lintas sumber, event di luar bbox, cakupan satu kategori, dan belum adanya review editorial/G10.

Hasil: **BELUM TERVERIFIKASI / TIDAK LAYAK PUBLIKASI**.

## 14. Temuan, keputusan, dan rekomendasi

### 14.1 Daftar temuan

| ID | Prioritas | Jenis | Temuan | Bukti | Dampak | Status |
|---|---|---|---|---|---|---|
| `AUD-01` | P1 | Belum terverifikasi | Lisensi/izin seluruh sumber belum ada; robots BMKG tidak terbaca | 4/4 `unverified`; terms kosong; robots `unreadable`/`not_found` | Tidak boleh publikasi/redistribusi | BELUM TERVERIFIKASI |
| `AUD-02` | P1 | Temuan data | `tsunami_potential` dipakai untuk nilai negasi; nama field menyesatkan | 10 event bernilai `Tidak berpotensi tsunami`; 1 event memakai `bmkg_potential_note` | Risiko false positive tsunami | PERINGATAN |
| `AUD-03` | P1 | Batasan cakupan | Hanya Gempabumi yang tercakup; tujuh kategori lain belum | 20/20 kategori Gempabumi; 7 kategori 0 event | Klaim delapan kategori tidak sah | PERINGATAN |
| `AUD-04` | P2 | Risiko | Dua kandidat duplikat belum direlasikan atau direview | 2 pasangan; `event_relation` 0; `event_group_id` kosong | Hitungan event fisik dapat berlebih | PERINGATAN |
| `AUD-05` | P2 | Temuan data | Event di luar bbox tetap `category_scope=in_scope` | `EVT-BMKG-72D9473D8378`, `-5.45, 141.90`, `is_inside_indonesia=tidak` | Scope dataset tidak konsisten | PERINGATAN |
| `AUD-06` | P2 | Temuan data | Dokumen pendukung tidak menghasilkan assertion; dua laporan `Dirasakan` tidak terangkat | 3 link non-primer, 0 assertion; Tomohon `II - III Ternate, II Minahasa`, Tanimbar `II Saumlaki` | Informasi pendukung hilang dari tabel event | PERINGATAN |
| `AUD-07` | P2 | Risiko | URL BMKG bukan URL stabil per record | 21 dokumen memakai `feed#record=...`; tidak ada halaman record | Tautan tidak dapat dibuka per kejadian | PERINGATAN |
| `AUD-08` | P3 | Temuan data | Dua judul BMKG menormalkan magnitudo `6.0`/`5.0` menjadi `M6`/`M5` | `DOC-b5e6c0cf56585a3d`, `DOC-1e6e76a86b5afd87` | Fidelitas tampilan sedikit berkurang; atribut magnitudo tetap benar | PERINGATAN |
| `AUD-09` | P3 | Belum terverifikasi | Append-only lintas run belum diuji | Hanya satu run tersisa; `change_log` konsisten dalam run | Jaminan append-only belum terbukti | BELUM TERVERIFIKASI |

Tidak ada temuan **P0**.

### 14.2 Keputusan A–D

- **A — Terima untuk publikasi:** tidak dipilih. Hak penggunaan belum terverifikasi, duplikasi belum selesai, dan cakupan baru satu kategori.
- **B — Lanjut untuk evaluasi internal dengan perbaikan wajib:** **dipilih**. Integritas teknis, provenance, baseline, dan relasi dasar lulus.
- **C — Tunda seluruh penggunaan:** tidak diperlukan. Tidak ada P0, data dapat diparse, dan baseline aman.
- **D — Tolak/rollback:** tidak diperlukan. Baseline tidak berubah dan tidak ada kerusakan data.

### 14.3 Rekomendasi berurutan

1. Perbaiki `AUD-02`: ganti `tsunami_potential` menjadi field teks netral, misalnya `bmkg_potential_text`, atau tambahkan boolean eksplisit `tsunami_potential=false`. Jangan memakai nama field saat ini sebagai flag positif.
2. Selesaikan `AUD-01` sebelum publikasi: catat dasar lisensi/izin tiap sumber, termasuk terms dan atribusi. Jangan menganggap HTTP 200 atau robots `not_found` sebagai izin.
3. Review manual dua kandidat duplikat. Simpan keputusan di `event_relation`/`event_group_id` tanpa menggabungkan identitas event atau menghapus parameter sumber.
4. Tetapkan keputusan scope untuk `EVT-BMKG-72D9473D8378`: pertahankan dengan status di luar bbox dan scope yang sesuai, atau keluarkan dari dataset Indonesia setelah review. Jangan biarkan `in_scope` tanpa alasan.
5. Petakan dokumen pendukung ke assertion/atribut, khususnya `Dirasakan` dari feed `gempa_dirasakan`, atau dokumentasikan secara eksplisit bahwa hanya dokumen primer yang dinormalisasi.
6. Pertahankan raw payload dan fragment URL BMKG sebagai bukti; tambahkan URL stabil bila sumber menyediakannya.
7. Normalisasi tampilan magnitudo pada judul atau dokumentasikan aturan `M6`/`M5` sebagai display normalization.
8. Uji append-only dengan snapshot kedua sebelum mengklaim perilaku lintas run.
9. Jalankan G10, review editorial, dan review legal setelah P1 selesai. Jangan publikasikan pilot ini.

### 14.4 Kesimpulan

Pilot **lulus audit teknis untuk penggunaan internal**: file lengkap, hash cocok, header dan field wajib sesuai, relasi dasar bersih, provenance dapat ditelusuri, waktu tidak dicampur dengan waktu publikasi, baseline aman, dan laporan pilot sesuai data aktual.

Pilot **belum layak publikasi**: hak penggunaan belum terverifikasi, atribut tsunami berisiko menyesatkan, dua duplikat belum diselesaikan, ada event di luar bbox yang masih `in_scope`, dan hanya satu kategori yang tercakup. Keputusan yang tepat adalah **B**, dengan perbaikan P1 sebagai prasyarat sebelum data dipakai di luar evaluasi internal.
