# Final Dataset Baseline - GeoHazard News Locator

Status: **BASELINE RESMI PENGEMBANGAN**  
Tanggal baseline: **2026-11-02**  
Tanggal finalisasi dataset: **2026-11-01 15:05 UTC** (`2026-11-01T15:05:01Z`)

## 1. Identitas Dataset

| Atribut | Nilai |
|---|---|
| Nama file | `geohazard_news_final_20261101T150501Z.csv` |
| Path relatif | `data/geohazard_news_final_20261101T150501Z.csv` |
| Path absolut | `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_final_20261101T150501Z.csv` |
| SHA-256 | `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06` |
| Jumlah baris data | **787** |
| Jumlah kolom | **51** |
| Ukuran file | **625249 byte** |
| Sumber final | `data/geohazard_news_located_20261101T144531Z_stage5_4.csv` |
| SHA-256 sumber | `bb1bc6d4343d2b8bb1982677d09a1e6f4183dc5032f1845335299bc38c5c20db` |
| Mode | Non-destruktif; 787 baris dipertahankan; tidak ada penghapusan baris |

Dataset ini adalah satu-satunya sumber data utama untuk pengembangan aplikasi. Path utama didefinisikan di `dataset_baseline.py` melalui `PRIMARY_DATASET_PATH`.

## 2. Aturan Baseline

- Dataset final tidak boleh diubah, ditimpa, atau ditulis ulang di tempat.
- Perubahan data harus menghasilkan file baru dengan timestamp baru dan baseline baru.
- File historis dan file sumber Stage 5.4 tidak boleh dihapus.
- Aplikasi baru harus membaca `PRIMARY_DATASET_PATH` dari `dataset_baseline.py`, bukan CSV lama.
- Jangan memakai `data/bmkg_news.csv`, `data/geohazard_news.csv`, atau `data/geohazard_news_located.csv` sebagai sumber aplikasi.
- Integritas wajib diperiksa dengan `verify_dataset()` sebelum dataset dipakai sebagai baseline rilis.

## 3. Batas Kualitas

- `Lainnya` belum terklasifikasi: **632** baris.
- Kategori di luar 8 target: **102** baris; semuanya ditandai dan tidak dipaksa menjadi kategori target.
- `event_time` tidak diketahui/perlu review: **723** baris.
- Tanpa lokasi kejadian: **679** baris.
- Koordinat belum terverifikasi: **40** baris.
- Lokasi administratif belum terverifikasi: **88** baris.
- Baris fokus `perlu_verifikasi`: **7** baris.
- Lima alamat tanpa provinsi tidak dipakai sebagai bukti lokasi kejadian.
- Duplikat judul/isi/URL: **10 / 4 / 0** baris; tidak ada baris yang dihapus.
- Tidak ada verifikasi online, geocoding, atau scraping baru pada tahap finalisasi.
- Dataset bukan data tervalidasi operasional. Gunakan status `terindikasi` atau `belum diverifikasi`; jangan menyatakan koordinat atau lokasi administratif sudah terverifikasi.

### Komposisi kategori final

| Kategori | Jumlah |
|---|---:|
| Abrasi dan Akresi | 3 |
| Gempabumi | 44 |
| Gerakan Tanah/Tanah Longsor | 1 |
| Gunungapi | 5 |
| Lainnya | 734 |
| Likuefaksi | 0 |
| Penurunan Muka Tanah | 0 |
| Semburan Gas dan Lumpur | 0 |
| Tsunami | 0 |

## 4. File yang Membaca Dataset Final

Saat baseline dibuat:

- `dataset_baseline.py` mendefinisikan path utama dan membaca dataset final di `verify_dataset()`.
- `test_dataset_baseline.py` memverifikasi path, hash, jumlah baris, dan jumlah kolom.
- Tidak ada kode aplikasi produksi atau pipeline produksi yang membaca dataset final.
- Direktori `static/`, `templates/`, `database/`, dan `sources/` tidak berisi kode aplikasi.

## 5. Pipeline yang Masih Membaca CSV Lama

Pipeline lama tetap ada dan tidak diubah:

| File | Input | Output | Catatan |
|---|---|---|---|
| `rss_scraper.py` | Feed RSS/Atom/BMKG | `data/geohazard_news_scrape_<timestamp>.csv` | Timestamped; collision memakai suffix `_2`, `_3`, dan seterusnya |
| `location_extractor.py` | `data/geohazard_news_scrape_*.csv` terbaru; fallback `data/geohazard_news.csv` | `data/geohazard_news_located_<timestamp>.csv` | Timestamped; collision memakai suffix |
| `category_detector.py` | `data/bmkg_news.csv` | `data/bmkg_news_classified.csv` | Pipeline BMKG legacy |
| `clean_data.py` | `data/bmkg_news.csv` | Tidak ditemukan output final | Pipeline BMKG legacy |
| `scraper/bmkg_scraper.py` | `data/bmkg_news.csv` | `data/bmkg_news_categorized.csv` | Pipeline BMKG legacy |
| `build_gazetteer.py` | Sumber referensi wilayah | `data/wilayah_gazetteer.json` | Tidak menyentuh dataset final |
| `scripts/build_geohazard_v2_phase1.py` | `data/geohazard_news.csv`, `data/geohazard_news_located.csv`, `data/geohazard_news_v2.csv` | `data/geohazard_news_v2_candidate_<timestamp>.csv` dan file audit | Kandidat V2; bukan baseline final |
| `scripts/refine_geohazard_v2_phase1.py` | Kandidat V2 | File review bertimestamp | Bukan baseline final |
| `scripts/improve_geohazard_quality_stage5.py` | Stage 5 source | `data/geohazard_news_located_<timestamp>_stage5.csv` | Timestamped; bukan baseline final |
| `scripts/refine_geohazard_quality_stage5_2.py` | Stage 5 | `data/geohazard_news_located_<timestamp>_stage5_2.csv` | Timestamped; bukan baseline final |
| `scripts/extract_event_time_stage5_4.py` | Stage 5.2 | `data/geohazard_news_located_<timestamp>_stage5_4.csv` | Timestamped; bukan baseline final |
| `scripts/finalize_geohazard_release.py` | Stage 5.4 | `data/geohazard_news_final_<timestamp>.csv` | Timestamped; guard hash sumber; tidak menimpa file existing |

## 6. Risiko Penimpaan

- Tidak ditemukan script yang menulis langsung ke path dataset final existing.
- `scripts/finalize_geohazard_release.py` dapat membuat kandidat `geohazard_news_final_<timestamp>.csv` baru. Script ini memakai nama bertimestamp dan loop collision, sehingga tidak menimpa baseline existing, tetapi menjalankannya dapat menghasilkan baseline baru yang membingungkan. Jangan dijalankan tanpa persetujuan.
- `rss_scraper.py` hanya menulis prefix `geohazard_news_scrape_`; sudah diuji dengan timestamp tetap dan collision suffix.
- `location_extractor.py` hanya menulis prefix `geohazard_news_located_`; sudah diuji dengan timestamp tetap dan collision suffix.
- Script Stage 5 menulis file stage-specific bertimestamp; tidak menulis path final.
- Script V2 dan pipeline BMKG legacy menulis file legacy masing-masing; tidak menulis path final.
- Tidak ada operasi penghapusan file historis yang ditemukan pada audit ini.

## 7. Pemeriksaan Integritas Terakhir

- Keberadaan file: ada.
- SHA-256: cocok dengan baseline.
- Jumlah baris: 787.
- Jumlah kolom: 51.
- Field wajib kosong: 0.
- URL unik: 787.
- Error validasi final: 0.
- Kategori final: 5 kategori terpakai, seluruhnya dalam kontrak 9 nilai.
- Hash sumber Stage 5.4: tidak berubah.
- Test terarah: **49 test lulus** (46 test final/lama + 3 test baseline).
- Tidak ditemukan operasi penghapusan file historis pada kode proyek.

Perintah verifikasi:

```powershell
& ".venv\Scripts\python.exe" -c "import dataset_baseline; print(dataset_baseline.verify_dataset())"
& ".venv\Scripts\python.exe" -m unittest -q test_stage5_quality test_stage5_2_quality test_stage5_4_event_time test_final_release_geohazard test_dataset_baseline
```
