# FIX 04 - Review Manual Geographic Scope 11 Event Tidak Diketahui

Tanggal: **2026-11-03**  
Fix ID: `FIX-GEOGRAPHIC-REVIEW-20261103T061354Z`  
Sumber: `data/pilot/fixes/FIX-GEOGRAPHIC-SCOPE-20261103T055509Z`  
Output: `data/pilot/fixes/FIX-GEOGRAPHIC-REVIEW-20261103T061354Z`  
Status: **11 event direview; semua tetap `tidak_diketahui`; tidak ada perubahan data**

## 1. Tujuan dan batas

FIX 04 melakukan review manual terhadap 11 event yang ditinggalkan FIX 03 sebagai `event_location.is_inside_indonesia=tidak_diketahui`. Review memakai bukti raw BMKG/USGS, bukan judul event, bbox pilot, atau asumsi toponimi.

Batas yang dipertahankan:

- Tidak mengubah `event`, `category`, `category_scope`, `event_relation`, `raw_payload`, atau baseline.
- Tidak menghapus, menggabungkan, atau mengganti `event_id`.
- Tidak mengubah output FIX 01, FIX 02, dan FIX 03 sebagai sumber.
- Tidak menaikkan `coordinate_status=source_coordinate` menjadi `verified`.
- Tidak memakai bbox pilot sebagai batas wilayah nasional.
- Tidak memakai judul event sebagai bukti lokasi.
- Tidak menambahkan `change_log` jika tidak ada perubahan status.
- Tidak mengubah schema; field dan vocabulary yang tersedia sudah cukup.

## 2. Metode review

Setiap event dicocokkan ke raw payload resmi memakai `DateTime` dan koordinat, atau external ID USGS. Review memakai:

- `Wilayah` dari `bmkg_gempa_terkini.xml`.
- `Wilayah` dan `Dirasakan` dari `bmkg_gempa_dirasakan.xml`.
- `title` dari `usgs_m45.atom`.
- Dokumen resmi yang terhubung sebagai konteks tambahan.

Temuan penting: tiga event memiliki record pendukung di `bmkg_gempa_dirasakan.xml` yang tidak terhubung sebagai dokumen pendukung pada `document_event_link.csv`. FIX 04 tetap menemukannya dengan pencocokan raw `DateTime` + koordinat:

| Event | Record pendukung yang ditemukan |
|---|---|
| `EVT-BMKG-72D9473D8378` | `Pusat gempa berada di darat 153 km tenggara Oksibil` |
| `EVT-BMKG-FFB357F335AE` | `Pusat gempa berada di laut 60 km Baratlaut Larat-Kep.Tanimbar` |
| `EVT-BMKG-608A37F640B2` | `Pusat gempa berada di laut 137 km Selatan Gunungkidul` |

Bukti tersebut memperkuat keputusan, tetapi tidak mengubah hasil: titik laut dan titik darat dekat perbatasan tetap tidak dapat ditetapkan sebagai Indonesia/luar Indonesia tanpa polygon batas nasional.

## 3. Keputusan review

Semua 11 event tetap `tidak_diketahui`. Tidak ada event yang dipaksa menjadi `ya` atau `tidak`.

| Event | Lokasi resmi | Koordinat | Keputusan | Keyakinan | Basis |
|---|---|---|---|---|---|
| `EVT-BMKG-8102A3842AA3` | 169 km BaratLaut TANIMBAR | `-7.0800,130.0700` | `tidak_diketahui` | high | `episentrum_laut_tanpa_batas_nasional` |
| `EVT-BMKG-9926ADFBE909` | 139 km BaratLaut TUAL-MALUKU | `-4.4000,132.4900` | `tidak_diketahui` | medium | `tanpa_penanda_darat_laut_tanpa_batas_nasional` |
| `EVT-BMKG-72D9473D8378` | 153 km Tenggara OKSIBIL-PAPUAPGNGN | `-5.4500,141.9000` | `tidak_diketahui` | high | `episentrum_darat_dekat_perbatasan_tanpa_batas_nasional` |
| `EVT-BMKG-FFB357F335AE` | 201 km BaratLaut TANIMBAR | `-6.3400,130.5200` | `tidak_diketahui` | high | `episentrum_laut_tanpa_batas_nasional` |
| `EVT-BMKG-8F1F74FF387A` | 187 km BaratLaut TAHUNA-KEP.SANGIHE-SULUT | `5.3000,125.4200` | `tidak_diketahui` | medium | `tanpa_penanda_darat_laut_tanpa_batas_nasional` |
| `EVT-BMKG-9C6C2E535D8B` | 221 km BaratLaut PULAUKARATUNG-SULUT | `5.5900,125.2700` | `tidak_diketahui` | medium | `tanpa_penanda_darat_laut_tanpa_batas_nasional` |
| `EVT-BMKG-608A37F640B2` | 136 km BaratDaya GUNUNGKIDUL-DIY | `-9.2000,110.3900` | `tidak_diketahui` | high | `episentrum_laut_tanpa_batas_nasional` |
| `EVT-BMKG-43C1A2818383` | 62 km TimurLaut MALUKUBRTDAYA | `-7.7500,128.1800` | `tidak_diketahui` | medium | `tanpa_penanda_darat_laut_tanpa_batas_nasional` |
| `EVT-BMKG-B2A5A39AE099` | Pusat gempa berada di laut 13 km tenggara Bahodopi | `-2.8700,122.2100` | `tidak_diketahui` | high | `episentrum_laut_tanpa_batas_nasional` |
| `EVT-BMKG-FC99150BA61F` | Pusat gempa berada di laut 97 km barat Kodi, Sumba Barat Daya | `-9.4500,118.1100` | `tidak_diketahui` | high | `episentrum_laut_tanpa_batas_nasional` |
| `EVT-USGS-7000tusv` | Banda Sea | `-6.9205,129.9514` | `tidak_diketahui` | high | `episentrum_laut_tanpa_batas_nasional` |

Ringkasan keputusan: `ya=0`, `tidak=0`, `tidak_diketahui=11`, `status_changes=0`.

### 3.1 Sumber dokumen per event

| Event | Sumber utama | Dokumen bukti | Raw payload bukti |
|---|---|---|---|
| `EVT-BMKG-8102A3842AA3` | `bmkg_gempa_terkini` | `DOC-fd54e30527cf02db`, `DOC-ee237cea966fd37d` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90`, `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` |
| `EVT-BMKG-9926ADFBE909` | `bmkg_gempa_terkini` | `DOC-c92e242be308ca7c` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90` |
| `EVT-BMKG-72D9473D8378` | `bmkg_gempa_terkini` | `DOC-b5e6c0cf56585a3d` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90`, `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` |
| `EVT-BMKG-FFB357F335AE` | `bmkg_gempa_terkini` | `DOC-83b15f792015119f` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90`, `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` |
| `EVT-BMKG-8F1F74FF387A` | `bmkg_gempa_terkini` | `DOC-1e6e76a86b5afd87` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90` |
| `EVT-BMKG-9C6C2E535D8B` | `bmkg_gempa_terkini` | `DOC-60f6ac00d841e3aa` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90` |
| `EVT-BMKG-608A37F640B2` | `bmkg_gempa_terkini` | `DOC-f567cc62e4d557b9` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90`, `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` |
| `EVT-BMKG-43C1A2818383` | `bmkg_gempa_terkini` | `DOC-29e3b5aa9d56dc0f` | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90` |
| `EVT-BMKG-B2A5A39AE099` | `bmkg_gempa_dirasakan` | `DOC-e3206b633c617e59` | `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` |
| `EVT-BMKG-FC99150BA61F` | `bmkg_gempa_dirasakan` | `DOC-95805e55d3fe5d92` | `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` |
| `EVT-USGS-7000tusv` | `usgs_m45` | `DOC-83ae76fc3aed7f4d` | `RAW-usgs_m45-20261102T110641Z-fbb7638a` |

Catatan: untuk `72D9473D8378`, `FFB357F335AE`, dan `608A37F640B2`, record
`bmkg_gempa_dirasakan` yang cocok ditemukan lewat `DateTime` + koordinat tetapi
belum terhubung di `document_event_link.csv`. Record itu dipakai sebagai bukti
review, bukan sebagai perubahan tabel relasi dokumen.

### 3.2 Daftar event yang tetap tidak diketahui

Kesebelas event berikut tetap `tidak_diketahui`:

1. `EVT-BMKG-8102A3842AA3`
2. `EVT-BMKG-9926ADFBE909`
3. `EVT-BMKG-72D9473D8378`
4. `EVT-BMKG-FFB357F335AE`
5. `EVT-BMKG-8F1F74FF387A`
6. `EVT-BMKG-9C6C2E535D8B`
7. `EVT-BMKG-608A37F640B2`
8. `EVT-BMKG-43C1A2818383`
9. `EVT-BMKG-B2A5A39AE099`
10. `EVT-BMKG-FC99150BA61F`
11. `EVT-USGS-7000tusv`

## 4. Dasar per event

- `8102`: raw BMKG menyebut `di laut 169 km BaratLaut Tanimbar`; USGS menyebut `Banda Sea`. Titik laut tidak dapat ditetapkan tanpa polygon batas.
- `9926`: lokasi resmi hanya `139 km BaratLaut TUAL-MALUKU`; tidak ada penanda darat/laut eksplisit dan tidak ada batas nasional.
- `72D`: raw pendukung menyebut `di darat 153 km tenggara Oksibil`. Penanda darat tidak membuktikan negara karena titik berada di luar bbox pilot dan dekat perbatasan Indonesia-PNG.
- `FFB`: raw pendukung menyebut `di laut 60 km Baratlaut Larat-Kep.Tanimbar`; `location_name` FIX 03 menyebut `201 km BaratLaut TANIMBAR`. Keduanya merujuk laut dan tidak ada batas nasional.
- `8F1F`: lokasi resmi hanya `187 km BaratLaut TAHUNA-KEP.SANGIHE-SULUT`; tidak ada penanda darat/laut eksplisit.
- `9C6`: lokasi resmi hanya `221 km BaratLaut PULAUKARATUNG-SULUT`; tidak ada penanda darat/laut eksplisit.
- `608A`: raw pendukung menyebut `di laut 137 km Selatan Gunungkidul`; titik laut tidak dapat ditetapkan tanpa polygon batas.
- `43C1`: lokasi resmi hanya `62 km TimurLaut MALUKUBRTDAYA`; jarak melewati ambang dekat classifier dan tidak ada batas nasional.
- `B2A`: raw BMKG menyebut `di laut 13 km tenggara Bahodopi`; Morowali adalah daerah terdampak, bukan bukti lokasi epicenter.
- `FC9`: raw BMKG menyebut `di laut 97 km barat Kodi, Sumba Barat Daya`; Sumbawa adalah daerah terdampak, bukan bukti lokasi epicenter.
- `USGS-7000tusv`: USGS menamai lokasi `Banda Sea`; BMKG counterpart juga menyebut laut.

## 5. Output dan metrik

| Item | Nilai |
|---|---|
| Event sebelum/sesudah | 20 / 20 |
| Event location sebelum/sesudah | 20 / 20 |
| Relasi sebelum/sesudah | 2 / 2 |
| `change_log` sebelum/sesudah | 386 / 386 |
| Scope sebelum | `ya=9`, `tidak=0`, `tidak_diketahui=11` |
| Scope sesudah | `ya=9`, `tidak=0`, `tidak_diketahui=11` |
| Event direview | 11 |
| Perubahan status | 0 |
| Sisa `tidak_diketahui` | 11 |

File output utama:

- `tables/` - 15 tabel, byte-identik dengan FIX 03.
- `geographic_review.csv` - 11 keputusan review.
- `geographic_review_evidence.json` - bukti raw dan dokumen per event.
- `geographic_review_validation.csv` - validasi R-GEO-07 sampai R-GEO-11 dan R-LOC-05.
- `fix_manifest.json` - manifest dan seluruh checks.

Karena tidak ada perubahan status, `change_log.csv` tidak bertambah. Review dicatat dalam artefak review, bukan sebagai perubahan data.

## 6. Invariant dan hash

Seluruh `tables/*.csv` output identik byte-per-byte dengan FIX 03. Tidak ada field yang berubah.

| Objek | SHA-256 |
|---|---|
| Baseline | `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06` |
| Manifest FIX 03 sumber | `52e1a0788d50c9152ed0c72dbf63d47298f86340cb30ed4064205334c2f7c86f` |
| Manifest FIX 04 output | `a09c2ea250e34056ff2c4da43c8944c6174787386110c2d6451e7a27cdfeba92` |
| `event.csv` | `dbfa6d732e5b66bd92adc783608e844b7b4c4ec471be3d0fd13db77cb51e4eff` |
| `event_location.csv` | `3632c2fa22a1c399a2b6d407b6e9d39a501ee4bea1b2b9bf71aeff8aa96b59e9` |
| `event_relation.csv` | `f5b8c497a2ddae8b82351de385c219148a91716a7c9c94f888d8e8f7fb702eae` |
| `category.csv` | `d0675f06b96510c59eb2105112a2278ca4110e81d3e207a8cbf67faa4b06cbf1` |
| `change_log.csv` | `c4d42f4b1d8c4f39ac546dfc93e42dd8f57b925d0908155309e41da2a37427dd` |
| `raw_payload.csv` | `49c9999322e405c7c612fd2ca764d409c341a13c46209c549d3db040859b4525` |
| `geographic_review.csv` | `7e29eb2b23d344a1db7154934ae8d3888acebe6d5db0d12560066276defcd249` |
| `geographic_review_evidence.json` | `0701286374dc18517ad78fdb7eead92d6a8fdaf2cff5b81fc3db2d5a6c1a0813` |
| `geographic_review_validation.csv` | `26f0f795a08c39f2f180c2e51083cf886c4f0ff171360f484a7c94b6655a1850` |

Dua relasi FIX 02 tetap utuh:

- `EREL-058FFADAE49A4801`: `EVT-BMKG-8102A3842AA3` ↔ `EVT-USGS-7000tusv`.
- `EREL-6947058A57B66894`: `EVT-BMKG-5989CC896238` ↔ `EVT-USGS-7000tuuy`.

Raw payload tidak berubah:

- `bmkg_gempa_terkini.xml`: `e5665e90cf097640eb5d9790536366ef6e4329c7f9dcd9c9170b44ea01673e7b`
- `bmkg_gempa_dirasakan.xml`: `9b1bc264382d54c9b69471412159d1f96c05741598c4f39047bf430e64c2c47b`
- `usgs_m45.atom`: `fbb7638a2198b07a9bdd1531b1b3712b4e14b662e1bc416086e3f04fb7b116f0`

## 7. Validasi dan test

Hasil `geographic_review_validation.csv`:

| Rule | Severity | Status | Catatan |
|---|---|---|---|
| `R-GEO-07` | P0 | Lulus | 11 event target direview tepat sekali |
| `R-GEO-08` | P0 | Lulus | Vocabulary sah; tidak ada perubahan status tanpa log |
| `R-GEO-09` | P1 | Lulus | Semua review memiliki bukti raw/dokumen, basis, dan alasan |
| `R-GEO-10` | P0 | Lulus | Event, kategori, category_scope, relasi, raw payload, baseline, koordinat sumber tetap |
| `R-GEO-11` | P0 | Lulus | Tidak ada `source_coordinate` yang dinaikkan menjadi `verified` |
| `R-LOC-05` | P1 | Lulus | Validator pilot menerima output FIX 04; 20/20 record |

Test terarah:

```text
.venv\Scripts\python.exe -m unittest -v test_geographic_review
10 test, lulus semua
```

Regresi terkait:

```text
.venv\Scripts\python.exe -m unittest -v test_geographic_scope
18 test, lulus semua

.venv\Scripts\python.exe -m unittest -v test_event_relation_candidates
17 test, lulus semua
```

Full suite:

```text
.venv\Scripts\python.exe -m unittest discover -v
122 test dijalankan; 121 lulus; 1 error lama pada test_scraper
```

Error `test_scraper` tidak terkait FIX 04:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

## 8. Kesimpulan, batas, dan rekomendasi

Kesimpulan: dari 11 event `tidak_diketahui`, tidak ada satu pun yang memiliki
bukti cukup untuk ditetapkan sebagai Indonesia atau luar Indonesia. Sebagian
besar adalah episentrum laut tanpa polygon batas nasional; satu event berada di
darat dekat perbatasan Indonesia-PNG; sisanya berjarak jauh dari toponimi
rujukan tanpa penanda darat/laut yang tegas. Bukti resmi BMKG/USGS hanya
menyebut lokasi relatif terhadap toponimi (misalnya "169 km BaratLaut
Tanimbar"), bukan bukti yurisdiksi. Karena itu keputusan yang dapat
dipertanggungjawabkan adalah mempertahankan `tidak_diketahui` untuk kesebelas
event, tanpa perubahan status, data, kategori, relasi, atau baseline.

Batas:

- Repository belum memiliki polygon batas wilayah Indonesia yang berlisensi dan dapat dipertanggungjawabkan.
- Bbox pilot bukan batas nasional dan tidak dipakai untuk memaksa status.
- Titik laut, titik dekat perbatasan, dan jarak jauh tanpa batas resmi tetap `tidak_diketahui`.
- `coordinate_status` tetap `source_coordinate`; review ini bukan verifikasi koordinat.
- Tiga record pendukung BMKG ditemukan di raw payload tetapi tidak terhubung di `document_event_link.csv`; FIX 04 memakainya sebagai bukti review tanpa mengubah tabel relasi dokumen.

Rekomendasi:

1. Tambahkan polygon batas wilayah Indonesia yang terdokumentasi sebelum menaikkan status 11 event ini.
2. Perbaiki pemetaan `document_event_link` untuk record `bmkg_gempa_dirasakan` yang saat ini belum terhubung, terutama Oksibil, FFB/Tanimbar, dan Gunungkidul.
3. Pertahankan pemisahan `category_scope` dan `is_inside_indonesia`.
4. Jangan menaikkan `coordinate_status` tanpa proses verifikasi koordinat yang eksplisit.
