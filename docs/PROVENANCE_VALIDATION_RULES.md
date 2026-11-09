# Provenance Validation Rules — GeoHazard News Locator

Tanggal: **2026-11-02**  
Versi: **1.0.0**  
Berlaku untuk: `reports/FINAL_PROVENANCE_SCHEMA.md` dan `docs/PROVENANCE_FIELD_DICTIONARY.csv`  
Sifat: kontrak validasi; **belum diimplementasikan sebagai kode atau database**

## 1. Arti tingkat keparahan

| Tingkat | Arti | Tindakan |
|---|---|---|
| **P0** | Pelanggaran identitas, integritas, izin, atau provenance dasar | Tolak record; jangan dipakai untuk rilis |
| **P1** | Pelanggaran kualitas/ konsistensi yang dapat menyebabkan klaim salah | Perbaiki atau tandai `manual_review`; blokir rilis bila tidak diselesaikan |
| **P2** | Peringatan/duplikasi/quality warning | Catat, review, atau terima dengan alasan tertulis |

Prinsip umum:

- Validator tidak boleh “memperbaiki” nilai dengan asumsi.
- Record yang gagal P0 tidak boleh masuk dataset baru.
- Record yang gagal P1 boleh disimpan hanya dengan status review yang eksplisit.
- Semua pengecualian harus tercatat di `change_log`.
- Baseline lama tidak boleh diubah untuk memenuhi aturan ini.

## 2. Urutan validasi

1. Validasi sumber (`R-SRC`).
2. Validasi payload mentah (`R-RAW`).
3. Validasi dokumen dan identitas sumber (`R-DOC`, `R-LEG`).
4. Validasi kejadian (`R-EVT`).
5. Validasi waktu (`R-TIME`).
6. Validasi lokasi dan koordinat (`R-LOC`).
7. Validasi kategori (`R-CAT`).
8. Validasi relasi dokumen-kejadian (`R-LINK`).
9. Validasi klaim dan konflik (`R-AST`).
10. Validasi verifikasi (`R-VER`).
11. Validasi relasi antar kejadian (`R-REL`).
12. Validasi duplikasi (`R-DUP`).
13. Validasi riwayat perubahan (`R-CHG`).

## 3. Aturan sumber

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-SRC-01` | P0 | `source_id` tidak ada di `docs/MASTER_SOURCE_REGISTER.csv`, duplikat, atau FK sumber tidak valid | Tolak record |
| `R-SRC-02` | P0 | `source_id` dibuat dari label, nama institusi, URL, atau nomor baris tanpa pemetaan register | Tolak; gunakan label legacy |
| `R-SRC-03` | P0 | `source_registry_status` di luar vocabulary, atau status `PERLU_IZIN`/`BELUM_TERSEDIA`/`TIDAK_SESUAI` dipakai sebagai sumber aktif | Tolak aktivasi |
| `R-SRC-04` | P1 | `source_type`, `source_role`, dan `source_data_type` tidak konsisten; mis. `news` sebagai `primary_official`, atau `risk_map` sebagai `event_feed` | Perbaiki atau tandai review |
| `R-SRC-05` | P0 | `source_license_status=verified` tanpa dasar lisensi; sumber robots `disallowed` diaktifkan; robots tidak terbaca dianggap izin | Tolak klaim izin/aktivasi |

## 4. Aturan payload mentah

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-RAW-01` | P0 | Record baru tidak memiliki `raw_payload_id`, `raw_payload_source_id`, `raw_payload_url`, atau `raw_payload_retrieved_at`; FK sumber tidak valid | Tolak record baru |
| `R-RAW-02` | P0 | `raw_payload_sha256` bukan 64 hex, ukuran negatif, path kosong, hash tidak cocok, atau payload lama ditimpa | Tolak; pertahankan snapshot lama |
| `R-RAW-03` | P1 | `raw_payload_retrieved_at` bukan ISO 8601, atau waktu ambil dipakai sebagai waktu publikasi/kejadian tanpa bukti | Perbaiki metadata waktu |
| `R-RAW-04` | P1 | `raw_payload_status=stored` tetapi payload tidak ada; record baru memakai `missing`; data legacy tanpa payload tidak memakai `legacy_incomplete` | Turunkan status provenance |

## 5. Aturan dokumen

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-DOC-01` | P0 | `document_id` duplikat, tidak stabil, berasal dari nomor baris, atau dipakai ulang | Tolak record |
| `R-DOC-02` | P1 | Dokumen tidak memiliki judul dan URL/ID eksternal; URL kanonik berubah tanpa alasan; hash konten baru tidak ada | Lengkapi atau tandai review |
| `R-DOC-03` | P0 | `registered` tanpa `source_id` valid; `legacy_label_only` tanpa label atau dengan `source_id`; tipe/peran dokumen tidak konsisten | Tolak record |
| `R-DOC-04` | P1 | Dokumen baru tidak memiliki raw payload, run, atau waktu ambil; status `complete` dipakai padahal salah satu bukti tidak ada | Turunkan ke `partial`/`legacy_incomplete` |

## 6. Aturan kejadian

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-EVT-01` | P0 | `event_id` duplikat, tidak stabil, memakai `document_id`, atau mengabaikan native ID yang tersedia | Tolak record |
| `R-EVT-02` | P1 | `event_primary_source_id` tidak valid; event tidak memiliki judul; sumber NULL tanpa catatan provenance | Lengkapi atau tandai review |
| `R-EVT-03` | P0 | Berita tunggal diberi `confirmed`; `confirmed` tanpa sumber resmi/korroborasi; `retracted` tanpa change log; konflik tidak ditandai `disputed` | Tolak status atau turunkan |
| `R-EVT-04` | P1 | `event_verification_status=official` dari berita/agregator; sumber resmi dianggap otomatis memverifikasi semua field | Turunkan status verifikasi |
| `R-EVT-05` | P1 | `event_group_id` dipakai sebagai pengganti `event_id`; atribut yang sama memiliki beberapa nilai terpilih tanpa resolusi; grup/atribut tidak memiliki bukti; `tsunami_potential` dipakai; status tsunami di luar `positive|negative|unknown`; status eksplisit tanpa nilai mentah | Perbaiki relasi/atribut |

Catatan `R-EVT-05`: potensi tsunami memakai `bmkg_potential_text` untuk nilai mentah dan `tsunami_potential_status` untuk status ternormalisasi. Status eksplisit (`positive`/`negative`) wajib memiliki nilai mentah; status `unknown` boleh berasal dari nilai kosong atau pernyataan yang tidak eksplisit.

## 7. Aturan waktu

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-TIME-01` | P0 | `event_time` terisi tanpa `event_time_basis` atau `event_time_evidence`; bukti tidak mendukung nilai | Tolak nilai waktu |
| `R-TIME-02` | P0 | `event_time` diisi dari `document_published_at`; `event_time` kosong tetapi status tidak `unknown`/`not_applicable`/`manual_review` | Hapus nilai atau perbaiki status |
| `R-TIME-03` | P1 | Presisi `second`/`minute`/`hour` tanpa zona waktu; presisi `day` diberi jam; rentang `start > end`; nilai tidak sesuai presisi | Perbaiki atau tandai review |
| `R-TIME-04` | P1 | `nowcast`/`forecast`/`estimated` diperlakukan sebagai `actual`; nowcast dipakai untuk klaim kejadian aktual | Turunkan status/keluarkan dari klaim aktual |
| `R-TIME-05` | P1 | `event_time_candidate_text` ada tetapi status bukan `manual_review`; tahun dibuat tanpa bukti; kandidat diubah menjadi `event_time` otomatis | Kembalikan ke review manual |
| `R-TIME-06` | P2 | Zona waktu bukan IANA atau offset tidak konsisten dengan nilai waktu | Perbaiki metadata zona |

## 8. Aturan lokasi dan koordinat

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-LOC-01` | P0 | Hanya latitude atau hanya longitude; latitude di luar -90..90; longitude di luar -180..180 | Tolak koordinat |
| `R-LOC-02` | P0 | Koordinat tanpa `coordinate_source`, `coordinate_status`, `coordinate_precision`, atau `coordinate_confidence`; `source_coordinate` ditandai `verified` | Tolak/turunkan status |
| `R-LOC-03` | P1 | `location_mention` tanpa dokumen/teks; `linked_event_id` atau `event_location.event_id` tidak valid | Perbaiki relasi |
| `R-LOC-04` | P1 | Rujukan administratif dijadikan titik kejadian tanpa bukti; `mention_role`/`mention_status` tidak konsisten; normalisasi tanpa evidence | Tandai review |
| `R-LOC-05` | P1 | `is_inside_indonesia` bertentangan dengan koordinat; koordinat luar Indonesia tidak ditandai; klaim Indonesia tanpa bukti | Perbaiki flag/klaim |
| `R-LOC-06` | P1 | `reported_coordinate`/`approximate`/`source_coordinate` ditandai `verified`; `verified` tanpa bukti | Turunkan status |
| `R-LOC-07` | P0 | `coordinate_status=verified` tanpa `coordinate_verified_at` dan `coordinate_verified_by` | Tolak status verified |

## 9. Aturan kategori

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-CAT-01` | P0 | `category_name` di luar 8 kategori + `Lainnya`; event FK tidak valid; tidak ada kategori `primary` pada event yang memiliki kategori | Tolak record |
| `R-CAT-02` | P0 | Kategori 8 resmi diberi `category_scope` selain `in_scope`; topik di luar 8 dipaksa `in_scope`; `Lainnya` tanpa scope yang jelas | Perbaiki scope |
| `R-CAT-03` | P1 | Kategori diubah tanpa `category_original`, alasan, basis, atau confidence; kategori hanya dari nama sumber | Tandai review/manual |
| `R-CAT-04` | P1 | `category_review_status=changed` tanpa reviewer, waktu, atau catatan; review mengubah kategori tanpa jejak | Tolak perubahan |

## 10. Aturan relasi dokumen-kejadian

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-LINK-01` | P0 | `link_id` duplikat; `document_id`/`event_id` tidak valid; relasi yatim | Tolak relasi |
| `R-LINK-02` | P1 | `relation_type`, `relation_direction`, `relevance`, `is_primary`, atau `relation_confidence` tidak valid; lebih dari satu `is_primary=ya` aktif tanpa pengecualian | Perbaiki relasi |
| `R-LINK-03` | P1 | `event_count_mentioned < 1`; dokumen multi-event dipaksa menjadi satu event tanpa grup/link terpisah; jumlah kejadian tidak konsisten | Tandai review |
| `R-LINK-04` | P1 | Relasi `superseded`/`rejected` dipakai untuk verifikasi; relasi nonaktif dianggap bukti | Keluarkan dari bukti |
| `R-LINK-05` | P2 | Relasi aktif duplikat untuk pasangan dokumen-kejadian-relasi yang sama | Gabungkan atau tandai duplikat |

## 11. Aturan klaim dan konflik

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-AST-01` | P0 | `assertion_id` duplikat; event FK tidak valid; tidak ada source/dokumen; `field_name` di luar daftar | Tolak klaim |
| `R-AST-02` | P1 | Klaim tanpa nilai, bukti, status, atau confidence; status `accepted` tanpa dasar | Lengkapi/tandai review |
| `R-AST-03` | P1 | Dua nilai `accepted` bertentangan untuk field yang sama tanpa status `conflict`/`disputed` dan tanpa catatan resolusi | Blokir pemilihan nilai |

## 12. Aturan verifikasi

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-VER-01` | P0 | Target verification tidak valid; status/level/metode/basis kosong; `verification_source_count < 0` | Tolak record |
| `R-VER-02` | P1 | `official` diberikan hanya dari berita/agregator; `official` tanpa dasar rekaman resmi atau persetujuan manual | Turunkan status |
| `R-VER-03` | P1 | `corroborated` tetapi sumber independen kurang dari 2; `verification_source_count` tidak sesuai | Turunkan ke `source_asserted` |
| `R-VER-04` | P1 | Verifikasi manual tanpa `verified_at`/`verified_by`; reject/retract tanpa alasan; verifikasi mengklaim lebih dari bukti | Perbaiki atau tolak |

## 13. Aturan perubahan

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-CHG-01` | P0 | `change_log` tanpa target valid, tipe, waktu, pelaku, alasan, atau versi skema | Tolak perubahan |
| `R-CHG-02` | P1 | `update` tanpa `field_name`/nilai lama/baru; `create` memakai nilai lama; `no_op` tanpa alasan | Perbaiki log |
| `R-CHG-03` | P0 | Data dihapus/ditimpa tanpa jejak; `manual_review` tidak sesuai kenyataan; log tidak append-only | Tolak perubahan |

## 14. Aturan data historis

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-LEG-01` | P0 | Label sumber historis diubah menjadi `source_id` tanpa pemetaan dan bukti | Tolak pemetaan |
| `R-LEG-02` | P0 | Record legacy tanpa raw/run diberi provenance `complete`; `legacy_incomplete` tidak dipakai padahal bukti tidak ada | Turunkan status provenance |
| `R-LEG-03` | P1 | Nomor baris dipakai sebagai `document_id`/`event_id`; `document_legacy_row_ref` dianggap identitas permanen | Ganti dengan ID stabil |
| `R-LEG-04` | P1 | `document_source_type`/`source_role` ditebak dari label tanpa catatan; `unknown` tidak dipakai saat tidak ada bukti | Tandai `unknown`/review |

## 15. Aturan duplikasi

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-DUP-01` | P1 | URL kanonik sama tetapi diperlakukan sebagai dokumen berbeda tanpa relasi versi/duplikat | Tautkan atau tandai duplikat |
| `R-DUP-02` | P1 | Dokumen duplikat dihitung sebagai event ganda; event duplikat tidak memakai native ID/kunci stabil; baris dihapus untuk memperbaiki statistik | Gabungkan event secara eksplisit, bukan menghapus bukti |

## 16. Aturan relasi antar kejadian

| ID | Tingkat | Kondisi gagal | Tindakan |
|---|---|---|---|
| `R-REL-01` | P0 | `event_relation_id` duplikat; `from_event_id`/`to_event_id` tidak valid; relasi ke diri sendiri | Tolak relasi |
| `R-REL-02` | P1 | Relasi tanpa tipe/confidence/bukti; `same_event` atau `secondary_hazard_of` tanpa bukti yang memadai | Tandai review |
| `R-REL-03` | P1 | Relasi bertentangan dengan grup/duplikasi/status event; siklus relasi yang tidak dapat dijelaskan | Blokir sampai direview |

## 17. Quality gate rilis

| Gate | Syarat | Gagal jika |
|---|---|---|
| **G0 Baseline** | Baseline lama tidak berubah | Hash, baris, atau kolom berubah |
| **G1 Sumber** | Semua sumber baru terdaftar, statusnya sah, dan lisensi/izin dicatat | Ada sumber tanpa register/izin |
| **G2 Payload** | Semua record baru memiliki payload mentah, hash, run, dan waktu ambil | Ada record baru tanpa snapshot |
| **G3 Dokumen** | Semua dokumen memiliki ID stabil dan identitas sumber yang konsisten | Ada ID dari nomor baris atau identitas sumber palsu |
| **G4 Kejadian** | Event terpisah dari dokumen; tidak ada event dari satu berita tanpa dasar | Ada event fiktif/ganda |
| **G5 Waktu** | Semua `event_time` memiliki bukti; nowcast dan tanggal saja ditandai | Ada waktu hasil tebakan |
| **G6 Lokasi** | Semua koordinat memiliki sumber/status/presisi; koordinat luar Indonesia ditandai | Ada koordinat tanpa provenance |
| **G7 Kategori** | Semua kategori dalam kontrak; scope konsisten | Ada kategori liar/pencampuran scope |
| **G8 Klaim/verifikasi** | Konflik tercatat; status verifikasi sesuai bukti | Ada klaim resmi tanpa dasar |
| **G9 Legacy/dedup** | Data legacy berstatus `legacy_incomplete`; duplikasi dicatat, bukan dihapus | Ada klaim lengkap dari data legacy |
| **G10 Rilis** | Hash, manifest, laporan gate, dan persetujuan tersedia | Tidak ada manifest/persetujuan |

Rilis baru hanya boleh dipromosikan jika:

1. G0-G4 lulus tanpa pengecualian P0.
2. G5-G8 lulus atau memiliki pengecualian tertulis yang disetujui.
3. G9-G10 lulus.
4. Tidak ada klaim “8 kategori lengkap” tanpa bukti kejadian untuk setiap kategori.

## 18. Ringkasan kegagalan yang paling berbahaya

| Kegagalan | Dampak | Aturan |
|---|---|---|
| Mengarang `source_id` dari label | Provenance palsu | `R-SRC-02`, `R-LEG-01` |
| Memakai `published_time` sebagai `event_time` | Waktu kejadian salah | `R-TIME-02` |
| Menganggap berita sebagai konfirmasi resmi | Klaim palsu | `R-EVT-03`, `R-EVT-04`, `R-VER-02` |
| Menganggap peta risiko sebagai event | Cakupan palsu | `R-SRC-04`, `R-CAT-02` |
| Menganggap koordinat sumber sebagai verified | Lokasi menyesatkan | `R-LOC-02`, `R-LOC-06`, `R-LOC-07` |
| Menghapus duplikat tanpa audit | Kehilangan bukti | `R-CHG-03`, `R-DUP-02` |
| Memecah satu artikel menjadi banyak event tanpa bukti | Hitungan berlebih | `R-LINK-03`, `R-EVT-05` |

## 19. Hubungan dengan dokumen lain

- Model dan contoh: `reports/FINAL_PROVENANCE_SCHEMA.md`
- Definisi field dan nilai: `docs/PROVENANCE_FIELD_DICTIONARY.csv`
- Register sumber: `docs/MASTER_SOURCE_REGISTER.csv`
- Rencana finalisasi: `reports/RENCANA_FINALISASI_DATASET.md`
- Audit sumber: `reports/FINAL_AUDIT_SUMBER_DATA.md`
- Kualitas baseline: `reports/AUDIT_KUALITAS_DATASET_FINAL.md`

Dokumen ini tidak mengubah baseline. Penerapan aturan harus dilakukan pada pipeline baru/file baru, bukan dengan menulis ulang dataset historis.
