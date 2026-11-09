# SOURCE DECISIONS — DRAFT

**Project:** GeoHazard News Locator
**Tanggal:** 22 Oktober 2026
**Basis:** Audit `AUDIT_SUMBER_DATA_2026-10-22.md` + bukti `data/uji_akses_sumber_2026-10-22.json`
**Status dokumen:** DRAFT — belum ada implementasi, belum ada perubahan kode/dataset.

> Dokumen ini adalah **keputusan sumber**, bukan migrasi. Tidak mengubah `feeds.py`, scraper, detektor kategori, database, atau dataset.

---

## 1. Keputusan Cakupan Project

| No | Keputusan | Konsekuensi |
|---|---|---|
| 1 | Cakupan **hanya 8 kategori bahaya geologi**: Gunungapi, Gempabumi, Tsunami, Gerakan Tanah/Tanah Longsor, Likuefaksi, Abrasi dan Akresi, Penurunan Muka Tanah, Semburan Gas dan Lumpur. | Kebakaran Hutan/Lahan dan Cuaca Ekstrem **tidak lagi dikumpulkan** untuk data baru. |
| 2 | **Satu dataset** dengan kolom `data_type` untuk membedakan `official_event_report` dan `news_article`. | Laporan resmi dan artikel berita boleh berada di tabel yang sama, dipisahkan oleh `data_type`. |
| 3 | PVMBG/MAGMA dan Portal MBG **menunggu izin tertulis** sebelum otomatisasi. | Status `MENUNGGU IZIN`; tidak ada scraping otomatis. |
| 4 | **787 berita lama dipertahankan**; pipeline aktif tidak diubah sebelum daftar sumber disetujui. | Tidak ada penghapusan baris; baris Karhutla/Cuaca Ekstrem lama tetap ada dan perlu penanda status (lihat §13). |
| 5 | Sumber internasional (USGS, GDACS) **bukan sumber resmi Indonesia**. | Ditandai sebagai *sumber internasional pendukung*, tidak menggantikan BMKG/PVMBG. |
| 6 | Akses URL ≠ izin. | Feed berita hanya `SUMBER PENDUKUNG`; lisensi/kutipan tetap `BELUM DIVERIFIKASI`. |

### Legenda status

- **DISETUJUI UNTUK KANDIDAT SUMBER AKTIF** — akses dan ketentuan penggunaan telah diperiksa; siap dipertimbangkan untuk aktivasi.
- **MENUNGGU IZIN** — jangan aktifkan otomatisasi.
- **PERLU RISET** — belum ditemukan sumber yang cukup kuat.
- **SUMBER PENDUKUNG** — hanya melengkapi/membandingkan, bukan sumber utama.

### Legenda ketersediaan data

| Simbol | Arti |
|---|---|
| ✅ | Tersedia eksplisit (field/teks terstruktur) |
| ◐ | Sebagian / perlu parsing / hanya dalam teks bebas |
| — | Tidak tersedia |
| ? | **BELUM DIVERIFIKASI** |

---

## 2. Ringkasan Matriks 8 Kategori

| Kategori | Sumber utama | Pendukung | Status utama |
|---|---|---|---|
| Gunungapi | PVMBG API publik / MAGMA | BMKG `/berita`, ANTARA Warta Bumi | **MENUNGGU IZIN** |
| Gempabumi | BMKG Open Data (XML/JSON) | USGS FDSN, GDACS, PVMBG gempa merusak | **DISETUJUI (kandidat)** |
| Tsunami | BMKG Open Data (`Potensi`) | PVMBG gempa merusak (flag tsunami), GDACS | **DISETUJUI (kandidat)** |
| Gerakan Tanah / Longsor | Portal MBG `get-field-reports` | ANTARA, Mongabay, PVMBG press-release | **MENUNGGU IZIN** |
| Likuefaksi | — | Portal MBG (perlu cek `event_type`) | **PERLU RISET** |
| Abrasi dan Akresi | — | Mongabay, ANTARA | **PERLU RISET** |
| Penurunan Muka Tanah | — | Badan Geologi PATGTL (halaman) | **PERLU RISET** |
| Semburan Gas dan Lumpur | — | Badan Geologi, berita | **PERLU RISET** |

**Kesimpulan jujur:** hanya **Gempabumi** dan **Tsunami** yang punya sumber utama terstruktur yang boleh diaktifkan sekarang. Gunungapi dan Longsor punya sumber kuat tetapi **tertahan izin**. Empat kategori lain **belum punya sumber terstruktur terverifikasi**.

---

## 3. Matriks Rinci per Kategori

### 3.1 Gunungapi

| Peran | Sumber | Endpoint terverifikasi | Akses & format | Waktu kejadian | Waktu publikasi | Jenis bahaya | Lokasi | Koordinat | Magnitudo/Status | Deskripsi | Status akses & ketentuan | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Utama | PVMBG API publik — press-release | `https://vsi.esdm.go.id/data/api/public/press-release` (+ `/{route}`) | HTTP GET, JSON; isi `content` = HTML | ◐ (dalam isi) | ✅ | ◐ (dari judul/isi) | ◐ | ? | ? | ✅ | 200; `robots.txt` `Disallow: /` | Isi bebas, tidak semua gunung | **MENUNGGU IZIN** |
| Utama | PVMBG — data dasar gunung api | `https://vsi.esdm.go.id/data/api/public/gunung-api/data-dasar` | HTTP GET, JSON | ? | ? | ✅ | ◐ | ? | ? | ◐ | 200; `robots.txt` `Disallow: /` | Struktur field BELUM DIVERIFIKASI | **MENUNGGU IZIN** |
| Utama | PVMBG — tingkat aktivitas | `https://vsi.esdm.go.id/tingkat-aktivitas/apis/get` | HTTP GET, JSON (respons 78 KB) | ? | ? | ✅ | ◐ | ? | ◐ | ◐ | 200; `robots.txt` `Disallow: /` | Struktur field BELUM DIVERIFIKASI | **MENUNGGU IZIN** |
| Utama | PVMBG — laporan singkat | `https://vsi.esdm.go.id/laporan-singkat/apis/get` | HTTP GET, JSON (respons 241 KB) | ? | ? | ✅ | ◐ | ? | ◐ | ◐ | 200; `robots.txt` `Disallow: /` | Struktur field BELUM DIVERIFIKASI | **MENUNGGU IZIN** |
| Utama | MAGMA — informasi letusan | `https://magma.esdm.go.id/v1/gunung-api/informasi-letusan` (+ `/AGU`) | HTML server-rendered | ✅ | ? | ✅ | ◐ (nama gunung) | ? | ◐ (letusan) | ✅ | 200; `robots.txt` `Disallow: /` | Perlu parser HTML; bukan JSON | **MENUNGGU IZIN** |
| Utama | MAGMA — laporan harian / aktivitas | `.../v1/gunung-api/laporan-harian`, `.../laporan` | HTML | ◐ | ? | ✅ | ◐ | ? | ◐ | ◐ | 200; `robots.txt` `Disallow: /` | Perlu parser HTML | **MENUNGGU IZIN** |
| Pendukung | Portal MBG — gunung api | `https://vsi.esdm.go.id/portalmbg/api/get-volcano-magma` | HTTP GET, JSON (160 KB) | ? | ? | ✅ | ◐ | ? | ? | ? | 200; `robots.txt` `Disallow: /` | Struktur field BELUM DIVERIFIKASI | **MENUNGGU IZIN** |
| Pendukung | BMKG — berita | `https://www.bmkg.go.id/berita` | HTML | — | ✅ | ◐ | ◐ | — | — | ◐ (ringkasan) | 200; `/berita` tidak dilarang robots | Bukan data kejadian; naratif | **SUMBER PENDUKUNG** |
| Pendukung | ANTARA Warta Bumi | `https://www.antaranews.com/rss/warta-bumi.xml` | RSS | — | ✅ | ◐ | ◐ | — | — | ◐ (ringkasan) | 200; robots mengizinkan (kec. `/ajax`,`/ucnews`) | Artikel, bukan laporan | **SUMBER PENDUKUNG** |

### 3.2 Gempabumi

| Peran | Sumber | Endpoint terverifikasi | Akses & format | Waktu kejadian | Waktu publikasi | Jenis bahaya | Lokasi | Koordinat | Magnitudo/Status | Deskripsi | Status akses & ketentuan | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Utama | BMKG Open Data — autogempa | `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml` | HTTP GET, XML | ✅ (`Tanggal`,`Jam`,`DateTime`) | — | ✅ | ✅ (`Wilayah`) | ✅ (`Lintang`,`Bujur`) | ✅ (`Magnitudo`) | ◐ (`Wilayah`,`Dirasakan`) | 200; Data Terbuka BMKG; tanpa `robots.txt` | 1 gempa terbaru; bukan arsip | **DISETUJUI (kandidat)** |
| Utama | BMKG Open Data — gempaterkini | `.../gempaterkini.xml` (+ `.json`) | XML/JSON | ✅ | — | ✅ | ✅ | ✅ | ✅ | ◐ | 200 | 15 item; bukan arsip | **DISETUJUI (kandidat)** |
| Utama | BMKG Open Data — gempadirasakan | `.../gempadirasakan.xml` (+ `.json`) | XML/JSON | ✅ | — | ✅ | ✅ | ✅ | ✅ | ◐ (`Dirasakan`) | 200 | 15 item | **DISETUJUI (kandidat)** |
| Pendukung | USGS FDSN Event API | `https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minlatitude=-11&maxlatitude=6&minlongitude=94&maxlongitude=142` | GeoJSON | ✅ (`time`) | ✅ (`updated`) | ✅ | ✅ (`place`) | ✅ | ✅ (`mag`) | ◐ | 200; API publik USGS | **Internasional**, bukan resmi RI | **DISETUJUI (kandidat)** |
| Pendukung | GDACS RSS | `https://www.gdacs.org/xml/rss.xml`, `.../rss_eq_24h.xml` | RSS/XML | ✅ | ✅ | ✅ (`eventtype`) | ◐ | ✅ | ◐ | ✅ | 200; rate 1/60 dtk, jendela 04:00–06:45 UTC | **Internasional**; batas akses ketat | **DISETUJUI (kandidat)** |
| Pendukung | PVMBG — gempa merusak | `https://vsi.esdm.go.id/portalmbg/api/get-destructive-earthquake` | HTTP GET, JSON | ✅ | ? | ✅ | ◐ (teks) | ? | ✅ (`mag`) | ◐ | 200; `robots.txt` `Disallow: /` | 357 record; koordinat BELUM DIVERIFIKASI | **MENUNGGU IZIN** |

### 3.3 Tsunami

| Peran | Sumber | Endpoint terverifikasi | Akses & format | Waktu kejadian | Waktu publikasi | Jenis bahaya | Lokasi | Koordinat | Magnitudo/Status | Deskripsi | Status akses & ketentuan | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Utama | BMKG Open Data — `Potensi` | `.../autogempa.xml`, `.../gempaterkini.xml`, `.../gempadirasakan.xml` | XML/JSON | ✅ | — | ✅ | ✅ | ✅ | ✅ | ◐ (`Potensi`, `Dirasakan`) | 200; Data Terbuka BMKG | Hanya potensi tsunami dari gempa; bukan peringatan tsunami mandiri | **DISETUJUI (kandidat)** |
| Pendukung | BMKG — halaman gempa berpotensi tsunami | `https://www.bmkg.go.id/gempabumi/berpotensi-tsunami` | HTML | ◐ | ◐ | ✅ | ◐ | ◐ | ◐ | ◐ | 200; path tidak dilarang | Perlu parser HTML; bukan feed | **SUMBER PENDUKUNG** |
| Pendukung | PVMBG — gempa merusak (flag tsunami) | `.../portalmbg/api/get-destructive-earthquake` | JSON | ✅ | ? | ✅ | ◐ | ? | ✅ | ◐ | 200; `robots.txt` `Disallow: /` | 29/357 record bertanda tsunami | **MENUNGGU IZIN** |
| Pendukung | GDACS RSS | `https://www.gdacs.org/xml/rss.xml` | RSS/XML | ✅ | ✅ | ✅ | ◐ | ✅ | ◐ | ✅ | 200; rate 1/60, jendela 04:00–06:45 UTC | **Internasional** | **DISETUJUI (kandidat)** |

> Catatan: tidak ditemukan feed peringatan tsunami resmi yang boleh diakses otomatis. `bmkg.go.id/alerts/...` **dilarang** `robots.txt`.

### 3.4 Gerakan Tanah / Tanah Longsor

| Peran | Sumber | Endpoint terverifikasi | Akses & format | Waktu kejadian | Waktu publikasi | Jenis bahaya | Lokasi | Koordinat | Magnitudo/Status | Deskripsi | Status akses & ketentuan | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Utama | Portal MBG — field reports | `https://vsi.esdm.go.id/portalmbg/api/get-field-reports` | HTTP GET, JSON | ✅ (`date_occurred`) | ? | ✅ (`event_type`) | ◐ (11,7%–39,8%) | ✅ (100%) | — | ? | 200; `robots.txt` `Disallow: /` | **2.397 baris ≠ 2.397 kejadian**; 619 `doc_id`, 363 tanggal unik | **MENUNGGU IZIN** |
| Utama | PVMBG — press-release / kajian kejadian | `.../data/api/public/press-release`, `.../kajian-kejadian/apis/get` | JSON + HTML | ◐ | ✅ | ✅ | ◐ | ? | ? | ✅ | 200; `robots.txt` `Disallow: /` | Isi bebas; tidak semua longsor | **MENUNGGU IZIN** |
| Pendukung | PVMBG — SIGAB | `.../portalmbg/api/sigab` | JSON | ? | ? | ✅ | ? | ? | ? | ? | 200; `robots.txt` `Disallow: /` | Hanya 5 record; field BELUM DIVERIFIKASI | **MENUNGGU IZIN** |
| Pendukung | PVMBG — gerakan tanah (rekap) | `https://vsi.esdm.go.id/gerakan-tanah?category_id=3` | HTML/JSON | ◐ | ? | ✅ | ◐ | ? | — | ◐ | 200 | Hanya 2 rekap **2011–2012**; bukan real-time | **SUMBER PENDUKUNG** |
| Pendukung | ANTARA Warta Bumi | `https://www.antaranews.com/rss/warta-bumi.xml` | RSS | — | ✅ | ◐ | ◐ | — | — | ◐ | 200; robots mengizinkan | Artikel; butuh geocoding | **SUMBER PENDUKUNG** |
| Pendukung | Mongabay Indonesia | `https://www.mongabay.co.id/feed/` | RSS | — | ✅ | ◐ | ◐ | — | — | ◐ | 200; robots mengizinkan | Artikel lingkungan | **SUMBER PENDUKUNG** |

### 3.5 Likuefaksi

| Peran | Sumber | Endpoint / target | Akses & format | Data tersedia | Status | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|
| Kandidat resmi | Portal MBG `get-field-reports` — periksa nilai `event_type` | `.../portalmbg/api/get-field-reports` | JSON | `event_type`, `date_occurred`, koordinat | 200; `robots.txt` `Disallow: /` | Apakah `event_type` memuat likuefaksi **BELUM DIVERIFIKASI** | **PERLU RISET** |
| Kandidat resmi | Badan Geologi / PVMBG — peta zona kerentanan likuefaksi & laporan investigasi gempa | Situs Badan Geologi (halaman; endpoint terstruktur belum ditemukan) | HTML/PDF | Peta, laporan | Belum diverifikasi | Tidak ada API/feed terverifikasi | **PERLU RISET** |
| Kandidat resmi | BNPB / DIBI | `bnpb.go.id`, `dibi.bnpb.go.id` | HTML | — | **403 Cloudflare**; DIBI API 403 | Tidak dapat diandalkan | **PERLU RISET** |
| Pendukung | Artikel berita (ANTARA, Mongabay, dll.) | feed yang sudah terdaftar | RSS | Ringkasan | 200 | Bukan laporan; deteksi keyword `likuefaksi`/`liquefaction` | **SUMBER PENDUKUNG** |
| Pendukung | Laporan penelitian (BRIN, ITB, UGM, jurnal) | — | PDF/DOI | Kajian per kejadian | Belum diverifikasi | Bukan sumber operasional | **PERLU RISET** |

### 3.6 Abrasi dan Akresi

| Peran | Sumber | Endpoint / target | Akses & format | Data tersedia | Status | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|
| Kandidat resmi | Badan Geologi / BBSPGL (Geologi Kelautan) | Halaman Badan Geologi (`geologi.esdm.go.id` 200), publikasi | HTML/PDF | Peta & laporan pesisir | Halaman 200; **endpoint data belum ditemukan** | Tidak ada feed/API terverifikasi | **PERLU RISET** |
| Kandidat resmi | KKP / BIG (garis pantai) | Belum diverifikasi | — | Data geospasial | **BELUM DIVERIFIKASI** | Jangan diasumsikan tersedia | **PERLU RISET** |
| Pendukung | Mongabay Indonesia | `https://www.mongabay.co.id/feed/` | RSS | Ringkasan | 200; robots mengizinkan | Artikel, bukan data | **SUMBER PENDUKUNG** |
| Pendukung | ANTARA Warta Bumi | `https://www.antaranews.com/rss/warta-bumi.xml` | RSS | Ringkasan | 200 | Artikel | **SUMBER PENDUKUNG** |
| Pendukung | Laporan penelitian pesisir (BRIN, IPB, UNDIP) | — | PDF/DOI | Kajian lokal | Belum diverifikasi | Tidak real-time | **PERLU RISET** |
| Historis | Dataset lama | `data/geohazard_news.csv` | CSV | 3 baris `Abrasi dan Akresi` | Ada | Sangat sedikit; bukan sumber baru | **SUMBER PENDUKUNG** |

### 3.7 Penurunan Muka Tanah

| Peran | Sumber | Endpoint / target | Akses & format | Data tersedia | Status | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|
| Kandidat resmi | Badan Geologi — PATGTL | `https://geologi.esdm.go.id/patgtl` | HTML | Profil & publikasi | 200 | **Tidak ada endpoint terstruktur** | **PERLU RISET** |
| Kandidat resmi | BIG / BRIN (InSAR, geodesi) | Belum diverifikasi | — | Data geospasial | **BELUM DIVERIFIKASI** | Jangan diasumsikan tersedia | **PERLU RISET** |
| Pendukung | Artikel berita | feed terdaftar | RSS | Ringkasan | 200 | Sangat jarang; deteksi `amblesan`/`subsidence` | **SUMBER PENDUKUNG** |
| Pendukung | Laporan penelitian geodesi (ITB, UGM, BIG) | — | PDF/DOI | Kajian lokal | Belum diverifikasi | Tidak real-time | **PERLU RISET** |

### 3.8 Semburan Gas dan Lumpur

| Peran | Sumber | Endpoint / target | Akses & format | Data tersedia | Status | Keterbatasan | Keputusan |
|---|---|---|---|---|---|---|---|
| Kandidat resmi | Badan Geologi (bahaya geologi) | Halaman Badan Geologi | HTML/PDF | Laporan | Halaman 200; endpoint data belum ditemukan | Tidak ada feed/API terverifikasi | **PERLU RISET** |
| Kandidat resmi | BPLS (Badan Penanggulangan Lumpur Sidoarjo) | Belum diverifikasi | — | Data historis | **BELUM DIVERIFIKASI** | Jangan diasumsikan tersedia | **PERLU RISET** |
| Pendukung | Artikel berita | feed terdaftar | RSS | Ringkasan | 200 | Artikel; deteksi `semburan lumpur`/`mud volcano` | **SUMBER PENDUKUNG** |
| Historis | Laporan/riset | — | PDF/DOI | Kajian | Belum diverifikasi | Tidak real-time | **PERLU RISET** |

---

## 4. Evaluasi Feed Berita yang Sudah Terdaftar

Semua feed di bawah merespons HTTP 200 pada audit, **tetapi akses URL bukan izin**. Status: **SUMBER PENDUKUNG** — hanya kandidat artikel berita, tidak untuk data kejadian resmi.

| Feed | Relevansi 8 kategori | Catatan |
|---|---|---|
| ANTARA — Warta Bumi | Tinggi (gunung api, gempa, longsor, pesisir) | Kanal paling relevan |
| ANTARA — Terkini / Top News | Sedang | Umum; perlu filter ketat |
| ANTARA Jatim — Nasional | Sedang | Umum |
| detikcom — Berita | Sedang | Umum |
| CNN Indonesia — Nasional | Sedang | Umum |
| CNBC Indonesia — News | Sedang | Umum |
| Tempo — Nasional | Sedang | `ai-train=no` pada konten sinyal; **BELUM DIVERIFIKASI** untuk penggunaan lain |
| Liputan6 — Peristiwa | Sedang | Umum |
| Republika — Utama | Sedang | `/feed/*` dilarang; `/rss` dipakai |
| Media Indonesia | Sedang | Umum |
| SINDOnews — Terkini | Sedang | `Disallow:` kosong; **bukan** berarti izin |
| kumparan — Terkini | Sedang | Umum |
| BBC Indonesia | Rendah–sedang | Umum |
| Mongabay Indonesia | Tinggi (longsor, pesisir) | Lingkungan |

**Tidak dipertimbangkan:** `bmkg_nowcast_id` (`/alerts/...` — di luar 8 kategori **dan** dilarang `robots.txt`).

---

## 5. Rencana Pencarian Sumber untuk 4 Kategori Kosong

Prinsip: **resmi → laporan penelitian → artikel berita → data historis**, tanpa mengisi dengan sumber tak relevan.

| Kategori | Langkah 1 — resmi | Langkah 2 — penelitian | Langkah 3 — berita | Langkah 4 — historis |
|---|---|---|---|---|
| **Likuefaksi** | Periksa nilai `event_type` pada Portal MBG `get-field-reports` (setelah izin); cari peta zona kerentanan likuefaksi Badan Geologi/PVMBG; laporan investigasi gempa (Palu 2018, Cianjur 2022) | Publikasi BRIN/ITB/UGM; jurnal geoteknik | Keyword `likuefaksi`, `liquefaction` pada feed terdaftar | Katalog USGS + laporan lapangan |
| **Abrasi/Akresi** | BBSPGL (Geologi Kelautan); KKP; BIG garis pantai | BRIN/IPB/UNDIP kajian pesisir | Mongabay, ANTARA | Publikasi BBSPGL |
| **Penurunan Muka Tanah** | PATGTL Badan Geologi (`geologi.esdm.go.id/patgtl`); BIG/BRIN InSAR | ITB/UGM geodesi; jurnal | Keyword `amblesan`, `penurunan muka tanah`, `subsidence` | Laporan tahunan |
| **Semburan Gas/Lumpur** | Badan Geologi; BPLS (Sidoarjo) | Riset geologi/geofisika | Keyword `semburan lumpur`, `semburan gas`, `mud volcano` | Laporan historis |

**Aturan:** setiap kandidat baru wajib melewati uji akses + pemeriksaan ketentuan sebelum masuk daftar. Selama belum, status tetap `PERLU RISET` / `BELUM DIVERIFIKASI`.

---

## 6. Daftar Endpoint & Bukti Verifikasi

Diuji 22 Oktober 2026; detail di `data/uji_akses_sumber_2026-10-22.json`.

| Endpoint | HTTP | Format | Status |
|---|---:|---|---|
| `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml` | 200 | XML | ✅ |
| `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json` | 200 | JSON | ✅ |
| `https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.xml` | 200 | XML | ✅ |
| `https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json` | 200 | JSON | ✅ |
| `https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.xml` | 200 | XML | ✅ |
| `https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json` | 200 | JSON | ✅ |
| `https://www.bmkg.go.id/alerts/nowcast/id/rss.xml` | 200 | RSS | ⛔ dilarang robots; di luar cakupan |
| `https://www.bmkg.go.id/gempabumi/berpotensi-tsunami` | 200 | HTML | ✅ |
| `https://www.bmkg.go.id/berita` | 200 | HTML | ✅ |
| `https://vsi.esdm.go.id/data/api/public/press-release` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/data/api/public/press-release/{route}` | 200 | JSON (isi HTML) | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/data/api/public/gunung-api/data-dasar` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/tingkat-aktivitas/apis/get` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/laporan-singkat/apis/get` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/kajian-kejadian/apis/get` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/gerakan-tanah?category_id=3` | 200 | HTML/JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/gerakan-tanah?category_id=1` | 200 | HTML/JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/portalmbg/api/get-field-reports` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/portalmbg/api/get-destructive-earthquake` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/portalmbg/api/sigab` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/portalmbg/api/get-volcano-magma` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/portalmbg/api/get-lews-stations` | 200 | JSON | 🔒 menunggu izin |
| `https://vsi.esdm.go.id/portalmbg/api/get-province` | **403** | JSON | ❌ gagal |
| `https://magma.esdm.go.id/v1/gunung-api/informasi-letusan` | 200 | HTML | 🔒 menunggu izin |
| `https://magma.esdm.go.id/v1/gunung-api/informasi-letusan/AGU` | 200 | HTML | 🔒 menunggu izin |
| `https://magma.esdm.go.id/v1/gunung-api/laporan-harian` | 200 | HTML | 🔒 menunggu izin |
| `https://magma.esdm.go.id/v1/gunung-api/tingkat-aktivitas` | 200 | HTML | 🔒 menunggu izin |
| `https://magma.esdm.go.id/v1/gunung-api/laporan` | 200 | HTML | 🔒 menunggu izin |
| `https://geologi.esdm.go.id/profil/arsip-berita` | 200 | HTML | ✅ (nilai rendah) |
| `https://geologi.esdm.go.id/pelayanan-publik/geohazard` | 200 | HTML | ✅ |
| `https://geologi.esdm.go.id/patgtl` | 200 | HTML | ✅ (tanpa endpoint data) |
| `https://www.esdm.go.id/id/media-center/arsip-berita` | 200 | HTML | ✅ (nilai rendah) |
| `https://earthquake.usgs.gov/fdsnws/event/1/query?...` | 200 | GeoJSON | ✅ internasional |
| `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.atom` | 200 | Atom | ✅ internasional |
| `https://www.gdacs.org/xml/rss.xml` | 200 | RSS | ✅ internasional, batas ketat |
| `https://api.reliefweb.int/v2/disasters?appname=...` | **403** | JSON | ❌ butuh appname terdaftar |
| `https://bnpb.go.id/berita` | **403** | HTML | ❌ Cloudflare |
| `https://dibi.bnpb.go.id/` | 200 | HTML | ⚠️ halaman 200; API **403** |
| `https://www.emsifa.com/api-wilayah-indonesia/api/provinces.json` | 200 | JSON | ✅ referensi wilayah (bukan gazetteer resmi) |

---

## 7. Daftar Sumber yang Boleh Dipertimbangkan untuk Aktivasi

| Sumber | Peran | Alasan | Syarat |
|---|---|---|---|
| BMKG Open Data (3 XML + 3 JSON) | Utama resmi — Gempa, Tsunami | 200, Data Terbuka, tanpa `robots.txt` | Atribusi BMKG; parsing XML/JSON |
| USGS FDSN Event API | Internasional pendukung | 200, API publik | Filter bbox Indonesia; bukan resmi RI |
| GDACS RSS | Internasional pendukung | 200 | Rate 1/60 dtk, jendela 04:00–06:45 UTC |
| BMKG `/berita` | Pendukung naratif | 200, tidak dilarang | Parser HTML; bukan data kejadian |
| 14 feed berita terdaftar | Pendukung artikel | 200 | Hanya `news_article`; lisensi **BELUM DIVERIFIKASI** |

---

## 8. Daftar Sumber yang Menunggu Izin

| Sumber | Domain | Alasan |
|---|---|---|
| PVMBG API publik (press-release, data-dasar, tingkat-aktivitas, laporan-singkat, kajian-kejadian) | `vsi.esdm.go.id` | `robots.txt` `Disallow: /` |
| Portal MBG (field-reports, destructive-earthquake, sigab, volcano-magma, lews-stations) | `vsi.esdm.go.id` | `robots.txt` `Disallow: /` |
| MAGMA (informasi-letusan, laporan-harian, tingkat-aktivitas, laporan) | `magma.esdm.go.id` | `robots.txt` `Disallow: /` |

**Jangan aktifkan otomatisasi sampai ada konfirmasi tertulis.**

---

## 9. Daftar Sumber yang Tidak Dipertimbangkan

| Sumber | Alasan |
|---|---|
| `bmkg_nowcast_id` (`/alerts/...`) | Di luar 8 kategori **dan** dilarang `robots.txt` |
| `bmkg.go.id/api`, `/alerts` | Dilarang `robots.txt` |
| ReliefWeb v1 | 410 Gone |
| ReliefWeb v2 tanpa appname | 403 |
| BNPB `/berita` | 403 Cloudflare |
| BNPB DIBI API | 403 |
| Halaman Badan Geologi "media-center" | 22 Okt 2026 isinya non-hazard (museum, vaksin HPV) |
| Scraping massal feed berita | Tidak ada izin eksplisit; risiko |

---

## 10. Kekurangan Sumber per Kategori

| Kategori | Kekurangan | Dampak |
|---|---|---|
| Gunungapi | Semua sumber kuat **menunggu izin** | Tidak bisa otomatis sekarang |
| Gempabumi | BMKG hanya 1/15/15 item (bukan arsip); butuh arsip historis | Riwayat terbatas |
| Tsunami | Tidak ada feed peringatan tsunami mandiri yang boleh diakses | Hanya dari `Potensi` gempa |
| Gerakan Tanah | Portal MBG titik ≠ kejadian; 619 laporan/363 tanggal; lokasi teks rendah | Dedup & lokasi sulit |
| Likuefaksi | Tidak ada sumber terstruktur | **0 cakupan** |
| Abrasi/Akresi | Tidak ada sumber terstruktur; hanya berita | **0 cakupan baru** |
| Penurunan Muka Tanah | PATGTL hanya halaman; tanpa endpoint | **0 cakupan** |
| Semburan Gas/Lumpur | Tidak ada sumber terstruktur | **0 cakupan** |

**Dengan demikian, delapan kategori belum seluruhnya tercakup oleh sumber yang layak.**

---

## 11. Metadata Minimum Dataset

Satu tabel, dua nilai `data_type`: `official_event_report` | `news_article`.

| Kolom | Wajib | Tipe | Keterangan |
|---|---|---|---|
| `event_id` | ✅ | teks | ID internal; dedup kejadian, **bukan** 1 artikel = 1 kejadian |
| `data_type` | ✅ | enum | `official_event_report` / `news_article` |
| `hazard_category` | ✅ | enum | 8 kategori saja |
| `source_name` | ✅ | teks | Nama sumber |
| `source_type` | ✅ | enum | `official` / `international` / `news` |
| `source_url` | ✅ | teks | URL asli |
| `title` | ✅ | teks | Judul |
| `event_time` | ✅ | datetime | **Kosongkan jika sumber tidak menyebut**; jangan dikarang |
| `published_time` | ✅ | datetime | Waktu publikasi |
| `collected_at` | ✅ | datetime | Waktu pengambilan |
| `province` | ✅ | teks | |
| `regency_city` | ✅ | teks | |
| `district` | ✅ | teks | |
| `village` | ✅ | teks | |
| `hamlet` | ✅ | teks | |
| `rw` | ✅ | teks | |
| `rt` | ✅ | teks | |
| `address_detail` | ✅ | teks | |
| `latitude` | ✅ | desimal | Null bila tidak ada; **jangan dikarang** |
| `longitude` | ✅ | desimal | Null bila tidak ada; **jangan dikarang** |
| `location_confidence` | ✅ | enum | `exact` / `admin` / `approx` / `none` |
| `magnitude` | ◐ | desimal | Untuk gempa; null untuk kategori lain |
| `status` | ◐ | teks | Status gunung api / peringatan |
| `description` | ✅ | teks | Isi resmi atau ringkasan artikel |
| `raw_payload` | ◐ | teks | Opsional: JSON/XML asli untuk audit |

Aturan: `news_article` tidak boleh mengisi `latitude`/`longitude` tanpa metode geocoding yang tercatat di `location_confidence`.

---

## 12. Contoh Rancangan Tabel Data (DUMMY — bukan data nyata)

> Nilai di bawah **ilustrasi format**, bukan kejadian sebenarnya. Satu tabel, dibedakan `data_type`.

| Field | Contoh `official_event_report` | Contoh `news_article` |
|---|---|---|
| `event_id` | `CONTOH-EQ-001` | `CONTOH-NEWS-001` |
| `data_type` | `official_event_report` | `news_article` |
| `hazard_category` | `Gempabumi` | `Gerakan Tanah / Tanah Longsor` |
| `source_name` | `BMKG` | `ANTARA` |
| `source_type` | `official` | `news` |
| `source_url` | `https://data.bmkg.go.id/...` | `https://www.antaranews.com/...` |
| `title` | `<judul dari sumber>` | `<judul artikel>` |
| `event_time` | `<Tanggal+Jam>` | `NULL` (tidak disebut) |
| `published_time` | `NULL` (tidak ada field) | `<pubDate>` |
| `collected_at` | `2026-10-22T...` | `2026-10-22T...` |
| `province` | `<Wilayah>` | `<hasil ekstraksi>` |
| `regency_city` | `NULL` | `<hasil ekstraksi>` |
| `district` / `village` / `hamlet` | `NULL` | `NULL` |
| `rw` / `rt` | `NULL` | `NULL` |
| `address_detail` | `NULL` | `NULL` |
| `latitude` | `<Lintang>` | `NULL` |
| `longitude` | `<Bujur>` | `NULL` |
| `location_confidence` | `exact` | `admin` |
| `magnitude` | `<Magnitudo>` | `NULL` |
| `status` | `NULL` | `NULL` |
| `description` | `<Wilayah + Potensi>` | `<ringkasan RSS>` |
| `raw_payload` | `<XML asli>` | `<RSS asli>` |

**Prinsip:** baris `official_event_report` dan `news_article` boleh merujuk kejadian yang sama, tetapi **tidak digabung otomatis**; `event_id` yang menghubungkan, bukan URL.

---

## 13. Keputusan yang Masih Membutuhkan Persetujuan

1. **Izin PVMBG/MAGMA/Portal MBG** — ajukan sekarang, atau tunda dan jalankan hanya BMKG/USGS/GDACS?
2. **Baris lama di luar cakupan** (Karhutla 71 + Cuaca Ekstrem 14) — dipertahankan apa adanya, diberi penanda `out_of_scope`, atau dipisah ke file arsip?
3. **Sumber berita** — setujui 14 feed sebagai `SUMBER PENDUKUNG`, atau persempit ke ANTARA Warta Bumi + Mongabay saja?
4. **GDACS** — setujui dengan batas 1 request/60 dtk dan jendela 04:00–06:45 UTC, atau lewati?
5. **Backfill** — 787 baris lama boleh diperkaya (koordinat/`data_type`), atau hanya data baru memakai skema baru?
6. **`location_confidence`** — definisi ambang `exact`/`admin`/`approx` perlu disepakati sebelum implementasi.
7. **Status 4 kategori kosong** — terima `PERLU RISET` untuk sementara, atau prioritaskan salah satu untuk riset mendalam?
8. **Verifikasi lisensi berita** — perlu keputusan apakah akan menghubungi penerbit atau membatasi ke kutipan/atribusi.

---

*Dokumen ini berhenti pada keputusan sumber. Tidak ada kode, database, atau dataset yang diubah.*
