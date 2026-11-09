# Audit Sumber Data MAGMA Indonesia / PVMBG

- Tanggal audit: **2026-11-02**
- Status: **selesai; read-only**
- Ruang lingkup: akses publik MAGMA Indonesia, dokumentasi API, struktur data, dan cakupan 8 kategori GeoHazard News Locator
- Perubahan kode/dataset: **tidak ada**
- Scraper lama dijalankan: **tidak**
- Unit test penuh dijalankan: **tidak**

## 1. Kesimpulan Utama

MAGMA Indonesia adalah sumber resmi PVMBG/Badan Geologi yang kuat untuk **Gunungapi** dan berguna sebagai sumber pendukung untuk **Gempabumi**. Namun, MAGMA **belum dapat dijadikan sumber otomatis tunggal untuk 8 kategori**.

Temuan kunci:

1. **Tidak ditemukan dokumentasi API publik resmi** berupa OpenAPI/Swagger, Postman collection, dokumentasi autentikasi, batas laju, atau skema respons.
2. **API data utama tidak dapat diakses tanpa token.** Route API resmi di repo MAGMA menunjukkan grup `/api/v1` dilindungi `jwt.auth`; pengujian tanpa token menghasilkan **401 Unauthorized**.
3. Endpoint yang dideklarasikan publik di kode mengembalikan **500**:
   - `/api/status` -> `{"status":"false","code":500,"message":"Token Invalid"}`
   - `/api/vona` dan `/api/vona/latest` -> `{"message":"Server Error"}`
4. Halaman publik MAGMA tersedia sebagai **HTML**, bukan API JSON. Contoh halaman status, laporan aktivitas, informasi letusan, gerakan tanah, gempa bumi, VONA, dan LEWS mengembalikan **200 text/html**.
5. Cakupan kategori tidak merata:
   - **Gunungapi**: tersedia dan cukup kaya.
   - **Gempabumi**: tersedia, tetapi halaman kajian tidak real-time; kajian terbaru yang terlihat adalah **2026-04-08**.
   - **Tsunami**: hanya pembahasan potensi tsunami di kajian gempa; tidak ada data kejadian tsunami.
   - **Gerakan Tanah/Tanah Longsor**: ada laporan tanggapan, tetapi laporan terbaru yang terlihat adalah **2023-05-04**; LEWS hanya menampilkan daftar stasiun.
   - **Likuefaksi, Abrasi dan Akresi, Penurunan Muka Tanah, Semburan Gas dan Lumpur**: **BELUM DAPAT DIVERIFIKASI** sebagai data kejadian; tidak ditemukan halaman/data kejadian untuk kategori tersebut.
6. Informasi potensi/peringatan seperti KRB, LEWS, dan “Zona Potensi Gerakan Tanah” **bukan data kejadian aktual** dan tidak boleh diperlakukan sebagai event.

Kesimpulan kelayakan:

- **Layak sebagai sumber pendukung**, terutama untuk Gunungapi.
- **Belum layak sebagai sumber API otomatis produksi** tanpa kerja sama/akses token dari PVMBG.
- **Tidak layak sebagai sumber tunggal** untuk 8 kategori.
- Untuk Tsunami, Likuefaksi, Abrasi/Akresi, Penurunan Muka Tanah, dan Semburan Gas/Lumpur diperlukan sumber resmi lain.

## 2. Metode Audit

Audit dilakukan tanpa login dan tanpa token:

- Penelusuran halaman resmi MAGMA, halaman edukasi, artikel ESDM, dan repository resmi MAGMA.
- Pemeriksaan route API pada repository resmi untuk mengetahui kontrak akses yang dideklarasikan.
- HTTP GET terbatas ke URL resmi; satu URL diperiksa tanpa iterasi halaman, tanpa pagination, dan tanpa pengambilan massal.
- Pengujian endpoint API tanpa autentikasi untuk melihat respons yang tersedia bagi publik.
- Tidak ada upaya menebak endpoint, brute force, login, atau penggunaan kredensial.
- Tidak ada pengujian terhadap endpoint pihak ketiga sebagai dasar kesimpulan resmi.

Batasan:

- Tidak ada akses ke API internal/institusional.
- Tidak ada dokumentasi resmi API publik yang dapat diuji.
- Tidak ada evaluasi Terms of Use, lisensi, atau izin scraping.
- Tidak ada pengambilan sampel historis dalam jumlah besar.
- Halaman dinamis dapat berubah sewaktu-waktu.

## 3. URL Resmi yang Diperiksa

### 3.1 Portal dan informasi publik

| URL | Status | Content-Type | Catatan |
|---|---:|---|---|
| `https://magma.esdm.go.id/` | 200 | `text/html` | Portal MAGMA versi baru |
| `https://magma.esdm.go.id/v1` | 200 | `text/html` | Portal MAGMA v1/Laravel |
| `https://magma.esdm.go.id/v1/edukasi/magma-indonesia` | 200 | `text/html` | Penjelasan resmi MAGMA dan cakupan publik |
| `https://magma.esdm.go.id/v1/gunung-api/tingkat-aktivitas` | 200 | `text/html` | Status aktivitas gunung api |
| `https://magma.esdm.go.id/v1/gunung-api/laporan` | 200 | `text/html` | Laporan aktivitas/VAR |
| `https://magma.esdm.go.id/v1/gunung-api/laporan-harian` | 200 | `text/html` | Laporan harian gunung api |
| `https://magma.esdm.go.id/v1/gunung-api/informasi-letusan` | 200 | `text/html` | Informasi letusan/VEN |
| `https://magma.esdm.go.id/vona` | 200 | `text/html` | VONA terbit |
| `https://magma.esdm.go.id/v1/vona` | 200 | `text/html` | Arsip VONA |
| `https://magma.esdm.go.id/v1/gerakan-tanah/tanggapan` | 200 | `text/html` | Laporan tanggapan gerakan tanah |
| `https://magma.esdm.go.id/v1/gerakan-tanah/lews` | 200 | `text/html` | Daftar stasiun LEWS |
| `https://magma.esdm.go.id/v1/gerakan-tanah/lews/1` | 200 | `text/html` | Halaman detail stasiun; isi data tidak tampil pada HTML awal |
| `https://magma.esdm.go.id/v1/gempa-bumi-dan-tsunami/kajian` | 200 | `text/html` | Kajian gempa bumi dan tsunami |

### 3.2 Dokumen pendukung resmi

| URL | Catatan |
|---|---|
| `https://www.esdm.go.id/en/media-center/news-archives/magma-indonesia-versi-terbaru-diluncurkan-warga-bisa-cek-kerawanan-bencana-dari-lokasinya` | Artikel ESDM 2026-10-22; menyebut integrasi API dan CAP |
| `https://github.com/magma-indonesia/magma-indonesia` | Repository resmi MAGMA Indonesia |
| `https://raw.githubusercontent.com/magma-indonesia/magma-indonesia/master/README.md` | README repo; menyebut MAGMA v2 sebagai webservice Laravel |
| `https://raw.githubusercontent.com/magma-indonesia/magma-indonesia/master/routes/api.php` | Route API resmi; sumber bukti perlindungan `jwt.auth` |
| `https://repo.esdm.go.id/magma/magma-indonesia` | Repo ESDM yang disebut sebagai asal import; tidak diperiksa langsung |

## 4. Hasil Uji Akses API

Pengujian dilakukan tanpa token dan tanpa login. Hasil berikut adalah respons aktual pada tanggal audit.

| Endpoint | Status | Content-Type | Respons |
|---|---:|---|---|
| `GET https://magma.esdm.go.id/api/status` | 500 | `application/json` | `{"status":"false","code":500,"message":"Token Invalid"}` |
| `GET https://magma.esdm.go.id/api/vona` | 500 | `application/json` | `{"message":"Server Error"}` |
| `GET https://magma.esdm.go.id/api/vona/latest` | 500 | `application/json` | `{"message":"Server Error"}` |
| `GET https://magma.esdm.go.id/api/v1/home/gunung-api/status` | 401 | `application/json` | Unauthorized |
| `GET https://magma.esdm.go.id/api/v1/home/gerakan-tanah/latest` | 401 | `application/json` | Unauthorized |
| `GET https://magma.esdm.go.id/api/v1/home/gempa-bumi/latest` | 401 | `application/json` | Unauthorized |
| `GET https://magma.esdm.go.id/api/v1/magma-var` | 401 | `application/json` | Unauthorized |

Interpretasi:

- **Tidak ada API data publik yang terbukti dapat digunakan tanpa token.**
- Route `/api/status` dideklarasikan di luar middleware `jwt.auth`, tetapi tetap mengembalikan “Token Invalid”.
- Route `/api/vona` dan `/api/vona/latest` dideklarasikan publik, tetapi mengembalikan “Server Error”.
- Route `/api/v1/*` yang memuat data gunung api, gerakan tanah, gempa bumi, dan VAR dilindungi `jwt.auth`.
- Repository resmi memiliki route login, tetapi dokumentasi autentikasi dan kontrak respons tidak ditemukan; login tidak dicoba karena tidak ada kredensial dan berada di luar ruang lingkup read-only.

Route API resmi yang relevan dari `routes/api.php`:

- Publik: `vona`, `vona/latest`, `vona/filter`, `vona/{uuid}`, `status`, `login`.
- Terlindungi `jwt.auth`: `gunung-api`, `mounts`, `vogamos`, `v1/magma-var`, `v1/magma-ven`, `v1/magma-sigertan`, `v1/home/gunung-api/*`, `v1/home/gerakan-tanah/*`, `v1/home/gempa-bumi/*`, `v1/bencana-geologi/terkini`.
- Tidak ditemukan OpenAPI, Swagger, dokumentasi skema, atau contoh respons resmi di repo/halaman yang diperiksa.

## 5. Contoh Struktur Data yang Tersedia

Struktur berikut berasal dari **halaman HTML publik**, bukan dari respons API JSON resmi.

### 5.1 Tingkat Aktivitas Gunung Api

Halaman: `https://magma.esdm.go.id/v1/gunung-api/tingkat-aktivitas`

Tabel utama memiliki kolom:

| Kolom | Contoh/Isi |
|---|---|
| Tingkat Aktivitas | `Level IV (Awas)`, `Level III (Siaga)`, `Level II (Waspada)`, `Level I (Normal)` |
| Jumlah | Jumlah gunung api pada level tersebut |
| Gunung Api | Nama gunung dan tautan laporan |

Contoh status pada audit:

- Level IV: 0
- Level III: 3, termasuk Anak Krakatau, Semeru, dan Merapi
- Tautan detail laporan menggunakan parameter `signature`.

### 5.2 Laporan Aktivitas Gunung Api/VAR

Halaman daftar: `https://magma.esdm.go.id/v1/gunung-api/laporan`

Field yang terlihat pada daftar:

- Nama gunung api
- Level aktivitas
- Periode laporan, misalnya `06:00-12:00 WIB`
- Tanggal laporan
- Nama pembuat laporan
- Ringkasan pengamatan visual
- Tautan detail dengan `signature`

Field yang terlihat pada halaman detail VAR:

- Nama gunung api
- Level aktivitas
- Tanggal dan periode
- Kabupaten/kota dan provinsi
- Latitude dan longitude
- Ketinggian
- Pengamatan visual
- Keterangan lainnya
- Klimatologi: cuaca, angin, suhu, kelembapan
- Pengamatan kegempaan: jenis gempa, amplitudo, durasi
- Rekomendasi
- Foto/gambar pendukung

Contoh nilai: Anak Krakatau, Level III (Siaga), periode `06:00-12:00 WIB`, koordinat `-6.102, 105.423`, ketinggian `157 mdpl`.

### 5.3 Informasi Letusan/VEN

Halaman: `https://magma.esdm.go.id/v1/gunung-api/informasi-letusan`

Field yang terlihat:

- Waktu letusan
- Zona waktu: WIB/WITA/WIT
- Nama gunung api
- Pembuat laporan
- Deskripsi letusan
- Tinggi kolom abu di atas puncak dan di atas permukaan laut
- Warna dan intensitas kolom abu
- Arah angin
- Amplitudo maksimum dan durasi gempa
- Gambar pendukung
- ID detail dan tautan `Details`

Contoh pada audit: letusan Ibu dan Dukono pada 2026-11-02, serta Semeru dan Karangetang pada 2026-11-01.

### 5.4 Gerakan Tanah/Tanah Longsor

Halaman: `https://magma.esdm.go.id/v1/gerakan-tanah/tanggapan`

Field yang terlihat:

- Waktu laporan
- Lokasi: desa, kecamatan, kabupaten, provinsi
- Waktu kejadian
- Koordinat lokasi
- Zona Potensi Gerakan Tanah: rendah, menengah, tinggi
- Rekomendasi
- ID laporan dan tautan detail dengan `signature`

Catatan kualitas data:

- Halaman menulis koordinat seperti `-6.549784 LU` dan `-2.594659 LU`; tanda negatif dengan “LU” tidak konsisten dan perlu normalisasi bila data dipakai.
- “Zona Potensi Gerakan Tanah” adalah informasi potensi, bukan bukti kejadian.
- Laporan terbaru pada halaman pertama saat audit: **2023-05-04**; ini tidak menunjukkan umpan kejadian terkini.

### 5.5 Gempa Bumi dan Tsunami

Halaman: `https://magma.esdm.go.id/v1/gempa-bumi-dan-tsunami/kajian`

Field yang terlihat:

- Judul kajian
- Waktu kejadian
- Intensitas MMI, bila ada
- Deskripsi kejadian
- Koordinat episenter dari BMKG, USGS, dan/atau GFZ
- Magnitudo
- Kedalaman hiposenter
- Rekomendasi
- Magnitudo ringkas, misalnya `4.5 SR`
- Status potensi tsunami, misalnya `Tidak berpotensi Tsunami`
- ID kajian dan tautan detail dengan `signature`

Catatan:

- Halaman ini adalah **kajian gempa bumi**, bukan umpan gempa real-time.
- Kajian terbaru pada halaman pertama saat audit: **2026-04-08**, sekitar 6 bulan sebelum tanggal audit.
- Tidak ditemukan halaman/data kejadian tsunami mandiri. “Tidak berpotensi Tsunami” adalah hasil asesmen, bukan data kejadian tsunami.

### 5.6 LEWS

Halaman: `https://magma.esdm.go.id/v1/gerakan-tanah/lews`

Field yang terlihat:

- Nama stasiun
- Lokasi administratif
- Jumlah data

Halaman detail stasiun, misalnya `https://magma.esdm.go.id/v1/gerakan-tanah/lews/1`, tidak menampilkan data pengukuran pada HTML awal. Data kemungkinan dimuat via JavaScript/API, tetapi API tersebut tidak dapat diakses tanpa token. LEWS adalah sistem peringatan dini, bukan katalog kejadian.

### 5.7 VONA

Halaman publik VONA dan arsip VONA tersedia sebagai HTML:

- `https://magma.esdm.go.id/vona`
- `https://magma.esdm.go.id/v1/vona`

VONA adalah notifikasi abu vulkanik untuk keselamatan penerbangan. Data ini relevan untuk Gunungapi, tetapi bukan pengganti laporan aktivitas atau data kejadian umum.

## 6. Matriks Cakupan 8 Kategori

| Kategori | Status | Bukti | Layak sebagai data kejadian? | Catatan |
|---|---|---|---|---|
| Gunungapi | **Tersedia** | Status aktivitas, VAR, VEN, VONA, laporan harian, KRB | Ya, dengan batasan | Paling kuat; laporan berkala; tautan detail memakai signature |
| Gempabumi | **Sebagian** | Kajian gempa bumi | Terbatas | Kajian terbaru 2026-04-08; bukan real-time; data episenter terutama berupa teks |
| Tsunami | **Sebagian, tidak memadai** | Menu “Gempa Bumi dan Tsunami”; status “Tidak berpotensi Tsunami” | Tidak | Tidak ada katalog kejadian tsunami; hanya asesmen potensi |
| Gerakan Tanah/Tanah Longsor | **Sebagian** | Laporan tanggapan kejadian; daftar stasiun LEWS | Terbatas | Laporan terbaru 2023-05-04; LEWS bukan data kejadian |
| Likuefaksi | **BELUM DAPAT DIVERIFIKASI** | Hanya frasa generik dalam rekomendasi gempa | Tidak | Tidak ditemukan halaman/data kejadian likuefaksi |
| Abrasi dan Akresi | **BELUM DAPAT DIVERIFIKASI** | Tidak ditemukan menu/data | Tidak | Tidak ditemukan halaman/data abrasi-akresi |
| Penurunan Muka Tanah | **BELUM DAPAT DIVERIFIKASI** | Hanya frasa “penurunan lahan” dalam rekomendasi gempa | Tidak | Tidak ditemukan data kejadian penurunan muka tanah |
| Semburan Gas dan Lumpur | **BELUM DAPAT DIVERIFIKASI** | Tidak ditemukan menu/data | Tidak | Tidak ditemukan halaman/data semburan gas/lumpur |

## 7. Kelebihan

- Sumber resmi PVMBG/Badan Geologi/Kementerian ESDM.
- Otoritatif untuk status dan laporan aktivitas gunung api.
- Menyediakan laporan terstruktur per periode untuk gunung api.
- Menyediakan VONA dan KRB untuk kebutuhan kebencanaan gunung api.
- Menyediakan catatan letusan, kajian gempa, dan laporan tanggapan gerakan tanah.
- Halaman publik dapat diakses tanpa login.
- Beberapa data memiliki koordinat, waktu, magnitudo, kedalaman, dan tingkat aktivitas.
- Ada arsip historis yang cukup besar, terutama untuk laporan gunung api dan letusan.

## 8. Keterbatasan dan Risiko

1. **Tidak ada API publik terdokumentasi.** Integrasi API disebut untuk BNPB/BPBD/K/L/pemangku kepentingan, bukan untuk konsumsi publik tanpa kontrak.
2. **API data utama memerlukan JWT.** Tanpa token, endpoint data mengembalikan 401.
3. **Endpoint publik yang diuji rusak.** `/api/vona` dan `/api/vona/latest` mengembalikan 500.
4. **Data utama berupa HTML.** Tidak ada skema JSON stabil; scraping HTML rapuh terhadap perubahan tampilan.
5. **Tautan detail memakai signature.** Masa berlaku signature tidak diuji; ini menambah kompleksitas automasi.
6. **Tidak semua kategori tersedia.** Empat kategori tidak ditemukan sama sekali; tsunami tidak memiliki katalog kejadian.
7. **Sebagian data tidak real-time.** Kajian gempa dan laporan gerakan tanah pada halaman pertama sudah lama.
8. **Data potensi bukan data kejadian.** KRB, LEWS, dan zona potensi gerakan tanah tidak boleh dihitung sebagai event.
9. **Kualitas lokasi tidak seragam.** Koordinat gempa umumnya berada dalam teks; koordinat gerakan tanah memiliki label LU/BT yang tidak konsisten.
10. **Tidak ada jaminan kelengkapan.** Audit tidak menguji seluruh arsip, seluruh pagination, atau seluruh endpoint internal.
11. **CAP belum terverifikasi.** Artikel ESDM menyebut CAP, tetapi tidak ditemukan endpoint/dokumentasi CAP publik.
12. **Aspek hukum/batas akses belum dinilai.** Perlu konfirmasi izin dan ketentuan penggunaan sebelum otomasi produksi.

## 9. Rekomendasi

1. **Gunakan MAGMA sebagai sumber pendukung**, terutama untuk Gunungapi.
2. **Jangan menjadikan MAGMA satu-satunya sumber** untuk 8 kategori.
3. Untuk **Gempabumi dan Tsunami**, gunakan MAGMA hanya sebagai pelengkap kajian; sumber utama sebaiknya BMKG.
4. Untuk **Gerakan Tanah**, gunakan laporan MAGMA sebagai data historis/verifikasi, bukan umpan real-time.
5. Untuk **Likuefaksi, Abrasi/Akresi, Penurunan Muka Tanah, dan Semburan Gas/Lumpur**, cari sumber resmi lain.
6. **Jangan membangun scraper produksi berbasis HTML** tanpa persetujuan dan tanpa strategi perubahan tampilan.
7. Ajukan permintaan resmi kepada PVMBG untuk:
   - dokumentasi API,
   - mekanisme autentikasi/token,
   - batas laju,
   - skema respons,
   - izin penggunaan data,
   - informasi CAP.
8. Bila API institusional diperoleh, prioritaskan endpoint terstruktur untuk Gunungapi, Gempabumi, dan Gerakan Tanah; tetap perlakukan KRB/LEWS sebagai data potensi/peringatan.

## 10. Pernyataan Audit

Audit ini hanya melakukan pembacaan halaman publik, pemeriksaan repository resmi, dan GET terbatas tanpa autentikasi. Tidak ada perubahan kode aplikasi, dataset final, baseline, atau file pipeline. Tidak ada scraper lama yang dijalankan dan tidak ada unit test penuh yang dijalankan.
