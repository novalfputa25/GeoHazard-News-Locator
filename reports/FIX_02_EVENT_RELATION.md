# FIX 02 - Pencatatan Relasi Kandidat Duplikat BMKG-USGS

Tanggal: **2026-11-03**  
Fix ID: `FIX-EVENT-RELATION-20261103T053822Z`  
Sumber: `data/pilot/fixes/FIX-TSUNAMI-20261102T171637Z`  
Output: `data/pilot/fixes/FIX-EVENT-RELATION-20261103T053822Z`  
Status: **relasi kandidat tercatat; tidak ada merge, hapus event, atau perubahan baseline**

## 1. Tujuan dan batas

FIX 02 mencatat dua kandidat duplikat lintas sumber, BMKG dan USGS, ke tabel `event_relation`. Relasi ini hanya menyatakan bahwa kedua event kandidat saling terkait secara lokal. Relasi tidak menyatakan bahwa kedua event pasti merupakan kejadian fisik yang sama.

Batas yang dipertahankan:

- Tidak menghapus atau menggabungkan event.
- Tidak mengubah `event_id`, isi `event`, `raw_payload`, atau baseline.
- Tidak mengubah FIX 01 sebagai sumber.
- Tidak mengubah schema.
- Tidak mengklaim verifikasi katalog independen.
- Tidak menggunakan `same_event` atau `duplicate_of` karena bukti belum cukup untuk klaim tersebut.

## 2. Sumber dan output

| Item | Nilai |
|---|---|
| FIX 01 sumber | `data/pilot/fixes/FIX-TSUNAMI-20261102T171637Z` |
| SHA-256 manifest FIX 01 | `aaa5b2ab6c3a02f33574f256aa3f52721be323b52b65668a872dfcdc341eb6a2` |
| Run pilot asal | `data/pilot/runs/PILOT-20261102T110641Z` |
| Output FIX 02 | `data/pilot/fixes/FIX-EVENT-RELATION-20261103T053822Z` |
| Relasi sebelum | 0 |
| Relasi sesudah | 2 |
| Event sebelum/sesudah | 20 / 20 |
| `change_log` sebelum/sesudah | 373 / 375 |

File utama output:

- `tables/event_relation.csv`
- `tables/change_log.csv`
- `event_relation_fix_summary.csv`
- `event_relation_evidence.json`
- `event_relation_validation.csv`
- `fix_manifest.json`

## 3. Kandidat dan bukti

### 3.1 Tomohon

| Field | BMKG | USGS |
|---|---|---|
| `event_id` | `EVT-BMKG-5989CC896238` | `EVT-USGS-7000tuuy` |
| Waktu | `2026-11-02T08:13:10+00:00` | `2026-11-02T08:13:14+00:00` |
| Koordinat | `1.3100,124.8300` | `1.3920,124.6476` |
| Magnitudo | 5.3 | 5.1 |
| Kedalaman | 148.0 km | 196.65 km |
| Dokumen | `DOC-441dadaefbcb350a`, `DOC-d58a4f375995c665` | `DOC-03734fe8a96ac6d6` |
| Raw payload | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90`, `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | `RAW-usgs_m45-20261102T110641Z-fbb7638a` |

Selisih waktu 4 detik, jarak episentrum 22.232 km, selisih magnitudo 0.2, dan selisih kedalaman 48.65 km. Wilayah dan judul kedua sumber konsisten. BMKG juga memiliki laporan gempabumi dirasakan untuk wilayah Tomohon/Ternate/Minahasa.

### 3.2 Tanimbar

| Field | BMKG | USGS |
|---|---|---|
| `event_id` | `EVT-BMKG-8102A3842AA3` | `EVT-USGS-7000tusv` |
| Waktu | `2026-11-02T00:53:11+00:00` | `2026-11-02T00:53:10+00:00` |
| Koordinat | `-7.0800,130.0700` | `-6.9205,129.9514` |
| Magnitudo | 5.5 | 5.1 |
| Kedalaman | 130.0 km | 93.55 km |
| Dokumen | `DOC-fd54e30527cf02db`, `DOC-ee237cea966fd37d` | `DOC-83ae76fc3aed7f4d` |
| Raw payload | `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90`, `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | `RAW-usgs_m45-20261102T110641Z-fbb7638a` |

Selisih waktu 1 detik, jarak episentrum 22.043 km, selisih magnitudo 0.4, dan selisih kedalaman 36.45 km. Wilayah dan judul kedua sumber konsisten. BMKG juga memiliki laporan gempabumi dirasakan di Saumlaki.

### 3.3 Hash raw payload

| Raw payload | SHA-256 |
|---|---|
| `RAW-bmkg_gempa_terkini-20261102T110641Z-e5665e90` | `e5665e90cf097640eb5d9790536366ef6e4329c7f9dcd9c9170b44ea01673e7b` |
| `RAW-bmkg_gempa_dirasakan-20261102T110641Z-9b1bc264` | `9b1bc264382d54c9b69471412159d1f96c05741598c4f39047bf430e64c2c47b` |
| `RAW-usgs_m45-20261102T110641Z-fbb7638a` | `fbb7638a2198b07a9bdd1531b1b3712b4e14b662e1bc416086e3f04fb7b116f0` |

## 4. Penilaian

Penilaian lokal untuk kedua pasangan: **`likely_same_event`**.

Dasar penilaian:

- Waktu hampir identik, selisih 1-4 detik.
- Episentrum berdekatan, sekitar 22 km.
- Wilayah dan judul kedua sumber konsisten.
- BMKG memiliki laporan gempabumi dirasakan yang mendukung konteks wilayah dan waktu.

Alasan tidak memakai `confirmed_same_event`:

- Tidak ada verifikasi katalog independen.
- Tidak ada pencocokan native ID lintas sumber; BMKG tidak memiliki native event ID pada data ini.
- Selisih kedalaman cukup besar, 36.45 km dan 48.65 km.
- Bukti lokal dari dua feed tidak cukup untuk memastikan identitas fisik kejadian.

Karena itu, relasi dicatat sebagai kandidat, bukan keputusan final duplikat.

## 5. Implementasi relasi

Schema `event_relation` yang tersedia tidak memiliki field khusus assessment, reason, atau source refs. FIX 02 tidak mengubah schema. Nilai yang dipakai:

| Field | Nilai |
|---|---|
| `event_relation_type` | `related_to` |
| `event_relation_confidence` | `medium` |
| `event_relation_evidence` | Assessment, alasan, metrik, referensi dokumen/raw payload, hash, dan caveat |
| `created_at` | `2026-11-03T05:38:22.137592+00:00` |

Relasi yang dibuat:

| Pair | `event_relation_id` | From | To |
|---|---|---|---|
| Tanimbar | `EREL-058FFADAE49A4801` | `EVT-BMKG-8102A3842AA3` | `EVT-USGS-7000tusv` |
| Tomohon | `EREL-6947058A57B66894` | `EVT-BMKG-5989CC896238` | `EVT-USGS-7000tuuy` |

Setiap evidence memuat:

- `candidate_duplicate=true`
- `assessment=likely_same_event`
- `relation_type=related_to`
- `no_merge=true`
- `confirmed_same_event=false`
- Metrik waktu, jarak, koordinat, magnitudo, dan kedalaman
- `reason=...`
- `source_refs=...` berisi `BMKG_DOC`, `BMKG_RAW`, `USGS_DOC`, `USGS_RAW`, dan `RAW_SHA256`
- `caveat=...` yang menyatakan bukti lokal bukan verifikasi katalog independen

`event_relation_type=related_to` dipilih karena netral. Nilai `same_event` dan `duplicate_of` tidak dipakai untuk menghindari klaim yang belum terbukti.

## 6. Invariant yang diverifikasi

Semua pemeriksaan pada manifest bernilai `true`:

| Pemeriksaan | Status |
|---|---|
| `event_count_unchanged` | Lulus |
| `event_ids_unchanged` | Lulus |
| `event_table_unchanged` | Lulus |
| `no_event_deleted` | Lulus |
| `no_merge` | Lulus |
| `raw_payload_table_unchanged` | Lulus |
| `raw_payload_files_unchanged` | Lulus |
| `baseline_unchanged` | Lulus |
| `source_fix_relations_were_empty` | Lulus |
| `relations_point_to_existing_events` | Lulus |
| `relation_validation_no_p0` | Lulus |

Hash utama:

| Objek | SHA-256 |
|---|---|
| Baseline | `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06` |
| `event.csv` sumber dan output | `dbfa6d732e5b66bd92adc783608e844b7b4c4ec471be3d0fd13db77cb51e4eff` |
| `event_relation.csv` output | `f5b8c497a2ddae8b82351de385c219148a91716a7c9c94f888d8e8f7fb702eae` |
| `change_log.csv` output | `f2d0e8afbbeec4b413e835ee2d2bb0b33a98b744e93b9e7a94d5ccbf1038d970` |

Baseline tetap 787 baris x 51 kolom. Tidak ada event yang dihapus, digabung, atau diberi `event_group_id`. Dua baris baru di `change_log` hanya mencatat `create` pada `event_relation`.

## 7. Validasi dan test

Validasi relasi:

| Aturan | Tingkat | Hasil | Catatan |
|---|---|---|---|
| `R-REL-01` | P0 | Lulus | 2 relasi; ID unik; FK valid; tidak ada relasi ke diri sendiri |
| `R-REL-02` | P1 | Lulus | 2 relasi memiliki tipe, confidence, dan bukti |
| `R-REL-03` | P1 | Lulus | Tidak ada siklus atau pertentangan grup |

Test FIX 02:

```powershell
& .venv\Scripts\python.exe -m unittest -v test_event_relation_candidates
```

Hasil: **17/17 test lulus**.

Cakupan test mencakup dua pasangan yang diharapkan, metrik waktu/jarak/magnitudo/kedalaman, penilaian `likely_same_event` yang tidak diklaim confirmed, evidence dan alasan, event tetap ada, ID event tidak berubah, tidak ada event dihapus, tidak ada merge, relasi menunjuk event valid, baseline tidak berubah, raw payload tidak berubah, `change_log` hanya menambah relasi, validasi `R-REL` lulus, dan FIX 01 tidak termutasi.

Full suite dengan virtual environment yang sama: **93 test lulus, 1 error tidak terkait FIX 02** pada `test_scraper` dengan `ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'`. Error tersebut berasal dari modul scraper yang tidak terkait dan tidak menyentuh file atau output FIX 02.

## 8. Keterbatasan dan risiko

1. Relasi ini adalah pencatatan kandidat, bukan penutupan review duplikat.
2. `likely_same_event` hanya tersimpan di `event_relation_evidence`; schema belum memiliki enum assessment khusus.
3. Tidak ada verifikasi katalog independen atau pencocokan native ID lintas sumber.
4. Selisih kedalaman 36.45 km dan 48.65 km perlu diperhitungkan dalam review lanjutan.
5. Relasi dapat direvisi menjadi `same_event`, `duplicate_of`, atau dibatalkan bila bukti independen tersedia.
6. Full suite masih memiliki satu error terpisah di `test_scraper`; error ini tidak menghambat FIX 02.

## 9. Rekomendasi schema minimum

Schema sebaiknya ditambah pada versi berikutnya agar assessment tidak hanya berada di teks evidence:

- `event_relation_assessment` enum: `possible_same_event`, `likely_same_event`, `unresolved`, `likely_distinct_event`, `confirmed_same_event`.
- `event_relation_reason` text: alasan penilaian yang terpisah dari bukti mentah.
- `event_relation_source_refs` text/JSON: daftar event, dokumen, raw payload, dan hash.

Perubahan tersebut belum diterapkan pada FIX 02.

## 10. Kesimpulan

FIX 02 berhasil mencatat dua relasi kandidat duplikat BMKG-USGS tanpa merge, hapus event, perubahan ID, perubahan raw payload, atau perubahan baseline. Kedua pasangan dinilai `likely_same_event` dengan confidence `medium` dan tipe relasi netral `related_to`. Dua event BMKG dan dua event USGS tetap tersimpan terpisah.

Status: **selesai untuk pencatatan relasi kandidat; review duplikat final masih memerlukan bukti independen atau keputusan manual**.

