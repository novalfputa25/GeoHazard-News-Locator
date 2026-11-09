# FIX 05 - Audit Document Event Link Tiga Record bmkg_gempa_dirasakan

Tanggal: **2026-11-03**  
Sumber data: `data/pilot/fixes/FIX-GEOGRAPHIC-REVIEW-20261103T061354Z`  
Run pilot: `PILOT-20261102T110641Z`  
Status: **audit read-only; tiga record terkonfirmasi terkait event yang sudah ada; belum ada perubahan data atau kode**

## 1. Tujuan dan batas

FIX 05 mengaudit tiga record `bmkg_gempa_dirasakan` yang disebut pada FIX 04 sebagai belum terhubung:

1. Oksibil
2. Tanimbar/FFB
3. Gunungkidul

Tujuan audit adalah memastikan apakah ketiga record benar-benar berkaitan dengan event yang sudah ada di dataset pilot. Audit memakai `document_id`, `external_id`, `event_id`, waktu, koordinat, magnitudo, kedalaman, dan isi record. Audit tidak memakai web, geocoding eksternal, atau kemiripan nama lokasi sebagai bukti utama.

Batas yang dipertahankan:

- Tidak mengubah baseline, output FIX 01 sampai FIX 04, atau raw payload.
- Tidak membuat event baru.
- Tidak menggabungkan event.
- Tidak mengubah kategori bahaya atau `category_scope`.
- Tidak mengubah `is_inside_indonesia` atau status cakupan geografis.
- Tidak menghubungkan record secara paksa bila identitasnya tidak dapat dipastikan.
- Tidak mengubah schema atau kode produksi.

## 2. Sumber dan konteks

Laporan dan output yang dibaca:

- `reports/FIX_02_EVENT_RELATION.md`
- `reports/FIX_03_GEOGRAPHIC_SCOPE.md`
- `reports/FIX_04_GEOGRAPHIC_REVIEW.md`
- `reports/PILOT_PENGUMPULAN_DATA.md`
- `reports/AUDIT_KUALITAS_PILOT.md`
- `data/pilot/fixes/FIX-GEOGRAPHIC-REVIEW-20261103T061354Z/tables/*.csv`
- `data/pilot/runs/PILOT-20261102T110641Z/raw/bmkg_gempa_dirasakan.xml`
- `data/pilot/runs/PILOT-20261102T110641Z/raw/bmkg_gempa_terkini.xml`
- `docs/PROVENANCE_FIELD_DICTIONARY.csv`
- `scripts/pilot_collect_official_geohazard.py`

Konteks dataset:

| Item | Nilai |
|---|---:|
| Event | 20 |
| Dokumen | 23 |
| `document_event_link` | 23 |
| Dokumen tanpa link | 0 |
| Record `bmkg_gempa_dirasakan` di raw XML | 15 |
| Record `bmkg_gempa_dirasakan` yang dipilih menjadi dokumen | 10 |
| Record `bmkg_gempa_dirasakan` tidak dipilih | 5 |

Pilot membatasi tiap sumber dengan `MAX_ITEMS_PER_SOURCE=10` dan memakai `parsed_items[:MAX_ITEMS_PER_SOURCE]`. Karena feed `bmkg_gempa_dirasakan` berisi 15 record, lima record terakhir tidak pernah menjadi baris `document`. Dari lima record itu:

- tiga record cocok dengan event yang sudah ada: Oksibil, Tanimbar/FFB, dan Gunungkidul;
- dua record Tanggamus (28 Oktober 2026) tidak memiliki event kandidat di dataset pilot.

Dengan demikian, ketiga objek audit ini **bukan baris `document` yang sudah ada tetapi belum dikaitkan**. Ketiganya adalah record raw yang belum dimaterialisasi menjadi `document`, sehingga memang tidak mungkin memiliki `document_id` atau baris `document_event_link` pada dataset saat ini. Seluruh 23 dokumen yang sudah ada sudah memiliki link.

## 3. Identitas tiga record

Tidak ada `document_id` atau `document_external_id` native BMKG di raw XML untuk ketiga record ini. Identitas record di bawah memakai posisi record pada raw XML dan `external_id` deterministik yang dibentuk oleh pipeline pilot dari `source_id|DateTime|lat|lon|magnitude`.

| Label | Raw payload | Record ke- | `DateTime` | Koordinat | Mag | Kedalaman | `Wilayah` | `Dirasakan` |
|---|---|---:|---|---|---:|---:|---|---|
| Oksibil | `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | 11 | `2026-10-29T03:26:49+00:00` | `-5.4500,141.9000` | 6.0 | 120 km | Pusat gempa berada di darat 153 km tenggara Oksibil | III Boven Digoel, II Jayapura, II Merauke |
| Tanimbar/FFB | `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | 12 | `2026-10-28T22:06:47+00:00` | `-6.3400,130.5200` | 6.4 | 160 km | Pusat gempa berada di laut 60 km Baratlaut Larat-Kep.Tanimbar | II - III Banda Naira, II - III Tanimbar, II - III Kaimana, II - III Sorong |
| Gunungkidul | `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | 15 | `2026-10-27T14:43:13+00:00` | `-9.2000,110.3900` | 5.4 | 10 km | Pusat gempa berada di laut 137 km Selatan Gunungkidul | II Bantul, II Sleman, II Wonogiri, II Kulon Progo, II Sukoharjo, II Trenggalek, II Nganjuk, II Pacitan, II Klaten, II Kediri, II Ponorogo, II Banjarnegara, II Lumajang, II Blitar |

Identitas deterministik yang dihitung dengan fungsi pipeline yang sama:

| Label | `external_id` kandidat | `event_key` BMKG | Event ID hasil identitas |
|---|---|---|---|
| Oksibil | `bmkg_gempa_dirasakan\|2026-10-29T03:26:49+00:00\|-5.4500\|141.9000\|6.0` | `BMKG\|2026-10-29T03:26:49+00:00\|-5.45\|141.90\|6.0` | `EVT-BMKG-72D9473D8378` |
| Tanimbar/FFB | `bmkg_gempa_dirasakan\|2026-10-28T22:06:47+00:00\|-6.3400\|130.5200\|6.4` | `BMKG\|2026-10-28T22:06:47+00:00\|-6.34\|130.52\|6.4` | `EVT-BMKG-FFB357F335AE` |
| Gunungkidul | `bmkg_gempa_dirasakan\|2026-10-27T14:43:13+00:00\|-9.2000\|110.3900\|5.4` | `BMKG\|2026-10-27T14:43:13+00:00\|-9.20\|110.39\|5.4` | `EVT-BMKG-608A37F640B2` |

Status di dataset saat ini:

| Label | `document_id` | Baris `document` | Baris `document_event_link` |
|---|---|---|---|
| Oksibil | tidak ada | tidak ada | tidak ada |
| Tanimbar/FFB | tidak ada | tidak ada | tidak ada |
| Gunungkidul | tidak ada | tidak ada | tidak ada |

## 4. Event kandidat yang diperiksa

| Label | Event ID | Sumber primer event | Dokumen primer | Waktu event | Koordinat | Mag | Kedalaman | Link saat ini |
|---|---|---|---|---|---:|---:|---|
| Oksibil | `EVT-BMKG-72D9473D8378` | `bmkg_gempa_terkini` | `DOC-b5e6c0cf56585a3d` | `2026-10-29T03:26:49+00:00` | `-5.4500,141.9000` | 6.0 | 120 km | 1 primer |
| Tanimbar/FFB | `EVT-BMKG-FFB357F335AE` | `bmkg_gempa_terkini` | `DOC-83b15f792015119f` | `2026-10-28T22:06:47+00:00` | `-6.3400,130.5200` | 6.4 | 160 km | 1 primer |
| Gunungkidul | `EVT-BMKG-608A37F640B2` | `bmkg_gempa_terkini` | `DOC-f567cc62e4d557b9` | `2026-10-27T14:43:13+00:00` | `-9.2000,110.3900` | 5.4 | 10 km | 1 primer |

Ketiga event sudah ada sebelum FIX 05. Tidak ada event baru yang diperlukan.

## 5. Perbandingan waktu, koordinat, magnitudo, dan isi dokumen

| Label | Pembanding | Waktu | Koordinat | Magnitudo | Kedalaman | Hasil |
|---|---|---|---|---|---|---|
| Oksibil | Record `dirasakan` vs event `terkini` | sama persis, selisih 0 detik | sama persis, selisih 0 | 6.0 vs 6.0 | 120 km vs 120 km | cocok penuh |
| Tanimbar/FFB | Record `dirasakan` vs event `terkini` | sama persis, selisih 0 detik | sama persis, selisih 0 | 6.4 vs 6.4 | 160 km vs 160 km | cocok penuh |
| Gunungkidul | Record `dirasakan` vs event `terkini` | sama persis, selisih 0 detik | sama persis, selisih 0 | 5.4 vs 5.4 | 10 km vs 10 km | cocok penuh |

Perbandingan isi:

| Label | `Wilayah` di `terkini` | `Wilayah` di `dirasakan` | Catatan |
|---|---|---|---|
| Oksibil | `153 km Tenggara OKSIBIL-PAPUAPGNGN` | `Pusat gempa berada di darat 153 km tenggara Oksibil` | Konsisten; versi `dirasakan` menambahkan penanda darat. |
| Tanimbar/FFB | `201 km BaratLaut TANIMBAR` | `Pusat gempa berada di laut 60 km Baratlaut Larat-Kep.Tanimbar` | Teks memakai titik rujukan dan jarak berbeda, tetapi waktu, koordinat, magnitudo, dan kedalaman identik. Perbedaan teks tidak dipakai sebagai bukti identitas. |
| Gunungkidul | `136 km BaratDaya GUNUNGKIDUL-DIY` | `Pusat gempa berada di laut 137 km Selatan Gunungkidul` | Arah dan jarak relatif berbeda 1 km pada teks; parameter inti identik. |

Pemeriksaan kandidat lain:

- Tidak ada event lain dengan `DateTime` yang sama pada ketiga waktu tersebut.
- Tidak ada event lain dengan pasangan koordinat yang sama.
- Tidak ada event lain dengan `event_key` BMKG yang sama.
- `event_key` deterministik dari ketiga record menghasilkan `event_id` yang sudah ada, bukan ID baru.

Berdasarkan waktu, koordinat, magnitudo, kedalaman, dan `event_key` yang identik, ketiga record adalah **record BMKG yang sama dengan event kandidat**, dilihat dari dua feed BMKG yang berbeda. Ini bukan sekadar kemiripan nama lokasi.

## 6. Keputusan masing-masing record

| Label | Event kandidat | Keputusan audit | Keyakinan | Status teknis saat ini |
|---|---|---|---|---|
| Oksibil | `EVT-BMKG-72D9473D8378` | **Terkait terkonfirmasi; layak menjadi link pendukung bila dokumen dimaterialisasi** | high | belum terhubung karena `document` belum ada |
| Tanimbar/FFB | `EVT-BMKG-FFB357F335AE` | **Terkait terkonfirmasi; layak menjadi link pendukung bila dokumen dimaterialisasi** | high | belum terhubung karena `document` belum ada |
| Gunungkidul | `EVT-BMKG-608A37F640B2` | **Terkait terkonfirmasi; layak menjadi link pendukung bila dokumen dimaterialisasi** | high | belum terhubung karena `document` belum ada |

Ringkasan:

- Record terkait terkonfirmasi: **3**
- Record ditolak: **0**
- Event baru yang dibuat: **0**
- Event yang digabung: **0**
- Record yang secara teknis masih belum terhubung: **3**

## 7. Alasan keputusan

1. **Parameter inti identik.** Ketiga record memiliki `DateTime`, koordinat, magnitudo, dan kedalaman yang sama persis dengan event kandidat. Selisih waktu 0 detik, selisih koordinat 0, selisih magnitudo 0, dan selisih kedalaman 0.
2. **Identitas deterministik sama.** Pipeline pilot membentuk `event_key` dari waktu, koordinat, dan magnitudo. Ketiga record menghasilkan `event_key` yang sama dengan event yang sudah ada, sehingga fungsi `event_identity()` menghasilkan `event_id` yang sama.
3. **Perbedaan teks bersifat deskriptif.** Pada FFB, `terkini` menyebut Tanimbar 201 km, sedangkan `dirasakan` menyebut Larat 60 km. Perbedaan ini adalah perbedaan titik rujukan dan format laporan, bukan perbedaan koordinat. Pada Gunungkidul, arah dan jarak tekstual berbeda 1 km, sedangkan koordinat tetap sama. Teks lokasi tidak dipakai sebagai bukti tunggal.
4. **Tidak ada kandidat event lain.** Tidak ada event dengan waktu atau koordinat yang sama selain ketiga pasangan tersebut.
5. **Tidak perlu event baru.** Karena identitas event sudah ada, menambahkan event baru justru akan menduplikasi kejadian.
6. **Tidak ada alasan untuk merge.** Event yang sudah ada tetap dipertahankan. Record `dirasakan` seharusnya menjadi dokumen pendukung, bukan event baru dan bukan pengganti event primer.
7. **Belum diubah karena tahap audit.** Perbaikan link memerlukan pembuatan baris `document` terlebih dahulu. Itu perubahan data dan berada di luar batas audit FIX 05.

## 8. Daftar record yang tetap belum terhubung

| Label | Event kandidat | Alasan belum terhubung |
|---|---|---|
| Oksibil | `EVT-BMKG-72D9473D8378` | Belum ada baris `document`; record hanya tersimpan di raw payload. |
| Tanimbar/FFB | `EVT-BMKG-FFB357F335AE` | Belum ada baris `document`; record hanya tersimpan di raw payload. |
| Gunungkidul | `EVT-BMKG-608A37F640B2` | Belum ada baris `document`; record hanya tersimpan di raw payload. |

Catatan: dua record Tanggamus juga tetap tidak terhubung, tetapi keduanya tidak memiliki event kandidat di dataset pilot. Keduanya berada di luar tiga record yang diaudit dan tidak boleh dibuatkan event tanpa bukti tambahan.

Semua 23 baris `document` yang sudah ada tetap terhubung; tidak ada dokumen lama yang menjadi orphan atau kehilangan link.

## 9. Rekomendasi perbaikan

1. **Materialisasi dokumen pada fix berikutnya.** Ubah ketiga record menjadi baris `document` dengan `document_source_id=bmkg_gempa_dirasakan`, `document_raw_payload_id=RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264`, URL feed + fragmen record, dan `document_external_id` deterministik. Jika memakai fungsi pipeline yang sama, kandidat `document_id` adalah:
   - Oksibil: `DOC-f887636094654d53`
   - Tanimbar/FFB: `DOC-cfd2f5df338e302d`
   - Gunungkidul: `DOC-57dbfb14c6cc3343`

   Ketiga ID tersebut belum ada di `document.csv`, sehingga tidak menimpa dokumen lama.
2. **Tambahkan link pendukung, bukan link primer.** Nilai yang direkomendasikan: `relation_type=reports`, `relation_direction=document_to_event`, `relevance=supporting`, `is_primary=tidak`, `relation_confidence=high`, `event_count_mentioned=1`, `link_status=active`. Link primer tetap pada dokumen `bmkg_gempa_terkini`.
3. **Simpan bukti pencocokan.** `relation_evidence` sebaiknya memuat waktu, koordinat, magnitudo, kedalaman, `event_key`, dan pernyataan bahwa teks lokasi hanya konteks, bukan bukti identitas.
4. **Pertimbangkan pemetaan `Dirasakan`.** Setelah link dibuat, nilai `Dirasakan` dapat dipetakan ke `event_attribute` atau assertion pendukung sesuai temuan `AUD-06`. Ini harus menjadi fix terpisah dan tidak boleh mengubah kategori atau scope.
5. **Perbaiki pemilihan record.** Jangan hanya memakai `parsed_items[:10]` jika record pendukung untuk event yang sudah ada berada di luar batas tersebut. Pilih record berdasarkan `event_key` atau tambahkan aturan yang mempertahankan record pendukung dari event terpilih.
6. **Tambahkan test regresi.** Test harus memastikan `event_identity()` deterministik, tidak ada `document_id` ganda, link menunjuk event valid, tidak ada event baru, dan tidak ada perubahan kategori/scope/baseline.
7. **Jangan merge atau hapus event.** Jika materialisasi dilakukan, validasi bahwa jumlah event tetap 20 dan `event_id` tidak berubah.

## 10. Integritas dan batas

Audit ini hanya membaca data. Tidak ada perubahan pada tabel, raw payload, baseline, atau output FIX 01 sampai FIX 04.

| Objek | SHA-256 | Status |
|---|---|---|
| Baseline `data/geohazard_news_final_20261101T150501Z.csv` | `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06` | tidak berubah |
| `document.csv` FIX 03 dan FIX 04 | `e4d8121c9bb36af103f5d10e8dcb2a3b5fd61347b120bbd29e0f185badacc930` | identik |
| `document_event_link.csv` FIX 03 dan FIX 04 | `e2320ef31cf1fad9e16ebf8e1da771f64ed3b6303dbc4e8e95fcf660073de071` | identik |
| `event.csv` | `dbfa6d732e5b66bd92adc783608e844b7b4c4ec471be3d0fd13db77cb51e4eff` | tidak berubah |
| `event_time.csv` | `81cbe69ad498f89eb29dcbf7711876a2cced9514b45f8efa50641ac6e977d0e4` | tidak berubah |
| `event_location.csv` | `3632c2fa22a1c399a2b6d407b6e9d39a501ee4bea1b2b9bf71aeff8aa96b59e9` | tidak berubah |
| `raw_payload.csv` | `49c9999322e405c7c612fd2ca764d409c341a13c46209c549d3db040859b4525` | tidak berubah |
| `raw/bmkg_gempa_dirasakan.xml` | `9b1bc264382d54c9b69471412159d1f96c05741598c4f39047bf430e64c2c47b` | tidak berubah |
| `raw/bmkg_gempa_terkini.xml` | `e5665e90cf097640eb5d9790536366ef6e4329c7f9dcd9c9170b44ea01673e7b` | tidak berubah |
| `raw/usgs_m45.atom` | `fbb7638a2198b07a9bdd1531b1b3712b4e14b662e1bc416086e3f04fb7b116f0` | tidak berubah |

## 11. Pengujian

Pengujian relevan yang dijalankan:

```text
.venv\Scripts\python.exe -m unittest test_geographic_review test_geographic_scope test_event_relation_candidates test_dataset_baseline
Ran 48 tests
OK
```

Full suite:

```text
.venv\Scripts\python.exe -m unittest discover -v
Ran 122 tests
FAILED (errors=1)
```

Satu error adalah error lama yang tidak terkait FIX 05:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

Tidak ada kegagalan pada test FIX 02, FIX 03, FIX 04, atau baseline.

## 12. Kesimpulan

Ketiga record `bmkg_gempa_dirasakan` memang berkaitan dengan event yang sudah ada:

- Oksibil -> `EVT-BMKG-72D9473D8378`
- Tanimbar/FFB -> `EVT-BMKG-FFB357F335AE`
- Gunungkidul -> `EVT-BMKG-608A37F640B2`

Hubungan ini didukung oleh waktu, koordinat, magnitudo, kedalaman, dan `event_key` deterministik yang identik. Tidak ada event baru yang diperlukan dan tidak ada alasan untuk menggabungkan event.

Namun ketiganya belum dapat dihubungkan secara teknis karena belum ada baris `document`. Sesuai batas audit, tidak ada perubahan data yang dilakukan. Rekomendasi berikutnya adalah materialisasi tiga dokumen pendukung dan penambahan link `supporting` pada fix terpisah, dengan validasi bahwa jumlah event, kategori, scope geografis, relasi lama, dan baseline tetap tidak berubah.
