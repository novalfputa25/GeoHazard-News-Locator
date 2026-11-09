# FIX 08 - Filter Wilayah Provinsi dan Kabupaten/Kota

Tanggal: **2026-11-05**  
Fix ID: `FIX-WILAYAH-20261105`  
Status: **filter provinsi + kabupaten/kota, opsi dependent, URL state, test, dan verifikasi browser selesai**

## 1. Tujuan dan batas

FIX 08 menambahkan filter wilayah bertingkat pada dashboard:

1. Pengguna memilih provinsi.
2. Setelah provinsi dipilih, pengguna dapat memilih kabupaten/kota.
3. Seluruh kartu statistik, grafik kategori, tren, grafik wilayah, dan berita terbaru mengikuti filter yang sama.

Batas yang dipertahankan:

- Dashboard tetap read-only.
- Tidak ada perubahan pada baseline, raw payload, event lama, atau status relevansi FIX 07.
- Tidak ada lokasi yang ditebak dari judul berita atau koordinat.
- Wilayah hanya diambil dari kolom resmi `event_location.admin_province` dan `event_location.admin_kabupaten_kota`.
- Dokumen wilayah harus mengikuti `document_event_link`; dokumen tanpa relasi event tidak dimasukkan ke wilayah tertentu.
- Event tanpa provinsi tetap diwakili opsi `Tidak diketahui`, bukan dipaksa masuk provinsi tertentu.
- Nama wilayah asli dipertahankan; normalisasi hanya untuk pencocokan, bukan mengubah database.

Tidak ada migrasi database pada FIX 08 karena perubahan hanya ada di query dashboard dan UI. Karena itu tidak ada backup baru.

## 2. Sumber data

Tabel utama:

```text
event_location(
  event_location_id, event_id, location_name, location_role,
  admin_province, admin_kabupaten_kota, admin_kecamatan,
  admin_desa_kelurahan, latitude, longitude, ...
)
```

Relasi yang dipakai:

```text
event
  -> event_location
  -> document_event_link
  -> document
  -> document_relevance
```

Aturan hitung:

- Event dihitung dari tabel `event` dengan `EXISTS` ke `event_location`.
- Dokumen dihitung dari `document` yang aktif, tidak duplikat, dan `relevance_status = 'relevan'`.
- Filter wilayah dokumen memakai `EXISTS` ke `document_event_link` aktif lalu ke `event_location`.
- Hitungan event tidak digandakan oleh jumlah dokumen atau jumlah baris lokasi.

## 3. Kondisi data wilayah

Jumlah baris `event_location`: **75**. Saat ini setiap event memiliki satu baris lokasi, sehingga tidak ada duplikasi event dari multi-lokasi.

| Temuan | Jumlah |
|---|---:|
| Event dengan baris lokasi | 75 |
| Event dengan provinsi diketahui | 31 |
| Event tanpa provinsi | 44 |
| Event dengan kabupaten/kota diketahui | 21 |
| Event tanpa kabupaten/kota | 54 |
| Event provinsi diketahui tetapi kabupaten/kota belum ada | 10 |
| Provinsi dengan data | 15 |
| Kabupaten/kota dengan data | 14 |

Rincian provinsi:

| Provinsi | Event | Pilihan kabupaten/kota |
|---|---:|---:|
| Aceh | 1 | 1 |
| Bali | 1 | 1 |
| Banten | 1 | 0 |
| Gorontalo | 1 | 1 |
| Jawa Barat | 7 | 3 |
| Jawa Timur | 1 | 1 |
| Kalimantan Utara | 1 | 1 |
| Nusa Tenggara Barat | 1 | 0 |
| Nusa Tenggara Timur | 8 | 2 |
| Papua | 1 | 1 |
| Papua Barat | 1 | 1 |
| Sulawesi Selatan | 1 | 0 |
| Sulawesi Tengah | 2 | 1 |
| Sulawesi Utara | 3 | 1 |
| Sumatera Barat | 1 | 0 |

Provinsi tanpa pilihan kabupaten/kota: **Banten, Nusa Tenggara Barat, Sulawesi Selatan, Sumatera Barat**. Provinsi tetap dapat difilter dan tetap menampilkan event provinsi-only.

Rincian kabupaten/kota:

```text
Aceh / Kabupaten Aceh Jaya
Bali / Kabupaten Jembrana
Gorontalo / Kabupaten Pohuwato
Jawa Barat / Kabupaten Garut
Jawa Barat / Kabupaten Sukabumi
Jawa Barat / Kota Bogor
Jawa Timur / Kabupaten Pacitan
Kalimantan Utara / Kota Tarakan
Nusa Tenggara Timur / Kabupaten Manggarai
Nusa Tenggara Timur / Kabupaten Sumba Barat Daya
Papua / Kabupaten Sarmi
Papua Barat / Kota Sorong
Sulawesi Tengah / Kabupaten Morowali Utara
Sulawesi Utara / Kota Bitung
```

Data nama wilayah saat ini bersih; tidak ditemukan variasi spasi atau kapitalisasi. Meskipun demikian, query tetap memakai normalisasi aman:

- `_clean_region_name()` merapikan spasi dan trim.
- `_region_key()` memakai `casefold()` untuk kunci opsi.
- SQL memakai `LOWER(TRIM(...))` untuk pencocokan.

## 4. Perubahan kode

| File | Perubahan |
|---|---|
| `dashboard/repository.py` | Field `kabupaten`, parsing query, filter provinsi/kabupaten pada event dan dokumen, statistik kabupaten, katalog opsi wilayah, meta lokasi. |
| `dashboard/static/app.js` | State `kabupaten`, URL param, opsi dependent, reset kabupaten saat provinsi berubah, ringkasan filter, notice, catatan statistik. |
| `dashboard/templates/index.html` | Field `Kabupaten/Kota`, notice status, placeholder catatan statistik lokasi. |
| `dashboard/static/styles.css` | Grid filter 7 kolom, gaya select disabled, gaya notice. |
| `test_dashboard.py` | 10 test baru untuk katalog wilayah, statistik, kombinasi filter, relasi dokumen, alias, dan API. |

Detail repository:

- `DashboardFilters.kabupaten` ditambahkan dengan default `"all"`.
- `parse_filters()` menerima `kabupaten` dan alias `kabupaten_kota`.
- `_event_where()` memfilter provinsi dan kabupaten lewat `EXISTS event_location`.
- `_document_where()` memfilter dokumen lewat `document_event_link` aktif dan `event_location`.
- `_event_stats()` mengembalikan `events_with_kabupaten_kota` dan `events_without_kabupaten_kota`.
- `_region_options()` menggantikan `_provinces()` dan mengembalikan:
  - `provinces`: daftar provinsi terurut.
  - `kabupaten_by_province`: peta provinsi ke daftar kabupaten/kota.
- `build_dashboard()` menambahkan `options["kabupaten_by_province"]` dan statistik kabupaten.
- `meta.location_basis` menjelaskan bahwa wilayah tidak ditebak dari koordinat dan dokumen mengikuti link event.

Detail UI:

- Provinsi `Semua wilayah`: select kabupaten disabled dengan teks `Pilih provinsi dulu`.
- Provinsi `Tidak diketahui`: select kabupaten disabled dengan teks `Tidak ada kabupaten/kota`.
- Provinsi tanpa data kabupaten: select disabled dengan teks `Tidak ada kabupaten/kota diketahui` dan notice menjelaskan hasil tetap di tingkat provinsi.
- Mengganti provinsi mereset kabupaten ke `all` agar tidak membawa pilihan lama.
- Reset mengembalikan seluruh filter ke default.
- URL menyimpan `kabupaten`; URL lama dengan `kabupaten_kota` tetap dibaca.
- Ringkasan filter menampilkan provinsi dan kabupaten/kota yang dipilih.
- Notice muncul untuk filter kosong, provinsi tanpa kabupaten, dan `Tidak diketahui`.

## 5. Perilaku filter

| Filter | Dokumen | Event | Event dengan kab/kota |
|---|---:|---:|---:|
| Tanpa filter | 84 | 75 | 21 |
| Jawa Barat | 7 | 7 | 6 |
| Jawa Barat / Kota Bogor | 3 | 3 | 3 |
| Jawa Barat / Kabupaten Sukabumi | 2 | 2 | 2 |
| Jawa Barat / Kabupaten Garut | 1 | 1 | 1 |
| Banten | 1 | 1 | 0 |
| Nusa Tenggara Barat | 1 | 1 | 0 |
| Nusa Tenggara Timur | 8 | 8 | 6 |

Kombinasi filter:

| Filter | Dokumen | Event |
|---|---:|---:|
| `Gempabumi` + Jawa Barat + Kota Bogor | 3 | 3 |
| Oktober 2026 + Jawa Barat + Kota Bogor | 3 | 3 |
| `Gunungapi` + Jawa Barat | 0 | 0 |
| `Tidak diketahui` + Kota Bogor | 0 | 0 |

Catatan:

- Jawa Barat memiliki 7 event: 6 memiliki kabupaten/kota dan 1 event provinsi-only.
- Dokumen relevan total 84; yang terhubung ke event 77; yang tidak terhubung 7. Dokumen tanpa relasi event tidak masuk hasil filter wilayah.
- `Tidak diketahui` + kabupaten menghasilkan nol karena event tanpa provinsi tidak boleh dipaksa memiliki kabupaten.
- Grafik wilayah tetap menampilkan tingkat provinsi; filter kabupaten menyempitkan event yang dihitung.

## 6. Hasil verifikasi browser

Verifikasi headless Chrome pada dashboard yang berjalan:

URL:

```text
http://127.0.0.1:8765/?province=Jawa%20Barat&kabupaten=Kota%20Bogor
```

Hasil DOM:

```text
Select kabupaten berisi:
Semua kabupaten/kota, Kabupaten Garut, Kabupaten Sukabumi, Kota Bogor

Ringkasan:
Kategori: Semua kategori · Wilayah: Jawa Barat · Kab/Kota: Kota Bogor · ...

Statistik:
Dokumen = 3
Event = 3
Lokasi = 3 punya provinsi · 3 punya kab/kota · 0 belum
```

URL provinsi tanpa kabupaten:

```text
http://127.0.0.1:8765/?province=Banten
```

Hasil DOM:

```text
Select kabupaten disabled:
Tidak ada kabupaten/kota diketahui

Notice:
Provinsi Banten belum memiliki data kabupaten/kota; hasil ditampilkan pada tingkat provinsi.

Statistik:
Dokumen = 1
Event = 1
```

Tidak ada error JavaScript pada DOM hasil render.

## 7. Test dan verifikasi

```text
.venv\Scripts\python.exe -m unittest test_dashboard -v
21 test, lulus semua (11 test lama + 10 test FIX 08)

.venv\Scripts\python.exe -m unittest test_relevance -v
12 test, lulus semua

.venv\Scripts\python.exe -m unittest discover -q
189 test dijalankan; 188 lulus; 1 error lama test_scraper

node --check dashboard/static/app.js
lulus

py_compile dashboard/repository.py dashboard/app.py test_dashboard.py
lulus
```

Error lama yang tidak terkait FIX 08:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

Test FIX 08 mencakup:

1. Katalog 15 provinsi dan 14 kabupaten/kota.
2. Statistik 21 event dengan kabupaten/kota dan 54 tanpa.
3. Filter Kota Bogor pada semua komponen.
4. Perbedaan hasil Kabupaten Sukabumi dan Kabupaten Garut.
5. Provinsi tanpa kabupaten tetap mengembalikan event.
6. Kombinasi kategori, tanggal, dan kabupaten.
7. `Tidak diketahui` + kabupaten menghasilkan nol.
8. Dokumen kabupaten mengikuti link event.
9. Alias query `kabupaten` dan `kabupaten_kota`.
10. API HTTP dan elemen UI filter kabupaten.

## 8. Batasan dan rekomendasi

Batasan:

- Cakupan kabupaten/kota masih mengikuti data `event_location` yang ada: 21 event dan 14 kabupaten/kota.
- 44 event belum memiliki provinsi dan 54 event belum memiliki kabupaten/kota; angka ini tidak diisi paksa.
- Dokumen relevan yang tidak terhubung ke event tidak dapat dimasukkan ke filter wilayah tanpa menebak relasi.
- Grafik wilayah masih pada tingkat provinsi; belum ada breakdown kabupaten/kota di grafik.
- Satu event saat ini hanya memiliki satu baris `event_location`; jika nanti ada multi-lokasi, hitungan event tetap memakai `EXISTS`/event unik.

Rekomendasi:

1. Lengkapi provinsi/kabupaten untuk event yang masih unknown melalui review bukti, bukan menebak dari judul.
2. Tambahkan breakdown kabupaten/kota pada grafik wilayah jika data multi-lokasi sudah lebih lengkap.
3. Pertahankan normalisasi hanya untuk pencocokan; jangan menulis ulang nama wilayah tanpa keputusan data.
4. Tambahkan validasi API bahwa kabupaten harus berada dalam provinsi yang dipilih jika filter dipakai di luar UI.
5. Tambahkan test browser otomatis untuk perilaku reset kabupaten saat provinsi berubah.

## 9. File terkait

- `dashboard/repository.py`
- `dashboard/static/app.js`
- `dashboard/templates/index.html`
- `dashboard/static/styles.css`
- `dashboard/app.py`
- `database/schema.sql`
- `database/geohazard.db`
- `test_dashboard.py`
- `test_relevance.py`
- `reports/FIX07_RELEVANSI_BERITA.md`
