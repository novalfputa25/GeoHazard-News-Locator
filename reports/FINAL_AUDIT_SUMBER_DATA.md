# Final Audit Sumber Data

Tanggal audit: **2026-11-02**  
Cakupan: sumber aktif, kandidat sumber resmi, portal/peta pendukung, dan sumber historis di dataset final.  
Register pendamping: `docs/MASTER_SOURCE_REGISTER.csv` (54 baris sumber/URL yang dievaluasi).

## 1. Ringkasan eksekutif

- Hanya **7 feed** yang benar-benar aktif: 3 XML BMKG, USGS Atom, GDACS RSS, ANTARA Warta Bumi, dan Mongabay.
- Dari 54 baris register: **7 `TERVERIFIKASI_AKTIF`**, **25 `TERVERIFIKASI_MANUAL`**, **14 `PERLU_IZIN`**, **6 `BELUM_TERSEDIA`**, dan **2 `TIDAK_SESUAI`**.
- Feed aktif yang menyediakan kejadian terstruktur hanyalah BMKG, USGS, dan GDACS. ANTARA dan Mongabay adalah berita pendukung, bukan laporan kejadian resmi.
- Sumber resmi Indonesia untuk gunung api, gerakan tanah, dan likuefaksi sangat relevan, tetapi endpoint PVMBG/MAGMA/Portal MBG berada di balik `robots.txt` yang melarang akses dan membutuhkan izin tertulis.
- DIBI BNPB hanya terverifikasi sebagai dashboard manual; tidak ada API kejadian individual yang terdokumentasi dan berhasil diuji. Portal Satu Data BNPB mengembalikan **403**.
- Peta risiko BNPB/BIG tidak boleh dianggap sebagai umpan kejadian. Katalog InaRISK menampilkan 160 service, tetapi service likuefaksi/abrasi yang diuji mengembalikan **521**; layer `TanahLongsor_2022` adalah layer statis, bukan data terkini.
- Tidak ada bypass autentikasi, CAPTCHA, atau akses paksa. Pengujian dilakukan dengan satu GET per URL dan jeda sekitar 1,2 detik.
- **Dataset final belum boleh disebut tervalidasi penuh** hanya karena audit sumber selesai.

## 2. Metode dan batas bukti

1. URL diuji dengan `GET` aman, bukan POST, tanpa login, dan tanpa mencoba menembus proteksi.
2. Hasil yang dicatat adalah status HTTP, tipe konten, jumlah item/entry yang terlihat, dan judul halaman bila tersedia.
3. Uji 2026-11-02 adalah snapshot sesaat; status 200 tidak menjamin ketersediaan permanen, lisensi, atau izin penggunaan.
4. Untuk sumber yang sudah diaudit pada 2026-10-22, hasil lama dipakai hanya sebagai bukti historis dan ditandai tanggalnya di register.
5. `robots.txt` yang tidak dapat dibaca karena SSL/HTTPError tidak dianggap sebagai izin otomatis.
6. Berita tidak dianggap bukti kejadian; status sumber berita tetap `berita_pendukung`.
7. Peta risiko, atlas, dan publikasi tidak dianggap feed kejadian.

## 3. Sumber aktif yang terverifikasi

| Source ID | Sumber | Hasil uji 2026-11-02 | Peran |
|---|---|---|---|
| `bmkg_autogempa` | BMKG Autogempa XML | 200; XML `Infogempa`; 1 item gempa | Resmi utama, gempa terbaru |
| `bmkg_gempa_terkini` | BMKG Gempa Terkini XML | 200; 15 item gempa | Resmi utama, jendela terbatas |
| `bmkg_gempa_dirasakan` | BMKG Gempa Dirasakan XML | 200; 15 item gempa | Resmi utama, dampak dirasakan |
| `usgs_m45` | USGS M4.5+ Atom | 200; 21 entry | Internasional pendukung |
| `gdacs_all` | GDACS RSS | 200; RSS ±866 KB; 98 item dalam sampel 300 KB | Internasional pendukung, multibahaya |
| `antaranews_warta_bumi` | ANTARA Warta Bumi | 200; 20 item; 33.059 byte | Berita pendukung |
| `mongabay_indonesia` | Mongabay Indonesia | 200; 20 item; 84.945 byte | Berita pendukung |

Catatan penting:

- ANTARA gagal di Python `urllib` karena `CERTIFICATE_VERIFY_FAILED`, tetapi berhasil dengan `curl.exe` 200. Kegagalan TLS klien tidak boleh dicatat sebagai sumber mati.
- GDACS adalah agregator internasional, bukan sumber resmi Indonesia.
- USGS mencakup gempa global; 9 dari 40 koordinat pada dataset berasal dari luar Indonesia.
- Feed BMKG adalah jendela terbatas, bukan arsip historis. Untuk arsip diperlukan sumber resmi tambahan atau penyimpanan snapshot yang sah.
- `data.bmkg.go.id/robots.txt` tidak terbaca (SSL/HTTPError). Gunakan hanya endpoint resmi yang sudah diketahui, dengan laju rendah dan tanpa scraping agresif.

## 4. Sumber resmi yang memerlukan izin

Semua endpoint PVMBG, Portal MBG, dan MAGMA di bawah ini **tidak boleh diaktifkan otomatis** sebelum ada izin tertulis dan kesepakatan lisensi.

| Kelompok | Bukti lama | Keterbatasan |
|---|---|---|
| PVMBG API publik | 200 pada 2026-10-22; `press-release` 299 item, `kajian-kejadian` 749 item | `vsi.esdm.go.id/robots.txt` melarang seluruh situs |
| Portal MBG | 200 pada 2026-10-22; `field-reports` 2.397 titik, 619 `doc_id`, 363 tanggal unik | Banyak titik per laporan; perlu deduplikasi dan izin |
| Portal MBG gempa merusak | 200; 357 record; 29 bertanda tsunami | Field koordinat/waktu perlu diverifikasi; bukan umpan real-time |
| Portal MBG SIGAB | 200; 5 item | Jumlah sangat kecil; semantik field belum jelas |
| MAGMA | 200 HTML untuk informasi letusan, laporan, level, VONA | Tidak ada API publik terdokumentasi; parser HTML rapuh |
| PVMBG gerakan tanah | 200; rekap 2011–2012 | Sangat terbatas; bukan data terkini |

Keputusan: statusnya tetap **`PERLU_IZIN`**, bukan “tersedia”. Jangan menggunakan endpoint ini sebagai justifikasi bahwa seluruh 8 kategori sudah tercakup.

## 5. Portal, dashboard, peta, dan katalog

| Sumber | Hasil | Kesimpulan |
|---|---|---|
| DIBI BNPB dashboard | 200 HTML; judul “Data Informasi Bencana Indonesia” | Manual; tidak ada API kejadian individual yang terbukti |
| Portal Satu Data BNPB | 403 Cloudflare | Tidak dapat diverifikasi; bukan bukti API tersedia |
| BNPB InaRISK katalog | 200; 160 service; versi 11.4 | Katalog peta risiko, bukan feed kejadian |
| BNPB `TanahLongsor_2022` | 200; layer point; query count 500 | Statis 2022; tidak layak sebagai umpan terkini |
| InaRISK likuefaksi | 521 | Tidak dapat dipakai saat uji |
| InaRISK abrasi | 521 | Tidak dapat dipakai saat uji |
| BIG Atlas Kebencanaan | 200; 26 layer | Peta risiko/sesar/tsunami, bukan feed kejadian |
| BIG Ina-Geoportal | 200 HTML | Portal web; bukan API kejadian siap pakai |
| BPLS Sidoarjo | 200 HTML | Informasi manual; bukan katalog kejadian |
| Badan Geologi PATGTL/GeoHazard | 200 HTML | Profil/publikasi; tidak ada endpoint kejadian |
| Atlas likuefaksi Badan Geologi | Halaman publikasi 2019 ditemukan; GET langsung timeout | Tidak dapat diklaim aktif; peta risiko, bukan kejadian |
| KKP root | 200 HTML | Portal berita/publikasi; bukan feed abrasi |
| BPISDKP abrasi | Redirect ke `/abrasi-akresi/` → 404 | Tidak tersedia |
| ReliefWeb API v2 | 403 | Perlu appname terdaftar; bukan sumber resmi RI |
| emsifa/wilayah.id | 200; 34 provinsi | Gazetteer pihak ketiga; tidak sesuai sebagai sumber kejadian |

## 6. Robots, etika, dan kepatuhan

- **Diizinkan:** ANTARA (dengan pengecualian `/ajax/*` dan `/ucnews/*`), GDACS, Mongabay, DIBI, `data.bnpb.go.id`, `gis.bnpb.go.id`, `sda.pu.go.id`, dan `geologi.esdm.go.id`.
- **Dilarang:** `vsi.esdm.go.id`, `magma.esdm.go.id`, dan BMKG `/alerts/` (nowcast).
- **Tidak terbaca:** `data.bmkg.go.id` dan endpoint BIG terkait.
- **Tidak ditemukan/404:** USGS dan KKP.
- Sumber berita tetap tunduk pada syarat situs, hak cipta, dan atribusi. Status HTTP 200 bukan izin redistribusi.
- Jangan menyimpan atau menayangkan ulang isi berita secara penuh tanpa dasar lisensi.

## 7. Hubungan dengan dataset final

Dataset `data/geohazard_news_final_20261101T150501Z.csv` memiliki 16 label sumber historis, sedangkan konfigurasi aktif hanya 7 feed. Komposisi sumber final:

| Sumber | Baris |
|---|---:|
| detikcom | 100 |
| CNN Indonesia | 100 |
| CNBC Indonesia | 100 |
| Media Indonesia | 100 |
| ANTARA | 97 |
| Tempo | 50 |
| Liputan6 | 50 |
| BMKG | 38 |
| SINDOnews | 30 |
| kumparan | 25 |
| BBC Indonesia | 21 |
| ANTARA Jatim | 20 |
| Mongabay | 20 |
| Republika | 15 |
| USGS | 11 |
| GDACS | 10 |

Implikasi:

- Sebagian besar baris berasal dari berita umum, bukan feed resmi.
- Dataset final tidak menyimpan `source_id`, `source_type`, `collected_at`, `run_id`, atau `raw_payload`, sehingga provenance tidak dapat ditelusuri sampai tingkat feed/run.
- 13 feed RSS historis di register tidak aktif di `feeds.py`; jangan menyalakannya kembali tanpa audit lisensi dan kualitas.
- CNBC Indonesia memiliki 100 baris, tetapi tidak menyumbang satu pun baris pada 4 kategori target yang terisi.

## 8. Temuan kunci

1. **Kesenjangan kategori jauh lebih besar daripada kesenjangan jumlah baris.** Hanya Gempabumi yang memiliki sumber resmi terstruktur aktif; kategori lain tidak.
2. **Sumber resmi terbaik untuk Gunungapi, Gerakan Tanah, dan Likuefaksi memerlukan izin.** Tidak ada jalur otomatis yang sah saat ini.
3. **DIBI/Portal Satu Data belum terbukti menyediakan data kejadian individual.** Dashboard dan katalog tidak sama dengan API kejadian.
4. **Peta risiko bukan feed kejadian.** InaRISK/BIG dapat mendukung konteks, tetapi tidak boleh menambah hitungan kejadian.
5. **Tidak ada feed tsunami terpisah.** BMKG hanya menyediakan field potensi pada data gempa; 15 baris Gempabumi menyebut tsunami, tetapi bukan kejadian tsunami terpisah.
6. **Kualitas provenance belum memadai untuk operasional.** Diperlukan penambahan field sumber dan run sebelum dataset baru dapat dirilis.
7. **Ada kandidat underclassification.** Contoh jelas: “Status Gunung Sinabung Turun dari Level Siaga Jadi Waspada” masih `Lainnya`; ini perlu review manual, bukan reklasifikasi otomatis.

## 9. Rekomendasi

### P0 — sebelum menambah data

- Ajukan izin tertulis dan kesepakatan lisensi ke PVMBG/Badan Geologi untuk API/Portal MBG/MAGMA.
- Verifikasi dengan BNPB apakah DIBI menyediakan API individual, ekspor resmi, atau hanya dashboard; jangan mengandalkan dashboard sebagai sumber otomatis.
- Tetapkan kebijakan hukum untuk ANTARA, Mongabay, dan feed berita historis.
- Bekukan baseline dan catat setiap sumber baru dalam register sebelum diaktifkan.

### P1 — perbaikan pipeline

- Tambahkan `source_id`, `source_type`, `data_type`, `collected_at`, `run_id`, `event_id`, `raw_payload`, dan `license`.
- Bedakan `event_feed`, `news`, `risk_map`, `publication`, dan `gazetteer`.
- Simpan snapshot mentah dan hash respons untuk audit.
- Tingkatkan ekstraksi `event_time` hanya bila ada bukti eksplisit; jangan memakai `published_time`.
- Validasi koordinat dan bedakan lokasi kejadian dari lokasi administratif yang disebut.

### P2 — riset sumber

- Cari sumber resmi/struktural untuk Gerakan Tanah, Likuefaksi, Abrasi, Penurunan Muka Tanah, dan Semburan.
- Evaluasi laporan daerah/BNPB/KKP/Badan Geologi secara manual.
- Jangan mengotomatiskan peta risiko atau publikasi PDF sebagai pengganti feed kejadian.

## 10. Kesimpulan

Audit sumber menunjukkan bahwa konfigurasi 7 feed layak untuk **Gempabumi** dan berita pendukung, tetapi belum layak untuk mengklaim cakupan 8 kategori. Status yang benar saat ini adalah:

> **Sumber aktif terbatas; beberapa sumber resmi menjanjikan tetapi memerlukan izin; sebagian besar kategori belum memiliki feed kejadian yang terverifikasi.**

Dataset final harus diperlakukan sebagai baseline audit, bukan kumpulan kejadian bencana yang lengkap.

## 11. Rujukan

- `docs/MASTER_SOURCE_REGISTER.csv`
- `reports/MATRIKS_CAKUPAN_8_KATEGORI.md`
- `reports/AUDIT_KUALITAS_DATASET_FINAL.md`
- `reports/RENCANA_FINALISASI_DATASET.md`
- `reports/audit_sumber_magma.md`
- `AUDIT_SUMBER_DATA_2026-10-22.md`
- `SOURCE_DECISIONS_DRAFT.md`
- `docs/final_source_configuration.md`
- `data/uji_akses_sumber_2026-10-22.json`
