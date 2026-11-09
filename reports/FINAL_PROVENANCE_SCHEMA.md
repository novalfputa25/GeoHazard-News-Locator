# Final Provenance Schema — GeoHazard News Locator

Tanggal: **2026-11-02**  
Versi skema: **1.0.0**  
Status: **desain final; belum ada migrasi data, database, atau perubahan baseline**  
Baseline: `data/geohazard_news_final_20261101T150501Z.csv`  
SHA-256 baseline: `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06`  
Field dictionary: `docs/PROVENANCE_FIELD_DICTIONARY.csv` (183 field, 14 entitas)  
Aturan validasi: `docs/PROVENANCE_VALIDATION_RULES.md` (59 aturan)

## 1. Tujuan dan batas

Skema ini memisahkan **sumber**, **payload mentah**, **dokumen**, **kejadian**, **waktu**, **lokasi**, **kategori**, **relasi**, **klaim**, **verifikasi**, dan **riwayat perubahan**. Tujuannya agar data dari feed resmi, berita, peta risiko, publikasi, dan data historis dapat disatukan tanpa mengaburkan asal-usul atau tingkat kepastiannya.

Batas dokumen ini:

- Tidak mengubah baseline, `feeds.py`, scraper, atau pipeline.
- Tidak membuat database/backend/frontend.
- Tidak mengaktifkan sumber `PERLU_IZIN`.
- Tidak menambah kategori di luar 8 kategori resmi + `Lainnya`.
- Tidak mengisi data yang tidak memiliki bukti.
- Tidak mengklaim cakupan 8 kategori sudah lengkap.

## 2. Keputusan desain utama

1. **Model berlapis, bukan satu tabel datar.** Satu entitas tidak boleh mencampur sumber, dokumen, kejadian, dan klaim.
2. **Sumber dan dokumen dipisahkan.** `source` adalah sumber/feed terdaftar; `document` adalah artikel, laporan, halaman kejadian, peta, atau publikasi.
3. **Dokumen dan kejadian many-to-many.** Satu artikel dapat membahas beberapa kejadian; satu kejadian dapat memiliki banyak dokumen.
4. **Kejadian tidak sama dengan artikel.** `event_id` hanya untuk kejadian; `document_id` hanya untuk dokumen.
5. **Kategori adalah penetapan pada kejadian.** Kategori tidak disimpan sebagai label tunggal pada dokumen.
6. **Waktu dan lokasi memiliki provenance sendiri.** Nilai tidak boleh ada tanpa dasar, presisi, dan status yang jelas.
7. **Konflik tidak ditimpa.** Klaim dari sumber yang berbeda disimpan di `event_assertion`; nilai terpilih dan alasan dicatat.
8. **Data historis tidak dipalsukan.** Bila `source_id`, raw payload, atau run tidak diketahui, gunakan status `legacy_incomplete`; jangan membuat ID baru.
9. **Perubahan bersifat append-only.** `change_log` mencatat perubahan; tidak ada silent update.
10. **Kategori tetap 8 + fallback.** `Lainnya` hanya fallback; `category_scope` membedakan di luar cakupan dan belum terklasifikasi.

## 3. Model entitas dan kardinalitas

| Entitas | Isi | Kunci utama | Relasi utama |
|---|---|---|---|
| `source` | Sumber/feed terdaftar, status akses, lisensi, peran | `source_id` | 1:N `raw_payload`; 1:N `document`; 1:N `event` sebagai sumber utama |
| `raw_payload` | Snapshot mentah immutable dan hash | `raw_payload_id` | 1:N `document`; N:1 `source` |
| `document` | Artikel/laporan/halaman/peta yang dinormalisasi | `document_id` | N:1 `source` opsional; N:1 `raw_payload` opsional; M:N `event` |
| `event` | Kejadian yang diidentifikasi dan dinormalisasi | `event_id` | 1:N `event_time`, `event_location`, `category`, `event_assertion`, `event_attribute`; M:N `document`; 1:N `event_relation` |
| `event_time` | Waktu kejadian beserta presisi, jenis, bukti | `event_time_id` | N:1 `event` |
| `location_mention` | Penyebutan lokasi di dalam dokumen | `location_mention_id` | N:1 `document`; N:1 `event` opsional |
| `event_location` | Lokasi kejadian yang sudah diresolusi | `event_location_id` | N:1 `event` |
| `category` | Penetapan kategori pada kejadian | `category_assignment_id` | N:1 `event` |
| `document_event_link` | Relasi dokumen-kejadian | `link_id` | N:1 `document`; N:1 `event` |
| `event_assertion` | Klaim nilai dari sumber/dokumen | `assertion_id` | N:1 `event`; N:1 `document` opsional; N:1 `source` opsional |
| `event_relation` | Relasi antar kejadian | `event_relation_id` | N:1 `event` (asal dan tujuan) |
| `verification` | Catatan verifikasi polimorfik | `verification_id` | target_type + target_id |
| `change_log` | Riwayat perubahan append-only | `change_id` | target_type + target_id |
| `event_attribute` | Atribut kejadian terpilih (magnitudo, kedalaman, level) | `event_attribute_id` | N:1 `event`; N:1 `source` opsional |

Aturan kardinalitas:

- `document_event_link` harus many-to-many; jangan memaksa satu `event_id` di `document`.
- `event_group_id` boleh dipakai untuk mengelompokkan beberapa erupsi/kejadian terkait, tetapi bukan pengganti `event_id`.
- `event_assertion` menyimpan klaim; `event_attribute` menyimpan nilai terpilih yang sudah melalui aturan resolusi.
- `verification` dan `change_log` memakai pasangan `target_type` + `target_id`; target harus valid dan tidak boleh yatim.

## 4. Kebijakan ID dan identitas

| Objek | Aturan ID | Contoh |
|---|---|---|
| `source_id` | Hanya dari `docs/MASTER_SOURCE_REGISTER.csv`; tidak ada ID sintetis | `bmkg_gempa_terkini` |
| `raw_payload_id` | Turunan sumber + waktu ambil + hash; immutable | `RAW-bmkg_gempa_terkini-20261102T090000Z-0123abcd` |
| `document_id` | Turunan URL kanonik/ID dokumen; bukan nomor baris | `DOC-5e8944f8dbe047af` |
| `event_id` | Native ID bila ada; jika tidak, kandidat stabil dari sumber+waktu+lokasi | `EVT-USGS-...` atau `EVT-CAND-...` |
| `event_group_id` | Kelompok kejadian terkait; bukan pengganti event | `EGRP-KRAKATAU-20261018` |
| ID lain | Prefix entitas + ID unik; tidak boleh dipakai ulang | `TIME-...`, `LOCE-...`, `LINK-...` |

Larangan:

- Nomor baris, indeks CSV, atau urutan scrape tidak boleh menjadi ID.
- Label `sumber` tidak boleh diubah menjadi `source_id` tanpa pemetaan dan bukti.
- `document_id` tidak boleh dipakai sebagai `event_id`.
- Satu artikel tidak otomatis menghasilkan satu event.

## 5. Kontrak status dan vocabulary

Nilai status yang dipakai dalam skema:

| Field | Nilai yang diizinkan |
|---|---|
| `source_registry_status` | `TERVERIFIKASI_AKTIF`; `TERVERIFIKASI_MANUAL`; `PERLU_IZIN`; `BELUM_TERSEDIA`; `TIDAK_SESUAI` |
| `source_type` / `document_source_type` | `official`; `news`; `aggregator`; `risk_map`; `publication`; `gazetteer`; `unknown` |
| `source_role` / `document_source_role` | `primary_official`; `supporting_official`; `news_support`; `aggregator_support`; `risk_context`; `reference`; `unknown` |
| `source_data_type` | `event_feed`; `report`; `map`; `article`; `gazetteer`; `mixed`; `unknown` |
| `document_source_identity_status` | `registered`; `legacy_label_only`; `unresolved` |
| `document_provenance_status` | `complete`; `partial`; `legacy_incomplete`; `unresolved` |
| `raw_payload_status` | `stored`; `missing`; `restricted`; `not_applicable` |
| `event_status` | `candidate`; `reported`; `confirmed`; `disputed`; `retracted`; `unknown` |
| `event_verification_status` | `unverified`; `source_asserted`; `corroborated`; `official`; `disputed`; `rejected`; `not_applicable` |
| `event_verification_level` | `none`; `low`; `medium`; `high`; `official` |
| `event_time_status` | `extracted`; `date_only`; `manual_review`; `unknown`; `not_applicable` |
| `event_time_kind` | `actual`; `estimated`; `forecast`; `nowcast`; `unknown` |
| `event_time_precision` | `second`; `minute`; `hour`; `day`; `month`; `year`; `range`; `unknown` |
| `event_time_basis` | `official_field`; `official_document`; `news_text`; `manual_review`; `not_available` |
| `coordinate_status` | `not_available`; `source_coordinate`; `reported_coordinate`; `approximate`; `verified`; `rejected` |
| `coordinate_source` | `source_api`; `source_page`; `source_document`; `manual`; `derived`; `unknown` |
| `category_name` | 8 kategori resmi + `Lainnya` |
| `category_scope` | `in_scope`; `out_of_scope`; `unclassified` |
| `category_basis` | `official_metadata`; `source_title`; `source_body`; `manual_review`; `legacy_label`; `unknown` |
| `relation_type` | `reports`; `confirms`; `corroborates`; `disputes`; `mentions`; `follows_up`; `duplicate_of`; `corrects`; `contextualizes`; `derived_from` |
| `event_relation_type` | `same_event`; `component_of`; `secondary_hazard_of`; `duplicate_of`; `supersedes`; `related_to` |
| `assertion_status` | `proposed`; `accepted`; `rejected`; `superseded`; `conflict` |
| `change_type` | `create`; `update`; `review`; `merge`; `split`; `link`; `unlink`; `status_change`; `retract`; `no_op` |

Nilai di luar daftar ini harus ditolak oleh validasi, kecuali ada versi skema baru yang disetujui.

## 6. Aturan sumber

1. `source` hanya berisi sumber yang tercatat di register.
2. `TERVERIFIKASI_AKTIF` boleh dipakai otomatis dengan batas laju dan robots.
3. `TERVERIFIKASI_MANUAL` hanya untuk pengambilan/verifikasi manual; bukan izin otomatisasi.
4. `PERLU_IZIN`, `BELUM_TERSEDIA`, dan `TIDAK_SESUAI` tidak boleh menjadi sumber aktif.
5. `source_type` dan `source_role` harus konsisten:
   - `news` tidak boleh `primary_official`;
   - `risk_map`/`publication` tidak boleh `event_feed`;
   - `official` tidak otomatis berarti seluruh field terverifikasi.
6. `source_license_status=verified` hanya boleh bila ada dasar lisensi yang dicatat. HTTP 200, robots `allowed`, atau akses publik bukan bukti lisensi.
7. Data historis dengan label sumber saja tidak boleh diberi `source_id` tanpa pemetaan dan bukti.

## 7. Aturan payload mentah dan dokumen

- Dokumen baru wajib memiliki `raw_payload_id`, `run_id`, `document_retrieved_at`, dan hash payload.
- Payload mentah bersifat immutable; perubahan data tidak boleh menimpa snapshot lama.
- `document_url_canonical` dipakai untuk deduplikasi, tetapi parameter identitas kejadian tidak boleh dihapus.
- `document_source_identity_status=registered` mewajibkan `document_source_id` valid.
- `legacy_label_only` mewajibkan label sumber dan `document_source_id=NULL`.
- `document_provenance_status=complete` hanya boleh bila source, raw payload, waktu ambil, dan run tersedia.
- Data baseline yang tidak memiliki raw/run harus memakai `legacy_incomplete`.

## 8. Aturan kejadian, relasi, dan konflik

- `event_id` hanya diberikan pada kejadian yang dapat dibedakan.
- Berita tunggal tidak boleh otomatis menjadi `confirmed`.
- `event_status=confirmed` memerlukan sumber resmi atau bukti korroborasi yang dicatat.
- `event_verification_status=official` hanya untuk rekaman resmi atau keputusan manual yang menyebut dasar resminya.
- `corroborated` memerlukan minimal dua sumber independen.
- Artikel yang menyebut beberapa kejadian harus memakai beberapa `document_event_link` atau satu link dengan `event_count_mentioned>1`; jangan memecah event tanpa bukti.
- `event_group_id` mengelompokkan, bukan menggabungkan identitas event.
- Klaim yang bertentangan disimpan di `event_assertion`; nilai yang dipilih dicatat di `event_attribute` atau field event yang relevan, beserta alasan.
- Tsunami sebagai potensi pada gempa tidak otomatis menjadi event tsunami terpisah.
- Potensi tsunami BMKG disimpan sebagai `event_attribute.attribute_name=bmkg_potential_text` untuk nilai mentah dan `event_attribute.attribute_name=tsunami_potential_status` untuk status `positive|negative|unknown`.
- Nama atribut `tsunami_potential` tidak dipakai karena mencampur teks negasi dengan flag potensi. Status `unknown` tidak boleh diperlakukan sebagai `negative` atau sebagai bukti ketiadaan tsunami.
- Duplikat dokumen tidak otomatis menjadi duplikat event; deduplikasi event memakai native ID atau kunci stabil.

## 9. Aturan waktu

1. `document_published_at` bukan `event_time`.
2. `event_time` wajib memiliki `event_time_basis` dan `event_time_evidence`.
3. Jika waktu tidak diketahui, `event_time=NULL` dan status `unknown`/`not_applicable`; jangan menebak.
4. Tanggal saja boleh disimpan bila `event_time_precision=day`; tidak boleh diberi jam atau offset palsu.
5. `nowcast`, `forecast`, dan `estimated` tidak boleh diperlakukan sebagai aktual.
6. Kandidat seperti “Minggu (18/10)” tanpa tahun harus berstatus `manual_review` dan disimpan di `event_time_candidate_text`.
7. `event_time_timezone` wajib bila waktu memiliki jam; gunakan zona IANA.
8. Rentang waktu harus memenuhi `start <= end`.

## 10. Aturan lokasi dan koordinat

- `location_mention` mencatat penyebutan di dokumen; `event_location` mencatat lokasi kejadian yang diresolusi.
- Rujukan administratif belum menjadi lokasi kejadian.
- `latitude` dan `longitude` harus diisi bersama; rentang latitude -90..90 dan longitude -180..180.
- Koordinat wajib memiliki `coordinate_source`, `coordinate_status`, `coordinate_precision`, dan `coordinate_confidence`.
- `source_coordinate` bukan `verified`.
- `verified` memerlukan bukti, waktu verifikasi, dan verifier.
- Koordinat di luar Indonesia boleh disimpan, tetapi harus ditandai dan tidak dipakai sebagai klaim kejadian Indonesia.
- Geocoding dari judul tanpa verifikasi tidak boleh menghasilkan `event_location` final.

## 11. Aturan kategori

- Hanya 8 kategori resmi + `Lainnya`.
- `category_scope=in_scope` hanya untuk 8 kategori resmi.
- Karhutla, cuaca ekstrem, dan topik non-geologi tidak boleh dipaksa menjadi kategori geologi.
- `Lainnya` tidak otomatis berarti `in_scope`; gunakan `out_of_scope` atau `unclassified`.
- Perubahan kategori harus memiliki `category_original`, alasan, reviewer, dan waktu review.
- Kategori tidak boleh ditetapkan hanya dari nama sumber.

## 12. Verifikasi, perubahan, dan data historis

- `verification` harus menunjuk target yang ada dan mencatat status, level, metode, dasar, serta jumlah sumber.
- Verifikasi manual wajib memiliki `verified_at` dan `verified_by` (peran, bukan data pribadi).
- `change_log` wajib mencatat target, jenis perubahan, waktu, pelaku, alasan, dan versi skema.
- Update field wajib mencatat nilai lama dan baru.
- Penghapusan data tidak dilakukan; gunakan status `retracted`, `superseded`, atau `rejected`.
- Data historis harus mempertahankan `document_legacy_row_ref` untuk audit, tetapi referensi baris bukan identitas.
- Baseline tidak boleh ditimpa; perubahan harus menghasilkan file baru dan manifest.

## 13. Pemetaan baseline ke skema

| Field baseline | Tujuan skema | Catatan |
|---|---|---|
| `judul` | `document.document_title` | Bukan `event_title` otomatis |
| `sumber` | `document.document_source_label` + snapshot `document_source_type` | Jangan mengarang `source_id` |
| `url` | `document.document_url` / `document_url_canonical` | URL unik baseline dipertahankan |
| `published_time` | `document.document_published_at` | Bukan `event_time` |
| `event_time` | `event_time.event_time` | Hanya bila bukti dan status mendukung |
| `event_time_status` | `event_time.event_time_status` | `terekstrak` → `extracted`; `tanggal_saja` → `date_only`; `perlu_review` → `manual_review` |
| `event_time_basis` | `event_time.event_time_basis` | Perlu pemetaan eksplisit per nilai lama |
| `provinsi`..`alamat_detail` | `event_location` dan/atau `location_mention` | Rujukan administratif belum tentu lokasi kejadian |
| `latitude`, `longitude` | `event_location` | Wajib status/sumber/presisi |
| `kategori` | `category.category_name` | `Lainnya` perlu `category_scope` |
| `status_cakupan` | `category.category_scope` | `dalam_8_kategori` → `in_scope`; lainnya dipetakan eksplisit |
| `duplikat_judul`, `duplikat_isi`, `duplikat_url` | Keputusan link/dedup dan catatan audit | Jangan menghapus baris |
| `catatan_*` | `document_notes` atau `change_log` | Catatan bukan pengganti bukti |

Catatan penting:

- Baseline tidak memiliki `source_id`, `collected_at`, `run_id`, `raw_payload`, atau `license`; karena itu tidak boleh dimigrasikan sebagai `complete`.
- `record_id` tidak dipakai sebagai identitas baru. Identitas dokumen memakai `document_id`; identitas kejadian memakai `event_id`.
- Nomor baris baseline hanya boleh disimpan sebagai `document_legacy_row_ref`.

## 14. Contoh record

Contoh berikut memakai nilai faktual dari baseline. ID contoh adalah ID kandidat yang dapat diturunkan secara stabil; bukan ID resmi sumber.

### 14.1 Kejadian resmi BMKG

Record: data index 9, CSV line 10, sumber label `BMKG`.

```json
{
  "document": {
    "document_id": "DOC-5e8944f8dbe047af",
    "document_type": "official_event_record",
    "document_source_id": null,
    "document_source_label": "BMKG",
    "document_source_identity_status": "legacy_label_only",
    "document_source_type": "official",
    "document_source_role": "primary_official",
    "document_url": "https://www.bmkg.go.id/gempabumi/?t=2026-10-18T08%3A02%3A46%2B00%3A00&lat=8.14+LS&lon=120.29+BT&mag=4.1",
    "document_title": "Gempa M4.1 Pusat gempa berada di laut 56 km utara Ruteng",
    "document_published_at": "2026-10-18T08:02:46+00:00",
    "document_retrieved_at": null,
    "document_run_id": null,
    "document_provenance_status": "legacy_incomplete",
    "document_legacy_row_ref": "data-index:9"
  },
  "event": {
    "event_id": "EVT-CAND-BMKG-20261018T080246Z-M4.1-RUTENG",
    "event_group_id": null,
    "event_source_native_id": null,
    "event_primary_source_id": null,
    "event_title": "Gempa M4.1 di utara Ruteng",
    "event_status": "confirmed",
    "event_verification_status": "official",
    "event_verification_level": "official",
    "event_first_reported_at": null,
    "event_last_updated_at": null,
    "event_notes": "Halaman kejadian resmi BMKG; feed/run asal tidak tersimpan pada baseline."
  },
  "event_time": {
    "event_time_id": "TIME-5e8944f8dbe047af",
    "event_id": "EVT-CAND-BMKG-20261018T080246Z-M4.1-RUTENG",
    "event_time": "2026-10-18T15:02:46+07:00",
    "event_time_precision": "second",
    "event_time_kind": "actual",
    "event_time_status": "extracted",
    "event_time_basis": "official_document",
    "event_time_evidence": "Tanggal: 18 Okt 2026 15:02:46 WIB",
    "event_time_timezone": "Asia/Jakarta",
    "event_time_confidence": "high"
  },
  "event_location": {
    "event_location_id": "LOCE-5e8944f8dbe047af",
    "event_id": "EVT-CAND-BMKG-20261018T080246Z-M4.1-RUTENG",
    "location_name": "Pusat gempa di laut 56 km utara Ruteng",
    "location_role": "epicenter",
    "admin_province": "Nusa Tenggara Timur",
    "admin_kabupaten_kota": "Kabupaten Manggarai",
    "latitude": "-8.14",
    "longitude": "120.29",
    "coordinate_source": "source_page",
    "coordinate_status": "source_coordinate",
    "coordinate_precision": "point",
    "coordinate_confidence": "medium",
    "coordinate_verified_at": null,
    "coordinate_verified_by": null,
    "is_inside_indonesia": "ya",
    "location_notes": "Koordinat berasal dari parameter URL BMKG; belum diverifikasi manual."
  },
  "category": {
    "category_assignment_id": "CAT-5e8944f8dbe047af",
    "event_id": "EVT-CAND-BMKG-20261018T080246Z-M4.1-RUTENG",
    "category_name": "Gempabumi",
    "category_rank": "primary",
    "category_scope": "in_scope",
    "category_basis": "source_title",
    "category_confidence": "high",
    "category_review_status": "not_reviewed",
    "category_original": "Gempa Bumi"
  },
  "document_event_link": {
    "link_id": "LINK-5e8944f8dbe047af",
    "document_id": "DOC-5e8944f8dbe047af",
    "event_id": "EVT-CAND-BMKG-20261018T080246Z-M4.1-RUTENG",
    "relation_type": "reports",
    "relation_direction": "document_to_event",
    "relevance": "primary",
    "is_primary": "ya",
    "relation_confidence": "high",
    "event_count_mentioned": 1,
    "link_status": "active"
  },
  "verification": {
    "verification_id": "VER-5e8944f8dbe047af",
    "target_type": "event",
    "target_id": "EVT-CAND-BMKG-20261018T080246Z-M4.1-RUTENG",
    "verification_status": "official",
    "verification_level": "official",
    "verification_basis": "Rekaman kejadian resmi BMKG; feed/run tidak tersimpan.",
    "verification_source_count": 1,
    "verification_method": "official_record",
    "verified_at": null,
    "verified_by": null
  }
}
```

Penjelasan: status `official` mengikuti jenis rekaman BMKG, sedangkan `legacy_incomplete` menyatakan bahwa feed, run, dan payload mentah tidak dapat dilacak. Keduanya tidak saling menggantikan.

### 14.2 Berita media

Record: data index 325, sumber label `CNN Indonesia`.

```json
{
  "document": {
    "document_id": "DOC-95b7c1a7aa99d41a",
    "document_type": "news_article",
    "document_source_id": null,
    "document_source_label": "CNN Indonesia",
    "document_source_identity_status": "legacy_label_only",
    "document_source_type": "news",
    "document_source_role": "news_support",
    "document_url": "https://www.cnnindonesia.com/nasional/20261018143524-20-1416729/gunung-anak-krakatau-tiga-kali-erupsi-minggu-siang",
    "document_title": "Gunung Anak Krakatau Tiga Kali Erupsi Minggu Siang",
    "document_published_at": "2026-10-18T14:41:20+07:00",
    "document_retrieved_at": null,
    "document_run_id": null,
    "document_provenance_status": "legacy_incomplete",
    "document_legacy_row_ref": "data-index:325"
  },
  "event": {
    "event_id": "EVT-CAND-KRAKATAU-20261018-A",
    "event_group_id": "EGRP-KRAKATAU-20261018",
    "event_source_native_id": null,
    "event_primary_source_id": null,
    "event_title": "Erupsi Anak Krakatau 18 Oktober 2026",
    "event_status": "candidate",
    "event_verification_status": "source_asserted",
    "event_verification_level": "medium",
    "event_first_reported_at": null,
    "event_last_updated_at": null,
    "event_notes": "Artikel menyebut tiga kali erupsi; jangan otomatis memecah menjadi tiga event tanpa bukti."
  },
  "event_time": {
    "event_time_id": "TIME-95b7c1a7aa99d41a",
    "event_id": "EVT-CAND-KRAKATAU-20261018-A",
    "event_time": "2026-10-18",
    "event_time_precision": "day",
    "event_time_kind": "actual",
    "event_time_status": "date_only",
    "event_time_basis": "news_text",
    "event_time_evidence": "Gunung Anak Krakatau erupsi pada 18 Oktober 2026, dengan kolom abu mencapai 500 meter.",
    "event_time_timezone": null,
    "event_time_confidence": "medium"
  },
  "location_mention": {
    "location_mention_id": "LOCM-95b7c1a7aa99d41a",
    "document_id": "DOC-95b7c1a7aa99d41a",
    "linked_event_id": "EVT-CAND-KRAKATAU-20261018-A",
    "mention_text": "Gunung Anak Krakatau",
    "mention_normalized": "Gunung Anak Krakatau",
    "mention_role": "event_location",
    "mention_status": "normalized",
    "mention_confidence": "medium",
    "mention_evidence": "Judul: Gunung Anak Krakatau Tiga Kali Erupsi Minggu Siang"
  },
  "category": {
    "category_assignment_id": "CAT-95b7c1a7aa99d41a",
    "event_id": "EVT-CAND-KRAKATAU-20261018-A",
    "category_name": "Gunungapi",
    "category_rank": "primary",
    "category_scope": "in_scope",
    "category_basis": "source_title",
    "category_confidence": "high",
    "category_review_status": "not_reviewed",
    "category_original": "Gunung Api"
  },
  "document_event_link": {
    "link_id": "LINK-95b7c1a7aa99d41a",
    "document_id": "DOC-95b7c1a7aa99d41a",
    "event_id": "EVT-CAND-KRAKATAU-20261018-A",
    "relation_type": "reports",
    "relation_direction": "document_to_event",
    "relevance": "primary",
    "is_primary": "ya",
    "relation_confidence": "medium",
    "event_count_mentioned": 3,
    "link_status": "active"
  },
  "verification": {
    "verification_id": "VER-95b7c1a7aa99d41a",
    "target_type": "event",
    "target_id": "EVT-CAND-KRAKATAU-20261018-A",
    "verification_status": "source_asserted",
    "verification_level": "medium",
    "verification_basis": "Artikel CNN Indonesia; belum dikorroborasi sumber resmi.",
    "verification_source_count": 1,
    "verification_method": "source_check",
    "verified_at": null,
    "verified_by": null
  }
}
```

Penjelasan: `event_count_mentioned=3` mencatat isi artikel, bukan tiga event. Jika kelak ketiga erupsi dapat dipisahkan dengan bukti, buat event individual dan `event_relation` yang sesuai.

### 14.3 Data historis dengan waktu belum pasti

Record: data index 643, sumber label `Media Indonesia`.

```json
{
  "document": {
    "document_id": "DOC-a23ef66a38b0fe4d",
    "document_type": "news_article",
    "document_source_id": null,
    "document_source_label": "Media Indonesia",
    "document_source_identity_status": "legacy_label_only",
    "document_source_type": "news",
    "document_source_role": "news_support",
    "document_url": "https://mediaindonesia.com/nusantara/946006/gunung-anak-krakatau-erupsi-bmkg-pantau-sebaran-abu-vulkanik-via-satelit",
    "document_title": "Gunung Anak Krakatau Erupsi, BMKG Pantau Sebaran Abu Vulkanik via Satelit",
    "document_published_at": "2026-10-19T10:57:00+07:00",
    "document_retrieved_at": null,
    "document_run_id": null,
    "document_provenance_status": "legacy_incomplete",
    "document_legacy_row_ref": "data-index:643"
  },
  "event": {
    "event_id": "EVT-CAND-KRAKATAU-20261018-B",
    "event_group_id": "EGRP-KRAKATAU-20261018",
    "event_source_native_id": null,
    "event_primary_source_id": null,
    "event_title": "Erupsi Anak Krakatau 18 Oktober 2026 (tanggal perlu review)",
    "event_status": "candidate",
    "event_verification_status": "source_asserted",
    "event_verification_level": "low",
    "event_first_reported_at": null,
    "event_last_updated_at": null,
    "event_notes": "Tanggal 'Minggu (18/10)' tidak memiliki tahun eksplisit; jangan mengisi event_time dari published_time."
  },
  "event_time": {
    "event_time_id": "TIME-a23ef66a38b0fe4d",
    "event_id": "EVT-CAND-KRAKATAU-20261018-B",
    "event_time": null,
    "event_time_precision": "day",
    "event_time_kind": "unknown",
    "event_time_status": "manual_review",
    "event_time_basis": "manual_review",
    "event_time_evidence": "Gunung Anak Krakatau ... kembali mengalami erupsi pada Minggu (18/10).",
    "event_time_candidate_text": "Minggu (18/10)",
    "event_time_review_reason": "Tanggal tanpa tahun eksplisit; perlu konteks tambahan.",
    "event_time_timezone": null,
    "event_time_confidence": "low"
  },
  "location_mention": {
    "location_mention_id": "LOCM-a23ef66a38b0fe4d",
    "document_id": "DOC-a23ef66a38b0fe4d",
    "linked_event_id": "EVT-CAND-KRAKATAU-20261018-B",
    "mention_text": "Gunung Anak Krakatau di Perairan Selat Sunda, Kabupaten Lampung Selatan",
    "mention_normalized": "Anak Krakatau, Lampung Selatan",
    "mention_role": "event_location",
    "mention_status": "normalized",
    "mention_confidence": "medium",
    "mention_evidence": "Isi berita menyebut lokasi dan tanggal kandidat."
  },
  "event_location": {
    "event_location_id": "LOCE-a23ef66a38b0fe4d",
    "event_id": "EVT-CAND-KRAKATAU-20261018-B",
    "location_name": "Perairan Selat Sunda, Kabupaten Lampung Selatan",
    "location_role": "reported_location",
    "admin_province": "Lampung",
    "admin_kabupaten_kota": "Kabupaten Lampung Selatan",
    "latitude": null,
    "longitude": null,
    "coordinate_source": null,
    "coordinate_status": "not_available",
    "coordinate_precision": "unknown",
    "coordinate_confidence": "unknown",
    "coordinate_verified_at": null,
    "coordinate_verified_by": null,
    "is_inside_indonesia": "ya",
    "location_notes": "Lokasi berdasarkan rujukan administratif di berita; bukan koordinat terverifikasi."
  },
  "category": {
    "category_assignment_id": "CAT-a23ef66a38b0fe4d",
    "event_id": "EVT-CAND-KRAKATAU-20261018-B",
    "category_name": "Gunungapi",
    "category_rank": "primary",
    "category_scope": "in_scope",
    "category_basis": "source_title",
    "category_confidence": "high",
    "category_review_status": "not_reviewed",
    "category_original": "Gunung Api"
  },
  "document_event_link": {
    "link_id": "LINK-a23ef66a38b0fe4d",
    "document_id": "DOC-a23ef66a38b0fe4d",
    "event_id": "EVT-CAND-KRAKATAU-20261018-B",
    "relation_type": "reports",
    "relation_direction": "document_to_event",
    "relevance": "primary",
    "is_primary": "ya",
    "relation_confidence": "medium",
    "event_count_mentioned": 1,
    "link_status": "active"
  },
  "verification": {
    "verification_id": "VER-a23ef66a38b0fe4d",
    "target_type": "event",
    "target_id": "EVT-CAND-KRAKATAU-20261018-B",
    "verification_status": "source_asserted",
    "verification_level": "low",
    "verification_basis": "Artikel Media Indonesia; tanggal kandidat belum dapat diresolusi.",
    "verification_source_count": 1,
    "verification_method": "source_check",
    "verified_at": null,
    "verified_by": null
  }
}
```

Penjelasan: `published_at=2026-10-19` tidak boleh menjadi `event_time`. Kandidat “Minggu (18/10)” tetap di `event_time_candidate_text` sampai tahun dan konteksnya dapat diverifikasi. Presisi `day` di sini adalah presisi kandidat, bukan klaim tanggal final; `event_time` tetap `NULL`.

## 15. Apakah skema cukup untuk integrasi multi-sumber 8 kategori?

### 15.1 Cukup secara struktural

Skema **cukup secara struktural** untuk:

1. Membedakan sumber resmi, berita, agregator, peta risiko, publikasi, dan gazetteer.
2. Menyimpan provenance sampai tingkat payload mentah, dokumen, event, waktu, lokasi, dan kategori.
3. Mengaitkan banyak dokumen ke satu event dan banyak event ke satu dokumen.
4. Menyimpan konflik klaim tanpa menimpa nilai lama.
5. Membedakan waktu aktual, tanggal saja, nowcast, kandidat manual, dan waktu tidak diketahui.
6. Membedakan penyebutan lokasi dari lokasi kejadian yang diresolusi.
7. Membedakan kategori in-scope, out-of-scope, dan belum terklasifikasi.
8. Menyimpan verifikasi, penolakan, retraksi, dan riwayat perubahan secara append-only.
9. Menangani data historis yang tidak lengkap tanpa mengarang `source_id`, raw payload, atau run.

Dengan kata lain, skema ini dapat menjadi **kontrak data** untuk integrasi multi-sumber tanpa mencampur bukti resmi dan berita.

### 15.2 Belum cukup secara operasional

Skema **belum cukup** untuk mengklaim dataset 8 kategori lengkap atau operasional, karena:

1. **Izin dan lisensi belum selesai.** 14 sumber berstatus `PERLU_IZIN`; PVMBG, Portal MBG, dan MAGMA belum boleh diaktifkan.
2. **Feed kejadian belum tersedia untuk semua kategori.** Hanya Gempabumi yang memiliki feed resmi terstruktur aktif.
3. **Gunungapi, Gerakan Tanah, dan Abrasi masih bergantung pada berita atau peta risiko.** Berita bukan bukti tunggal kejadian.
4. **Tsunami tidak memiliki feed kejadian mandiri.** Potensi tsunami pada gempa bukan event tsunami terpisah.
5. **Likuefaksi, Penurunan Muka Tanah, dan Semburan belum memiliki feed kejadian terverifikasi.**
6. **Baseline tidak memiliki raw payload, run, source_id, dan license.** Skema dapat menandainya `legacy_incomplete`, tetapi tidak dapat memulihkan bukti yang tidak pernah disimpan.
7. **Konektor dan pemetaan field per sumber belum dibuat.** Skema adalah kontrak; implementasi dan uji per sumber masih diperlukan.
8. **Verifikasi manual dan keputusan editorial belum dilakukan.** Schema tidak menggantikan reviewer, izin, atau bukti lapangan.

### 15.3 Kesimpulan

> **Skema ini siap sebagai model provenance dan kontrak integrasi, tetapi belum menjadikan dataset siap operasional atau lengkap 8 kategori.**

Status yang benar:

- **Model data:** siap.
- **Integrasi struktural:** siap.
- **Cakupan sumber:** belum.
- **Izin/lisensi:** belum.
- **Kualitas waktu/lokasi:** sebagian, dengan status ketidakpastian yang eksplisit.
- **Klaim 8 kategori lengkap:** tidak boleh dilakukan.

Langkah berikutnya adalah menjalankan aturan di `docs/PROVENANCE_VALIDATION_RULES.md`, membuat konektor/pemetaan field per sumber, dan menyelesaikan izin sebelum menambah data baru. Baseline tetap menjadi **baseline audit**, bukan dataset operasional final.
