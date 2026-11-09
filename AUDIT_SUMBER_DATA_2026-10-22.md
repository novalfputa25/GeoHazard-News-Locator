# Audit & Evaluasi Sumber Data — GeoHazard News Locator

Tanggal audit: **22 Oktober 2026**
Ruang lingkup: audit kode, dataset, konfigurasi sumber, dan uji akses langsung.
Bukti uji akses mentah: `data/uji_akses_sumber_2026-10-22.json`

> Dokumen ini **hanya berisi temuan dan rekomendasi**. Tidak ada kode, skrip, atau dataset lama yang diubah. Tidak ada package yang dipasang.

---

## 1. Ringkasan Temuan

1. **Sumber saat ini sangat berorientasi berita, bukan data kejadian.** Dari 22 feed aktif, hanya 7 yang resmi/terstruktur (4 BMKG + 2 GDACS + 1 USGS); 15 sisanya adalah feed berita umum.
2. **Hanya Gempa Bumi dan Kebakaran Hutan/Lahan yang punya isi berarti** (33 dan 71 baris). Empat dari delapan kategori prioritas **nol baris**: Tsunami, Likuefaksi, Penurunan Muka Tanah, Semburan Gas/Lumpur.
3. **83,9% dataset (661/787) masuk `Lainnya`.** Penyebab utama yang terverifikasi: 11/11 baris USGS dan 9/10 baris GDACS berakhir `Lainnya` karena judul berbahasa Inggris berformat `M 4.9 - ...` tidak cocok dengan pola detektor.
4. **Tidak ada koordinat sama sekali** di dataset (`latitude`/`longitude` tidak ada), padahal empat sumber resmi menyediakan koordinat terstruktur.
5. **`event_time` kosong di 787/787 baris** dan `isi_berita` hanyalah ringkasan RSS (median 149 karakter), bukan isi artikel penuh.
6. **Ada pelanggaran `robots.txt` pada sumber yang sedang dipakai**: `bmkg_nowcast_id` mengarah ke `/alerts/...` yang dilarang `www.bmkg.go.id`.
7. **Pemetaan lokasi lemah**: provinsi 44%, kabupaten/kota 29%, kecamatan 0,6%, RW/RT 0%.
8. **Ada dua sumber resmi bernilai tinggi yang belum dipakai**: Portal MBG (koordinat longsor & gempa merusak) dan API publik PVMBG (status gunung api + laporan). Namun keduanya berada di domain yang `robots.txt`-nya `Disallow: /` → **butuh izin tertulis** sebelum otomatisasi.
9. **`test_scraper.py` rusak** (`ImportError: cannot import name 'get_soup'`), dan `scraper/bmkg_scraper.py` punya efek samping saat diimpor (menulis CSV).
10. **Tidak ditemukan sumber resmi terverifikasi** untuk Abrasi/Akresi, Penurunan Muka Tanah, Semburan Gas/Lumpur, dan Likuefaksi.

---

## 2. Daftar Sumber Data yang Saat Ini Dipakai

Konfigurasi tunggal: `feeds.py` — **23 entri, 22 aktif** (19 `rss`, 3 `bmkg_xml`), 1 non-aktif.

### 2.1 Resmi / terstruktur (7 aktif)

| ID | Sumber | Endpoint | Tipe | Cakupan |
|---|---|---|---|---|
| `bmkg_autogempa` | BMKG | `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml` | XML | Gempa, Tsunami |
| `bmkg_gempa_terkini` | BMKG | `https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.xml` | XML | Gempa, Tsunami |
| `bmkg_gempa_dirasakan` | BMKG | `https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.xml` | XML | Gempa |
| `bmkg_nowcast_id` | BMKG | `https://www.bmkg.go.id/alerts/nowcast/id/rss.xml` | RSS | Cuaca Ekstrem |
| `gdacs_all` | GDACS | `https://www.gdacs.org/xml/rss.xml` | RSS | Gempa, Tsunami, Karhutla, Cuaca |
| `gdacs_eq_24h` | GDACS | `https://www.gdacs.org/xml/rss_eq_24h.xml` | RSS | Gempa, Tsunami |
| `usgs_m45` | USGS | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.atom` | RSS | Gempa, Tsunami |

### 2.2 Berita (15 aktif)

ANTARA (Warta Bumi, Terkini, Top News), ANTARA Jatim, detikcom, CNN Indonesia, CNBC Indonesia, Tempo, Liputan6, Republika, Media Indonesia, SINDOnews, kumparan, BBC Indonesia, Mongabay.

### 2.3 Non-aktif (1)

`pvmbg_magma` → `https://magma.esdm.go.id` (bukan RSS; belum dipakai).

### 2.4 Hasil uji akses (22 Oktober 2026)

- **Seluruh 22 feed aktif merespons HTTP 200.**
- BMKG Open Data menyediakan tepat **6 berkas**: `autogempa`, `gempaterkini`, `gempadirasakan` × (`.xml`, `.json`).
- `tsunami.json`, `gempa_signifikan.json`, `terkini.json` → **404**.

---

## 3. Evaluasi Sumber Saat Ini

### 3.1 Komposisi dataset `data/geohazard_news.csv`

787 baris × 15 kolom. Semua `url` terisi, 0 duplikat URL, 8 judul duplikat.

| Kategori | Baris | % |
|---|---:|---:|
| Lainnya | 661 | 83,9% |
| Kebakaran Hutan dan Lahan | 71 | 9,0% |
| Gempa Bumi | 33 | 4,2% |
| Cuaca Ekstrem | 14 | 1,8% |
| Gunung Api | 4 | 0,5% |
| Abrasi dan Akresi | 3 | 0,4% |
| Gerakan Tanah / Longsor | 1 | 0,1% |
| **Tsunami** | **0** | **0%** |
| **Likuefaksi** | **0** | **0%** |
| **Penurunan Muka Tanah** | **0** | **0%** |
| **Semburan Gas dan Lumpur** | **0** | **0%** |

Per sumber: detikcom 100, CNN 100, CNBC 100, Media Indonesia 100, ANTARA 97, Tempo 50, Liputan6 50, BMKG 38, SINDOnews 30, kumparan 25, BBC 21, ANTARA Jatim 20, Mongabay 20, Republika 15, USGS 11, GDACS 10.

### 3.2 Kualitas isi

| Aspek | Temuan |
|---|---|
| `isi_berita` | Median **149 karakter**; 96% < 300 karakter → hanya ringkasan RSS, bukan isi artikel |
| `published_time` | 696/787 (88,4%) bisa diparse RFC822; 91 gagal |
| `event_time` | **0/787** terisi |
| Koordinat | Kolom tidak ada |
| Duplikasi | 0 URL ganda, 8 judul ganda |

### 3.3 Kelengkapan lokasi (`geohazard_news_located.csv`)

| Kolom | Terisi | % |
|---|---:|---:|
| provinsi | 346 | 44,0% |
| kabupaten_kota | 228 | 29,0% |
| kecamatan | 5 | 0,6% |
| desa_kelurahan | 14 | 1,8% |
| dusun_kampung | 4 | 0,5% |
| rw / rt | 0 | 0% |
| alamat_detail | 13 | 1,7% |

### 3.4 Skema vs kebutuhan

Kolom yang **sudah sesuai**: `judul`→`title`, `published_time`, `event_time`, `sumber`→`source_name`, `kategori`→`hazard_category`, `provinsi`, `kabupaten_kota`, `kecamatan`, `desa_kelurahan`, `dusun_kampung`, `rw`, `rt`, `alamat_detail`, `url`→`source_url`, `isi_berita`→`content`.

Kolom yang **belum ada** (wajib untuk 8 kategori + data yang bisa dipetakan):

- `latitude`, `longitude`
- `data_type` (pembeda **laporan resmi** vs **artikel berita**)
- `location_confidence`
- `collected_at`
- (disarankan) `event_id` untuk dedup kejadian, dan `source_type`

### 3.5 Bug & cacat yang terverifikasi di kode

| Lokasi | Masalah | Dampak |
|---|---|---|
| `category_detector.py:66-71` | `Gempa Bumi` dicek **sebelum** `Tsunami`; judul "gempa ... tsunami" selalu jadi Gempa Bumi | Tsunami = 0 baris |
| `category_detector.py:67-70` | Pola judul hanya `gempa bumi\|gempabumi\|gempa\|earthquake`; tidak mengenali format `M 4.9 - ...` USGS | 11/11 USGS → Lainnya |
| `category_detector.py:131` | `Cuaca Ekstrem` memuat kata `banjir` (bukan kategori geohazard target) | Menggelembungkan kategori non-target |
| `category_detector.py:82` | Typo `long sor` di dalam regex | Tidak fatal, tapi menandakan kurang uji |
| `category_detector.py` main() | Memproses `data/bmkg_news.csv` (10 baris), bukan `geohazard_news.csv` (787) | Reklasifikasi dataset utama tidak ter-wire |
| `scraper/bmkg_scraper.py` | Kode top-level tanpa `if __name__ == "__main__"` | **Mengimpor modul menulis CSV** (terbukti saat audit) |
| `test_scraper.py` | `from scraper.bmkg_scraper import get_soup, ...` | **ImportError** — skrip mati |
| `feeds.py:39` | `bmkg_nowcast_id` di path `/alerts/...` | Melanggar `robots.txt` `www.bmkg.go.id` (`Disallow: /alerts`) |

---

## 4. Matriks Delapan Kategori Prioritas

| # | Kategori | Data lama | Sumber resmi terverifikasi | Kualitas | Status |
|---|---|---:|---|---|---|
| 1 | **Gunung Api** | 4 | MAGMA: informasi letusan, laporan harian, tingkat aktivitas, laporan aktivitas (200, HTML). PVMBG API: `data-dasar`, `tingkat-aktivitas` (isi lengkap), `laporan-singkat` (isi lengkap) | Tinggi (deskripsi + tanggal + status) | **Tersedia, perlu izin** |
| 2 | **Gempabumi** | 33 | BMKG 3 XML/JSON (200). USGS FDSN bbox Indonesia (200). PVMBG `get-destructive-earthquake` 357 record (1871–2026) | Tinggi (magnitudo, koordinat, kedalaman) | **Tersedia** |
| 3 | **Tsunami** | 0 | BMKG `autogempa`/`gempaterkini` field `Potensi` (teks). PVMBG `get-destructive-earthquake`: 29 record bertanda tsunami. Halaman `bmkg.go.id/gempabumi/berpotensi-tsunami` (200) | Sedang–tinggi | **Tersedia, belum dipetakan** |
| 4 | **Gerakan Tanah / Longsor** | 1 | Portal MBG `get-field-reports`: 2.397 baris, **koordinat 100%**, 619 `doc_id`, 363 tanggal unik. `get-sigab` 5 field report. `gerakan-tanah` 2 rekap historis 2011–2012 | Tinggi untuk titik, rendah untuk berita terkini | **Tersedia, perlu izin** |
| 5 | **Likuefaksi** | 0 | Tidak ditemukan feed/API khusus | — | **Belum ada sumber** |
| 6 | **Abrasi / Akresi** | 3 | Tidak ditemukan feed/API khusus; hanya berita (Mongabay/ANTARA) | Rendah | **Belum ada sumber resmi** |
| 7 | **Penurunan Muka Tanah** | 0 | Tidak ditemukan feed/API khusus | — | **Belum ada sumber** |
| 8 | **Semburan Gas / Lumpur** | 0 | Tidak ditemukan feed/API khusus | — | **Belum ada sumber** |

Catatan penting untuk #4: pada `get-field-reports`, **1 `doc_id` = 1 laporan investigasi**, dan satu laporan bisa berisi banyak baris titik (contoh `doc_id=235_2022` → 12 baris). Jadi 2.397 baris **bukan** 2.397 kejadian; kejadian unik ≈ 619 laporan / 363 tanggal.

---

## 5. Daftar Sumber yang Direkomendasikan

Prinsip: **resmi > terstruktur > berita**, dan hanya yang lolos uji akses.

### 5.1 Prioritas 1 — resmi & boleh dipakai sekarang

| Sumber | Endpoint | Kegunaan | Bukti |
|---|---|---|---|
| BMKG Open Data (XML/JSON) | `data.bmkg.go.id/DataMKG/TEWS/{autogempa,gempaterkini,gempadirasakan}.{xml,json}` | Gempa, magnitudo, koordinat, kedalaman, potensi tsunami | 200; Data Terbuka BMKG; tanpa `robots.txt` |
| USGS FDSN Event API | `earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minlatitude=-11&maxlatitude=6&minlongitude=94&maxlongitude=142` | Gempa berkoordinat, terfilter wilayah | 200 |
| GDACS RSS | `gdacs.org/xml/rss.xml`, `rss_eq_24h.xml` | Konfirmasi lintas sumber | 200; **rate limit 1/60 dtk, jendela 04:00–06:45 UTC** |
| Mongabap / ANTARA Warta Bumi | (sudah ada) | Berita lingkungan & kebencanaan | 200 |
| BMKG `/berita` | `www.bmkg.go.id/berita` | Berita resmi BMKG (bukan `/api`, bukan `/alerts`) | 200, tidak dilarang |

### 5.2 Prioritas 2 — resmi, bernilai tinggi, **wajib izin tertulis**

| Sumber | Endpoint | Kegunaan |
|---|---|---|
| Portal MBG — field reports | `vsi.esdm.go.id/portalmbg/api/get-field-reports` | Longsor/gerakan tanah + koordinat |
| Portal MBG — gempa merusak | `.../api/get-destructive-earthquake` | 357 gempa merusak + flag tsunami |
| Portal MBG — SIGAB | `.../api/sigab` | Laporan lapangan |
| Portal MBG — gunung api | `.../api/get-volcano-magma` | Data gunung api |
| PVMBG press-release | `vsi.esdm.go.id/data/api/public/press-release` (+ `/{route}` untuk isi penuh) | 299 laporan, isi HTML lengkap |
| PVMBG gunung api | `.../data/api/public/gunung-api/data-dasar` | Data dasar gunung api |
| PVMBG tingkat aktivitas / laporan singkat | `.../tingkat-aktivitas/apis/get`, `.../laporan-singkat/apis/get` | Status & laporan (isi lengkap dalam JSON) |
| MAGMA | `magma.esdm.go.id/v1/gunung-api/{informasi-letusan,laporan-harian,tingkat-aktivitas,laporan}` | Letusan, laporan, status |

> **Blocker:** `vsi.esdm.go.id` dan `magma.esdm.go.id` memiliki `robots.txt` `Disallow: /`. Semua endpoint di atas **berfungsi teknis** (200), tetapi otomatisasi tanpa izin berisiko melanggar kebijakan. **Jangan aktifkan sebelum ada konfirmasi tertulis.**

### 5.3 Prioritas 3 — opsional / pendukung

| Sumber | Catatan |
|---|---|
| ESDM arsip berita (`esdm.go.id/id/media-center/arsip-berita`) | 200; berita kementerian, relevansi geohazard rendah |
| Badan Geologi arsip berita (`geologi.esdm.go.id/profil/arsip-berita`) | 200; 22 Okt 2026 isinya non-hazard (museum, vaksin HPV) → nilai rendah |
| ReliefWeb API v2 | **403** tanpa `appname` terdaftar; perlu pendaftaran |
| BNPB / DIBI | `bnpb.go.id/berita` **403 Cloudflare**; DIBI API **403** → tidak dapat diandalkan |
| emsifa wilayah API | 200; bukan gazetteer resmi, hanya referensi wilayah |

### 5.4 Tidak direkomendasikan

- `bmkg.go.id/alerts/...` (nowcast RSS saat ini) — dilarang `robots.txt`.
- Scraping halaman `/api` BMKG — dilarang.
- ReliefWeb v1 — **410 Gone**.

---

## 6. Masalah & Hal yang Belum Terverifikasi

**Terverifikasi bermasalah:**
- `bmkg_nowcast_id` melanggar `robots.txt` (`Disallow: /alerts`).
- `test_scraper.py` → `ImportError`.
- `scraper/bmkg_scraper.py` menulis CSV saat diimpor.
- USGS/GDACS tidak terklasifikasi (format judul Inggris).
- Tsunami selalu kalah prioritas dari Gempa Bumi.
- `event_time` kosong total; `isi_berita` hanya ringkasan.
- Tidak ada koordinat / `data_type` / `location_confidence` / `collected_at`.

**Belum terverifikasi (jangan diasumsikan):**
- Arti persis `city_string`, `regency_string`, `district_string`, `village_string` pada Portal MBG. Kelengkapan rendah (11,7%–39,8%) dan semantiknya belum dipastikan → jangan dipetakan buta ke `kabupaten`/`kecamatan`/`desa`.
- Status lisensi/atribusi feed berita di luar `robots.txt` (Tempo `ai-train=no`, SINDOnews `Disallow:` kosong).
- Apakah PVMBG/MAGMA akan memberi izin otomatisasi.
- Cakupan "terkini" Portal MBG: `gerakan-tanah` hanya 2 rekap 2011–2012; `daftar-kejadian` hanya 1 record → **bukan sumber real-time**.
- Apakah ada API resmi untuk Likuefaksi, Abrasi/Akresi, Penurunan Muka Tanah, Semburan Gas/Lumpur (belum ditemukan).

---

## 7. Rencana Implementasi (belum dijalankan — menunggu persetujuan)

**Fase 0 — Izin & keputusan**
1. Kirim permintaan izin ke PVMBG/Badan Geologi untuk Portal MBG + MAGMA.
2. Putuskan apakah `bmkg_nowcast_id` (melanggar robots) dihapus/diganti.
3. Putuskan daftar kategori final (8 target saja, atau tetap 10 + Lainnya).

**Fase 1 — Perbaikan tanpa mengubah data lama**
- Tambah skema baru (file baru, bukan menimpa): `latitude`, `longitude`, `data_type`, `location_confidence`, `collected_at`, `event_id`, `source_type`.
- Perbaiki urutan prioritas detektor (Tsunami sebelum Gempa Bumi; tambah pola `M <angka>` / "Magnitude").
- Pisahkan `banjir` dari `Cuaca Ekstrem`.
- Perbaiki `test_scraper.py` dan guard `__main__` di `bmkg_scraper.py`.
- Uji ulang pada salinan dataset, bandingkan hasil.

**Fase 2 — Integrasi sumber resmi**
- Adapter BMKG JSON/XML → normalisasi (termasuk `Potensi` tsunami & koordinat).
- Adapter USGS FDSN bbox Indonesia.
- Adapter PVMBG/MAGMA **setelah izin** (field reports, destructive earthquake, gunung api, press-release).
- Dedup berbasis `event_id` (bukan URL) + `collected_at`.

**Fase 3 — Backfill & validasi**
- Backfill 4 kategori kosong dari sumber resmi/berita terverifikasi.
- Validasi: tidak ada koordinat karangan; `location_confidence` diisi; `event_time` hanya bila sumber menyebutkannya.

**File yang akan terdampak (usulan):**
`feeds.py`, `rss_scraper.py`, `category_detector.py`, `location_extractor.py`, `clean_data.py`, `scraper/bmkg_scraper.py`, `test_scraper.py`, plus modul adapter baru di `sources/`.

---

## 8. Pertanyaan yang Perlu Diputuskan

1. **Izin PVMBG/MAGMA**: apakah Anda akan mengajukan izin, atau kita batasi ke sumber yang jelas mengizinkan (BMKG Open Data, USGS, GDACS, berita)?
2. **`bmkg_nowcast_id`**: hapus, ganti, atau pertahankan? (saat ini melanggar `robots.txt`)
3. **Cakupan kategori**: 8 kategori target saja, atau tetap mempertahankan Karhutla & Cuaca Ekstrem?
4. **Definisi "data resmi"**: apakah laporan resmi dan artikel berita disimpan di tabel/kolom terpisah (`data_type`)?
5. **Target kelengkapan**: berapa minimum `location_confidence` dan cakupan provinsi/kabupaten yang dianggap layak?
6. **Backfill**: apakah dataset lama (787 baris) boleh diperkaya, atau hanya data baru yang memakai skema baru?

---

### Lampiran — Bukti uji akses

- `data/uji_akses_sumber_2026-10-22.json` — 40 endpoint, status HTTP, ukuran, kunci JSON, waktu uji.
- Sumber utama 200: BMKG (6 berkas), PVMBG API publik, Portal MBG (kecuali `get-province` 403), MAGMA, USGS, GDACS, ESDM.
- Gagal: ReliefWeb v2 403 (butuh appname), BNPB berita 403, BNPB DIBI API 403, Portal MBG `get-province` 403.
