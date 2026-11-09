# Konfigurasi Sumber Final — GeoHazard News Locator

Dokumen ini merangkum konfigurasi sumber aktif dan cakupan 8 kategori wajib proyek. Isinya disusun dari `feeds.py` saat ini serta dokumen yang sudah ada: `AUDIT_SUMBER_DATA_2026-10-22.md`, `SOURCE_DECISIONS_DRAFT.md`, dan bukti `data/uji_akses_sumber_2026-10-22.json`.

Dokumen ini bukan audit baru. Tidak ada scraper yang dijalankan, tidak ada request internet, dan tidak ada perubahan pada `feeds.py`, dataset, CSV, atau pipeline.

## 1. Ringkasan

- Ada **7 feed aktif**.
- **3 feed** berasal dari BMKG dan berstatus sumber resmi Indonesia.
- **2 feed** berasal dari USGS dan GDACS; keduanya sumber internasional pendukung, **bukan sumber resmi Indonesia**.
- **2 feed** berasal dari ANTARA Warta Bumi dan Mongabay; keduanya sumber berita pendukung, **bukan sumber utama resmi**.
- Hanya **Gempabumi** yang memiliki sumber utama resmi aktif.
- **Tsunami** hanya tercakup terbatas melalui informasi potensi tsunami pada data BMKG, bukan sebagai sumber tsunami penuh.
- Enam kategori lainnya belum memiliki sumber utama aktif yang boleh digunakan saat ini.

## 2. Tujuh Feed Aktif

| No | ID aktual | Sumber | Tipe | Endpoint | Peran |
|---:|---|---|---|---|---|
| 1 | `bmkg_autogempa` | BMKG | `bmkg_xml` | `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml` | Sumber resmi Indonesia |
| 2 | `bmkg_gempa_terkini` | BMKG | `bmkg_xml` | `https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.xml` | Sumber resmi Indonesia |
| 3 | `bmkg_gempa_dirasakan` | BMKG | `bmkg_xml` | `https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.xml` | Sumber resmi Indonesia |
| 4 | `usgs_m45` | USGS | `rss` | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.atom` | Sumber internasional pendukung |
| 5 | `gdacs_all` | GDACS | `rss` | `https://www.gdacs.org/xml/rss.xml` | Sumber internasional pendukung |
| 6 | `antaranews_warta_bumi` | ANTARA | `rss` | `https://www.antaranews.com/rss/warta-bumi.xml` | Sumber berita pendukung |
| 7 | `mongabay_indonesia` | Mongabay | `rss` | `https://www.mongabay.co.id/feed/` | Sumber berita pendukung |

Catatan: ID aktual di project adalah `bmkg_gempa_dirasakan`. ID tersebut dipertahankan agar konfigurasi dan referensi lama tidak berubah.

## 3. Klasifikasi Sumber

- **Sumber resmi Indonesia:** BMKG dan PVMBG/MAGMA. Dari keduanya, hanya BMKG yang memiliki feed aktif saat ini.
- **Sumber internasional:** USGS dan GDACS. Keduanya tidak dianggap sebagai sumber resmi Indonesia.
- **Sumber berita:** ANTARA, ANTARA Jatim, detikcom, CNN Indonesia, CNBC Indonesia, Tempo, Liputan6, Republika, Media Indonesia, SINDOnews, kumparan, BBC Indonesia, dan Mongabay. Hanya ANTARA Warta Bumi dan Mongabay yang aktif.
- Tidak ditemukan mekanisme `official_event_report`/`news_article` pada konfigurasi saat ini; dokumen ini tidak menambahkan mekanisme tersebut.

## 4. Matriks 8 Kategori Wajib

| Kategori | Sumber utama aktif | Status | Bukti/dukungan yang tercatat | Batas klaim |
|---|---|---|---|---|
| Gunungapi | Tidak ada | **Belum memiliki sumber utama aktif** | PVMBG API/MAGMA/Portal MBG menunggu izin; berita hanya pendukung | Tidak ada otomatisasi PVMBG/MAGMA/Portal MBG saat ini |
| Gempabumi | BMKG Open Data (`bmkg_autogempa`, `bmkg_gempa_terkini`, `bmkg_gempa_dirasakan`) | **Sumber utama BMKG tersedia** | USGS dan GDACS sebagai pendukung internasional | Koordinat, magnitudo, dan kedalaman bergantung pada isi feed |
| Tsunami | BMKG Open Data melalui field `Potensi` | **Cakupan terbatas; bukan sumber tsunami penuh** | Informasi potensi tsunami pada data gempa BMKG; USGS/GDACS hanya pendukung | Tidak ada feed peringatan tsunami mandiri yang aktif |
| Gerakan Tanah/Tanah Longsor | Tidak ada | **Belum memiliki sumber utama aktif** | Portal MBG menunggu izin; ANTARA dan Mongabay hanya berita pendukung | Jangan menyebut berita sebagai sumber utama resmi |
| Likuefaksi | Tidak ada | **Belum memiliki sumber utama aktif** | Belum ditemukan sumber terstruktur terverifikasi; berita hanya pendukung | Status sumber resmi belum terbukti |
| Abrasi dan Akresi | Tidak ada | **Belum memiliki sumber utama aktif** | Belum ditemukan sumber terstruktur terverifikasi; berita hanya pendukung | Status sumber resmi belum terbukti |
| Penurunan Muka Tanah | Tidak ada | **Belum memiliki sumber utama aktif** | Belum ditemukan sumber terstruktur terverifikasi; berita hanya pendukung | Status sumber resmi belum terbukti |
| Semburan Gas dan Lumpur | Tidak ada | **Belum memiliki sumber utama aktif** | Belum ditemukan sumber terstruktur terverifikasi; berita hanya pendukung | Status sumber resmi belum terbukti |

Sumber berita pendukung tidak boleh disebut sebagai sumber utama resmi. Ketersediaan artikel atau akses HTTP bukan bukti izin, cakupan penuh, atau status sumber utama.

## 5. Sumber Terlarang dan Menunggu Izin

- `bmkg_nowcast_id` **tidak boleh digunakan**. Endpoint `/alerts/` dilarang dan feed ini nonaktif.
- PVMBG API, Portal MBG, dan MAGMA **menunggu izin tertulis**. Tidak ada otomatisasi sampai izin tersebut tercatat.
- `pvmbg_magma` tetap nonaktif.
- Endpoint BMKG `/api/*`, BNPB, ReliefWeb, dan Portal MBG `get-province` tidak ditambahkan ke konfigurasi aktif.
- Tidak ada klaim bahwa izin sudah diperoleh.

## 6. Batas Dokumen

- Dokumen ini tidak mengubah konfigurasi, dataset, CSV, laporan audit, atau pipeline.
- Status kategori mengikuti bukti yang sudah tercatat; kategori tanpa sumber utama aktif tidak boleh ditulis sebagai sudah tercakup penuh.
- Perubahan status hanya boleh dilakukan setelah ada bukti akses, ketentuan penggunaan, dan izin yang sesuai.
