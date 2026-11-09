# Hasil Validasi Pilot Pengumpulan Data Geohazard

Run: `PILOT-20261102T110641Z`  
Sumber hasil: `data/pilot/runs/PILOT-20261102T110641Z/pilot_validation_results.csv`  
Quality gate: `data/pilot/runs/PILOT-20261102T110641Z/pilot_quality_gates.csv`  
Status: **pilot internal; belum layak rilis publik**

## 1. Ringkasan

Seluruh 59 aturan pada `docs/PROVENANCE_VALIDATION_RULES.md` tercakup dalam hasil implementasi: 51 dievaluasi, 8 tidak dievaluasi karena tidak relevan. Tidak ada aturan yang hilang dari hasil implementasi.

| Status | Jumlah |
|---|---:|
| Lulus | 51 |
| Gagal | 0 |
| Perlu review | 0 |
| Tidak dievaluasi | 8 |
| **Total** | **59** |

Rincian yang lulus:

| Tingkat | Lulus |
|---|---:|
| P0 | 22 |
| P1 | 27 |
| P2 | 2 |

Tidak ada pelanggaran P0. Tidak ada kegagalan validasi yang memblokir penggunaan pilot secara internal. Namun, gate G1 hanya **lulus dengan catatan** karena lisensi/izin redistribusi belum diverifikasi.

## 2. Quality gate

| Gate | Status | Catatan |
|---|---|---|
| G0 Baseline | Lulus | Hash dan ukuran baseline tidak berubah |
| G1 Sumber | Lulus dengan catatan | Semua sumber resmi aktif; lisensi belum diverifikasi |
| G2 Payload | Lulus | Empat raw payload tersimpan dan hash cocok |
| G3 Dokumen | Lulus | ID dokumen unik dan sumber terdaftar |
| G4 Kejadian | Lulus | Event terpisah dari dokumen; duplikat lintas sumber tidak digabung otomatis |
| G5 Waktu | Lulus | Waktu berasal dari field resmi, bukan `published_at` |
| G6 Lokasi | Lulus | Koordinat berstatus `source_coordinate`, belum `verified` |
| G7 Kategori | Lulus | Hanya Gempabumi yang tercakup |
| G8 Klaim dan verifikasi | Lulus | Klaim mengikuti rekaman resmi |
| G9 Legacy dan deduplikasi | Lulus | Tidak ada data legacy; duplikat hanya ditandai |
| G10 Rilis | Tidak dievaluasi | Pilot bukan rilis; belum ada persetujuan editorial |

## 3. Pemeriksaan utama yang lulus

- Empat `source_id` berasal dari register dan berstatus aktif.
- Empat raw payload memiliki SHA-256 yang cocok dengan file dan ukuran record.
- 23 `document_id` unik; seluruh dokumen memiliki sumber terdaftar dan provenance lengkap.
- 20 `event_id` unik; satu event memiliki tepat satu link primer.
- Waktu BMKG berasal dari `DateTime`; waktu USGS berasal dari `summary Time`. `updated` USGS tidak dipakai sebagai waktu kejadian.
- Koordinat berada dalam rentang yang sah dan flag `is_inside_indonesia` konsisten dengan bbox pilot.
- Kategori `Gempabumi` memiliki satu assignment primer per event.
- 140 assertion dan 59 atribut memiliki sumber dan bukti.
- Tidak ada relasi nonaktif yang dijadikan bukti.
- 373 `change_log` memiliki metadata wajib dan tidak ada `create` ganda untuk target yang sama.
- Baseline tetap `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06`, 787 baris × 51 kolom.
- `python -m unittest -v test_dataset_baseline` lulus 3/3.

## 4. Aturan yang tidak dievaluasi

Delapan aturan berikut tidak relevan pada pilot satu-run yang hanya memuat data kejadian, bukan data legacy, relasi antar-event, atau URL kanonik duplikat:

- `R-LEG-01`
- `R-LEG-02`
- `R-LEG-03`
- `R-LEG-04`
- `R-REL-01`
- `R-REL-02`
- `R-REL-03`
- `R-DUP-01`

Status ini bukan kegagalan. Aturan tersebut harus dijalankan ketika data legacy, relasi event, atau beberapa snapshot mulai dimasukkan.

## 5. Catatan dan risiko

1. **Lisensi belum diverifikasi.** Semua sumber memiliki `source_license_status=unverified`. Gate G1 tidak boleh dibaca sebagai izin publikasi.
2. **robots BMKG tidak terbaca.** Status `unreadable` tidak sama dengan izin. Pengambilan dilakukan satu kali dengan jeda dan tanpa bypass TLS.
3. **Dua kandidat duplikat.** Tomohon dan Tanimbar/Banda berdekatan waktu dan lokasi, tetapi tetap dipisah sampai review manual.
4. **Cakupan terbatas.** Hanya Gempabumi. Tujuh kategori lain tidak boleh diklaim tercakup.
5. **Append-only baru diuji dalam satu run.** `change_log` konsisten untuk run ini, tetapi perilaku append-only lintas snapshot belum diuji.
6. **Tidak ada URL BMKG per record.** URL memakai fragmen feed; raw payload adalah bukti utama.
7. **Jumlah event bukan jumlah kejadian fisik unik.** Dua pasangan lintas sumber belum digabung.

## 6. Kesimpulan

Validasi teknis pilot **lulus untuk evaluasi internal**: tidak ada pelanggaran P0, seluruh output memiliki provenance, dan baseline tidak berubah. Pilot **belum layak dipublikasikan atau diredistribusikan** karena lisensi belum diverifikasi, duplikat lintas sumber belum direview, dan cakupan baru satu kategori.

Tindakan sebelum naik status:

1. Review manual dua kandidat duplikat.
2. Selesaikan lisensi dan izin sumber.
3. Uji append-only pada snapshot kedua.
4. Tambahkan sumber resmi untuk kategori yang belum tercakup.
5. Jalankan ulang gate G10 setelah review editorial.
