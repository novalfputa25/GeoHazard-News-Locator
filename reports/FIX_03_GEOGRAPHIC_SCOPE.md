# FIX 03 - Koreksi Geographic Scope dan Pemisahan dari Category Scope

Tanggal: **2026-11-03**  
Fix ID: `FIX-GEOGRAPHIC-SCOPE-20261103T055509Z`  
Sumber: `data/pilot/fixes/FIX-EVENT-RELATION-20261103T053822Z`  
Output: `data/pilot/fixes/FIX-GEOGRAPHIC-SCOPE-20261103T055509Z`  
Status: **geographic scope dikoreksi; event, kategori, relasi, baseline, dan raw payload dipertahankan**

## 1. Tujuan dan batas

FIX 03 memisahkan **geographic scope** dari **category scope**. Geographic scope menjawab apakah lokasi kejadian berada di Indonesia, di luar Indonesia, atau belum dapat ditentukan. Category scope tetap menjawab apakah kategori kejadian termasuk cakupan kategori proyek.

Batas yang dipertahankan:

- Tidak menghapus, menggabungkan, atau mengganti `event_id`.
- Tidak mengubah `event`, `category`, `event_relation`, `raw_payload`, atau baseline.
- Tidak mengubah output FIX 01 dan FIX 02 sebagai sumber.
- Tidak menaikkan `coordinate_status=source_coordinate` menjadi `verified`.
- Tidak memakai judul berita/feed sebagai bukti tunggal lokasi.
- Tidak memaksa titik di luar bbox pilot atau di laut menjadi Indonesia/luar Indonesia tanpa bukti batas wilayah.
- Tidak mengubah schema; field dan vocabulary yang dipakai sudah tersedia.

## 2. Akar masalah

Sebelum FIX 03, `scripts/pilot_collect_official_geohazard.py` mengisi `event_location.is_inside_indonesia` langsung dari bounding box:

```text
ya    jika koordinat di dalam INDONESIA_BBOX (-11.0, 6.0, 95.0, 141.0)
tidak jika koordinat di luar bbox
```

Bbox tersebut adalah **bbox pilot**, bukan batas wilayah nasional Indonesia. Akibatnya:

- 19 event ditandai `ya` hanya karena koordinat masuk bbox, termasuk event laut dan event berjarak jauh.
- Event Oksibil `EVT-BMKG-72D9473D8378` di luar bbox ditandai `tidak`, padahal tidak ada polygon batas Indonesia yang dapat membuktikan status luar Indonesia.
- `category_scope` diisi `in_scope` secara terpisah, sehingga tampak seolah lokasi di luar Indonesia tetap "in scope" tanpa penjelasan geographic scope.

Temuan ini sesuai audit `reports/AUDIT_KUALITAS_PILOT.md` baris 24 dan 119.

## 3. Aturan geographic scope

Field yang dipakai: `event_location.is_inside_indonesia`. Vocabulary yang sudah ada di `docs/PROVENANCE_FIELD_DICTIONARY.csv`:

| Nilai | Makna |
|---|---|
| `ya` | Lokasi kejadian dapat diterima sebagai Indonesia |
| `tidak` | Lokasi kejadian dapat diterima sebagai luar Indonesia |
| `tidak_diketahui` | Lokasi belum dapat ditetapkan; masuk review manual |

Aturan yang diterapkan pada classifier `geographic_scope.py`:

| Kondisi | Hasil |
|---|---|
| Tidak ada koordinat valid | `tidak_diketahui` |
| Koordinat di luar bbox pilot, tanpa penanda negara asing yang jelas | `tidak_diketahui` |
| Koordinat di luar bbox pilot + penanda wilayah asing yang jelas + tanpa toponimi Indonesia | `tidak` |
| Titik di laut/perairan tanpa batas nasional | `tidak_diketahui` |
| Toponimi Indonesia + penanda `di darat` + koordinat dalam bbox pilot | `ya` |
| Toponimi Indonesia + jarak dekat (<= 50 km) + koordinat dalam bbox pilot | `ya` |
| Toponimi Indonesia tetapi jarak jauh, tanpa penanda darat | `tidak_diketahui` |
| Tanpa toponimi Indonesia yang cukup | `tidak_diketahui` |

Catatan penting:

- Bbox pilot hanya dipakai sebagai sanity check, bukan bukti tunggal.
- `event_title` tidak dipakai sebagai bukti lokasi. Judul yang menyebut "Indonesia" tidak otomatis membuat event menjadi Indonesia.
- Bukti toponimi berasal dari `location_name`, `wilayah_reference.py`, dan `data/wilayah_gazetteer.json`.
- Titik Oksibil, laut, perbatasan, dan jarak jauh tanpa batas resmi ditandai `tidak_diketahui`.
- Kategori dan `category_scope` tidak diubah. `category_scope=in_scope` tetap berarti kategori Gempabumi termasuk kategori proyek, bukan klaim lokasi di Indonesia.

## 4. Perubahan kode

| File | Perubahan |
|---|---|
| `geographic_scope.py` | Modul baru berisi classifier geographic scope dan dokumentasi batas bukti. |
| `scripts/fix_geographic_scope.py` | Script FIX 03: membaca FIX 02, mengoreksi hanya field scope pada baris yang berubah, menambah `change_log`, dan menulis manifest/evidence/validation. |
| `scripts/pilot_collect_official_geohazard.py` | `build_event_group()` memakai classifier, bukan bbox. `R-LOC-05` memvalidasi flag terhadap classifier, bukan `is_inside_bbox()`. |
| `test_geographic_scope.py` | 18 test untuk klasifikasi dan invariant output FIX 03. |
| `reports/FIX_03_GEOGRAPHIC_SCOPE.md` | Laporan ini. |

Tidak ada field baru. Tidak ada perubahan schema. `category_scope` tetap memakai nilai lama.

## 5. Output dan metrik

| Item | Nilai |
|---|---|
| FIX 02 sumber | `data/pilot/fixes/FIX-EVENT-RELATION-20261103T053822Z` |
| SHA-256 manifest FIX 02 | `c0bdeefa482d44154fdb25775ba61e7534cc73c1e1133be89a55f20dae6dcdc0` |
| SHA-256 manifest FIX 01 | `aaa5b2ab6c3a02f33574f256aa3f52721be323b52b65668a872dfcdc341eb6a2` |
| Event sebelum/sesudah | 20 / 20 |
| Relasi sebelum/sesudah | 2 / 2 |
| `change_log` sebelum/sesudah | 375 / 386 |
| Scope sebelum | `ya=19`, `tidak=1`, `tidak_diketahui=0` |
| Scope sesudah | `ya=9`, `tidak=0`, `tidak_diketahui=11` |
| Perubahan scope | 11 event |

File utama output:

- `tables/event_location.csv`
- `tables/change_log.csv`
- `geographic_scope_summary.csv`
- `geographic_scope_evidence.json`
- `geographic_scope_validation.csv`
- `fix_manifest.json`

## 6. Perubahan scope

| Event | Lokasi | Sebelum | Sesudah | Dasar |
|---|---|---|---|---|
| `EVT-BMKG-8102A3842AA3` | 169 km BaratLaut TANIMBAR | `ya` | `tidak_diketahui` | Jarak jauh, tanpa batas nasional |
| `EVT-BMKG-9926ADFBE909` | 139 km BaratLaut TUAL-MALUKU | `ya` | `tidak_diketahui` | Toponimi ada, jarak jauh |
| `EVT-BMKG-72D9473D8378` | 153 km Tenggara OKSIBIL-PAPUAPGNGN | `tidak` | `tidak_diketahui` | Di luar bbox pilot; dekat perbatasan; tanpa polygon batas |
| `EVT-BMKG-FFB357F335AE` | 201 km BaratLaut TANIMBAR | `ya` | `tidak_diketahui` | Jarak jauh, tanpa batas nasional |
| `EVT-BMKG-8F1F74FF387A` | 187 km BaratLaut TAHUNA-KEP.SANGIHE-SULUT | `ya` | `tidak_diketahui` | Toponimi ada, jarak jauh |
| `EVT-BMKG-9C6C2E535D8B` | 221 km BaratLaut PULAUKARATUNG-SULUT | `ya` | `tidak_diketahui` | Toponimi ada, jarak jauh |
| `EVT-BMKG-608A37F640B2` | 136 km BaratDaya GUNUNGKIDUL-DIY | `ya` | `tidak_diketahui` | Toponimi ada, jarak jauh |
| `EVT-BMKG-43C1A2818383` | 62 km TimurLaut MALUKUBRTDAYA | `ya` | `tidak_diketahui` | Toponimi ada, jarak di atas ambang dekat |
| `EVT-BMKG-B2A5A39AE099` | Pusat gempa berada di laut 13 km tenggara Bahodopi | `ya` | `tidak_diketahui` | Laut, tanpa batas nasional |
| `EVT-BMKG-FC99150BA61F` | Pusat gempa berada di laut 97 km barat Kodi, Sumba Barat Daya | `ya` | `tidak_diketahui` | Laut, tanpa batas nasional |
| `EVT-USGS-7000tusv` | Banda Sea | `ya` | `tidak_diketahui` | Laut, tanpa batas nasional |

Event yang tetap `ya` setelah evaluasi:

| Event | Lokasi | Dasar |
|---|---|---|
| `EVT-BMKG-E366564A79CD` | Pusat gempa di darat 9 km Utara Kota Jayapura | Toponimi + penanda darat |
| `EVT-BMKG-5989CC896238` | 1 km BaratDaya TOMOHON-SULUT | Toponimi + jarak dekat |
| `EVT-BMKG-48042118A4F4` | 6 km BaratLaut LEBONG-BENGKULU | Toponimi + jarak dekat |
| `EVT-BMKG-4C3A1522F512` | Pusat gempa di darat 24 km Barat Daya Kab. Pidie Jaya-Aceh | Toponimi + penanda darat |
| `EVT-BMKG-A758C4218E6B` | Pusat gempa di darat 14 km Timur Laut Kendari | Toponimi + penanda darat |
| `EVT-BMKG-AEA98CA645B3` | Pusat gempa di darat 7 km barat daya Samosir | Toponimi + penanda darat |
| `EVT-BMKG-003786C08B87` | Pusat gempa di 20 km Timur Laut Kota Sorong | Toponimi + jarak dekat |
| `EVT-BMKG-7034309488A9` | Pusat gempa di darat 31 km Timur Laut Kabupaten Gayolues | Toponimi + penanda darat |
| `EVT-USGS-7000tuuy` | 19 km WNW of Tomohon, Indonesia | Toponimi + jarak dekat |

Tidak ada event pilot yang dapat dibuktikan sebagai luar Indonesia. Karena itu hasil `tidak=0` bukan berarti aturan luar Indonesia tidak ada. Aturan `tidak` diuji dengan kasus sintetis Nicaragua pada `test_geographic_scope.py`.

## 7. Kategori dan relasi

Kategori tidak berubah:

- 20 event tetap berkategori `Gempabumi`.
- 20 event tetap `category_scope=in_scope`.
- `category.csv` hash sumber dan output sama: `d0675f06b96510c59eb2105112a2278ca4110e81d3e207a8cbf67faa4b06cbf1`.

Dua relasi FIX 02 tetap utuh dan tidak diubah:

| Relasi | From | To | Tipe |
|---|---|---|---|
| `EREL-058FFADAE49A4801` | `EVT-BMKG-8102A3842AA3` | `EVT-USGS-7000tusv` | `related_to` |
| `EREL-6947058A57B66894` | `EVT-BMKG-5989CC896238` | `EVT-USGS-7000tuuy` | `related_to` |

Hash `event_relation.csv` sumber dan output sama: `f5b8c497a2ddae8b82351de385c219148a91716a7c9c94f888d8e8f7fb702eae`. Tidak ada merge atau hapus event.

## 8. Invariant dan hash

Semua pemeriksaan manifest bernilai `true`:

| Pemeriksaan | Status |
|---|---|
| `event_count_unchanged` | Lulus |
| `event_ids_unchanged` | Lulus |
| `event_table_unchanged` | Lulus |
| `no_event_deleted` | Lulus |
| `no_merge` | Lulus |
| `event_location_ids_unchanged` | Lulus |
| `event_location_only_scope_fields_changed` | Lulus |
| `all_scope_changes_logged` | Lulus |
| `no_unlogged_location_changes` | Lulus |
| `category_table_unchanged` | Lulus |
| `category_names_unchanged` | Lulus |
| `category_scope_unchanged` | Lulus |
| `event_relation_table_unchanged` | Lulus |
| `fix02_relations_preserved` | Lulus |
| `raw_payload_table_unchanged` | Lulus |
| `raw_payload_files_unchanged` | Lulus |
| `baseline_unchanged` | Lulus |
| `source_fix_unchanged` | Lulus |
| `scope_values_valid` | Lulus |
| `no_outer_bbox_marked_indonesia` | Lulus |
| `change_log_count_expected` | Lulus |

Hash utama:

| Objek | SHA-256 |
|---|---|
| Baseline | `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06` |
| `event.csv` sumber dan output | `dbfa6d732e5b66bd92adc783608e844b7b4c4ec471be3d0fd13db77cb51e4eff` |
| `event_relation.csv` sumber dan output | `f5b8c497a2ddae8b82351de385c219148a91716a7c9c94f888d8e8f7fb702eae` |
| `category.csv` sumber dan output | `d0675f06b96510c59eb2105112a2278ca4110e81d3e207a8cbf67faa4b06cbf1` |
| `event_location.csv` output | `3632c2fa22a1c399a2b6d407b6e9d39a501ee4bea1b2b9bf71aeff8aa96b59e9` |
| `change_log.csv` output | `c4d42f4b1d8c4f39ac546dfc93e42dd8f57b925d0908155309e41da2a37427dd` |
| `raw_payload.csv` sumber dan output | `49c9999322e405c7c612fd2ca764d409c341a13c46209c549d3db040859b4525` |

Raw payload tidak berubah:

| Raw payload | SHA-256 |
|---|---|
| `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90` | `e5665e90cf097640eb5d9790536366ef6e4329c7f9dcd9c9170b44ea01673e7b` |
| `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | `9b1bc264382d54c9b69471412159d1f96c05741598c4f39047bf430e64c2c47b` |
| `RAW-usgs_m45-20261102T110641Z-fbb7638a` | `fbb7638a2198b07a9bdd1531b1b3712b4e14b662e1bc416086e3f04fb7b116f0` |

## 9. Validasi

Hasil `geographic_scope_validation.csv`:

| Rule | Severity | Status | Catatan |
|---|---|---|---|
| `R-LOC-05` | P0 | Lulus | 20/20 flag konsisten dengan classifier; bbox pilot bukan bukti tunggal |
| `R-GEO-01` | P1 | Lulus | Semua `unknown`/`luar` memiliki basis dan alasan |
| `R-GEO-02` | P0 | Lulus | `category_scope` tidak diubah dan tidak dipakai sebagai geographic scope |
| `R-GEO-03` | P0 | Lulus | `source_coordinate` tidak dinaikkan menjadi `verified` |
| `R-GEO-04` | P0 | Lulus | Tidak ada titik di luar bbox pilot yang dipaksa `ya` |
| `R-GEO-05` | P0 | Lulus | Dua relasi FIX 02 dipertahankan |
| `R-GEO-06` | P1 | Perlu review | 11 event `tidak_diketahui` masuk review manual |

Validator pilot juga menerima output FIX 03: `R-LOC-05` lulus 20/20 record.

## 10. Test

Test terarah:

```text
.venv\Scripts\python.exe -m unittest -v test_geographic_scope
18 test, lulus semua
```

Regresi FIX 02:

```text
.venv\Scripts\python.exe -m unittest -v test_event_relation_candidates
17 test, lulus semua
```

Full suite:

```text
.venv\Scripts\python.exe -m unittest discover -v
112 test dijalankan; 111 lulus; 1 error lama pada test_scraper
```

Error `test_scraper` tidak terkait FIX 03:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

## 11. Batas dan rekomendasi

Batas:

- Repository belum memiliki polygon batas wilayah Indonesia yang dapat dipertanggungjawabkan. Karena itu titik di laut, dekat perbatasan, atau di luar bbox pilot tidak dipaksa menjadi `ya`/`tidak`.
- `coordinate_status` tetap `source_coordinate`; FIX 03 tidak mengklaim verifikasi koordinat.
- Sebelas event `tidak_diketahui` membutuhkan review manual atau dataset batas wilayah resmi sebelum dapat ditetapkan sebagai Indonesia/luar Indonesia.
- Tidak ada event pilot yang dapat dibuktikan luar Indonesia. Aturan `tidak` sudah diimplementasikan dan diuji, tetapi belum ada event pilot yang memenuhinya.

Rekomendasi:

1. Tambahkan dataset batas wilayah Indonesia yang berlisensi dan terdokumentasi, misalnya polygon resmi, sebelum menaikkan status `tidak_diketahui` secara massal.
2. Review manual 11 event `tidak_diketahui`, terutama Oksibil, Tanimbar, Tual, Tahuna, Pulau Karatung, Maluku Barat Daya, Gunungkidul, Bahodopi, Kodi, dan Banda Sea.
3. Pertahankan pemisahan `category_scope` dan `is_inside_indonesia`. Jangan mengubah `category_scope` hanya karena lokasi di luar Indonesia.
4. Untuk event internasional baru, simpan event dan tandai geographic scope `tidak` bila ada bukti wilayah asing yang jelas; jangan hapus event.
