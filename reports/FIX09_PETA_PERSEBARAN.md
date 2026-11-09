# FIX 09 - Peta Persebaran Bahaya Geologi Indonesia

Tanggal: **2026-11-05**  
Fix ID: `FIX-PETA-20261105`  
Status: **peta interaktif, marker, popup, legenda, clustering, layer, statistik, integrasi filter, test, dan verifikasi browser selesai**

## 1. Tujuan dan batas

FIX 09 menambahkan peta interaktif pada dashboard untuk menampilkan persebaran kejadian geohazard yang memiliki koordinat valid.

Batas yang dipertahankan:

- Dashboard tetap read-only.
- Tidak ada perubahan pada baseline, raw payload, event lama, atau status relevansi FIX 07.
- Tidak ada migrasi database dan tidak ada backup baru.
- Tidak ada geocoding, interpolasi, atau tebakan koordinat.
- Marker hanya dibuat dari `event_location.latitude` dan `event_location.longitude`.
- Satu event menghasilkan paling banyak satu marker.
- Event tanpa koordinat valid tetap dihitung pada statistik, tetapi tidak ditampilkan sebagai marker.
- Dokumen pada popup hanya dokumen aktif, relevan, tidak duplikat, dan terhubung ke event.
- Wilayah tidak diisi paksa; nilai kosong tetap ditampilkan sebagai belum diketahui.
- Peta tidak memakai API key.

## 2. Sumber data dan aturan marker

Tabel yang dipakai:

```text
event
  -> event_location
  -> event_time
  -> category
  -> document_event_link
  -> document
  -> document_relevance
```

Aturan marker:

1. Event diambil dari tabel `event` dengan `JOIN event_location`.
2. Hanya baris dengan latitude dan longitude numerik serta finite yang diterima.
3. Latitude harus berada pada `-90..90`; longitude pada `-180..180`.
4. Jika satu event memiliki beberapa baris lokasi valid, marker memakai baris pertama berdasarkan `event_location_id`.
5. Marker tetap memakai koordinat apa adanya; nilai `is_inside_indonesia` tidak mengubah koordinat.
6. Kategori marker memakai kategori primary event, fallback `Lainnya`.
7. Popup memuat waktu, lokasi, provinsi, kabupaten/kota, koordinat, jumlah berita relevan, dan daftar berita.
8. Popup tanpa waktu memakai teks `Waktu kejadian belum diketahui`.
9. Popup tanpa kabupaten/kota memakai teks `Kabupaten/kota belum diketahui`.
10. Popup tanpa dokumen relevan menampilkan `Belum ada berita relevan untuk kejadian ini.`

Dokumen popup mengikuti aturan:

```text
document_event_link.link_status = 'active'
document.document_status = 'active'
document_relevance.relevance_status = 'relevan'
document tidak ada pada document_duplicate
```

## 3. Kondisi data

Ringkasan event dan koordinat:

| Temuan | Jumlah |
|---|---:|
| Total event | 75 |
| Event dengan koordinat valid | 70 |
| Event tanpa koordinat valid | 5 |
| Marker yang tampil | 70 |
| Marker di luar Indonesia | 10 |

Status koordinat valid:

| `is_inside_indonesia` | Jumlah |
|---|---:|
| `ya` | 42 |
| `tidak_diketahui` | 18 |
| `tidak` | 10 |

Kategori marker:

| Kategori | Marker |
|---|---:|
| Gempabumi | 66 |
| Lainnya | 4 |
| Gunungapi | 0 |
| Tsunami | 0 |
| Gerakan Tanah/Tanah Longsor | 0 |
| Likuefaksi | 0 |
| Abrasi dan Akresi | 0 |
| Penurunan Muka Tanah | 0 |
| Semburan Gas dan Lumpur | 0 |

Empat marker tidak memiliki dokumen relevan; keempatnya berasal dari event GDACS dan tetap ditampilkan dengan daftar berita kosong.

### Keputusan marker di luar Indonesia

Sebanyak 10 marker memiliki koordinat valid tetapi `is_inside_indonesia = 'tidak'`. Marker tersebut tetap ditampilkan karena:

- koordinatnya valid dan berasal dari data;
- dashboard tidak boleh menyembunyikan data valid tanpa penanda;
- peta dibuka pada extent Indonesia sehingga marker luar tidak langsung memenuhi tampilan;
- statistik peta menampilkan baris `Di luar Indonesia: 10`;
- legenda dan popup tetap memberi konteks kategori dan lokasi.

Jika kemudian diinginkan peta hanya Indonesia, kontrol lingkup dapat ditambahkan tanpa mengubah data sumber.

## 4. Perubahan kode

| File | Perubahan |
|---|---|
| `dashboard/repository.py` | Validasi kombinasi wilayah, helper koordinat, query marker, dokumen popup, statistik peta, `meta.map_basis`. |
| `dashboard/templates/index.html` | Section `#peta`, judul, kontrol layer, canvas, state loading/empty/error, badge marker, statistik, legenda, footnote. |
| `dashboard/static/styles.css` | Layout peta responsif, panel statistik/legenda, marker pin, cluster, popup, overlay state, notice tile. |
| `dashboard/static/app.js` | Inisialisasi Leaflet, layer Satellite/Topographic, fallback tile, marker cluster, popup, statistik, legenda, fokus/reset view. |
| `dashboard/static/vendor/leaflet/` | Leaflet 1.9.4 lokal beserta CSS, lisensi, dan gambar. |
| `dashboard/static/vendor/leaflet.markercluster/` | Leaflet.markercluster 1.5.3 lokal beserta CSS dan lisensi. |
| `test_dashboard.py` | 20 test baru untuk peta, validasi wilayah, statistik, dokumen, vendor, dan kontrak frontend. |

### Payload API

`build_dashboard()` menambahkan:

```text
data["map"]["markers"]
data["map"]["stats"]
```

Field marker:

```text
event_id, event_title, category, event_time,
location_name, province, kabupaten,
latitude, longitude, is_inside_indonesia,
document_count, documents
```

Field dokumen marker:

```text
document_id, title, source, url, published_at
```

Field statistik peta:

```text
total_events, events_with_coordinates,
events_without_coordinates, marker_count,
markers_outside_indonesia, marker_categories
```

`meta.map_basis` menjelaskan bahwa marker memakai satu koordinat valid per event dan event tanpa koordinat tetap dihitung.

### Validasi wilayah

Validasi baru menolak kombinasi yang tidak konsisten:

| Kondisi | Pesan |
|---|---|
| `kabupaten` tanpa `province` | `kabupaten memerlukan province` |
| `province=__unknown__` + `kabupaten` | `kabupaten tidak tersedia untuk province tidak diketahui` |
| Kabupaten bukan milik provinsi | `Kombinasi province dan kabupaten tidak valid` |

`ValueError` dari repository ditangani handler dashboard yang sudah ada dan menghasilkan HTTP `400`.

## 5. Perilaku peta dan UI

### Tampilan

- Judul: **Peta Persebaran Bahaya Geologi Indonesia**.
- Navigasi dashboard memiliki tautan `Peta persebaran`.
- Peta dibuka pada pusat Indonesia `[-2.5, 118.5]`, zoom `5`.
- Layer awal `Satellite` memakai Esri World Imagery dan label Esri.
- Layer `Topographic` memakai OpenTopoMap.
- Jika tile gagal, peta mencoba fallback OpenStreetMap dan menampilkan notice.
- Atribusi layer tetap ditampilkan.
- Marker memakai pin berwarna dan simbol kategori.
- Marker berdekatan dikelompokkan dengan Leaflet.markercluster.
- Jika plugin cluster tidak tersedia, marker tetap tampil sebagai layer biasa.
- Popup memuat metadata kejadian dan tautan berita relevan.
- Panel samping menampilkan statistik peta dan legenda 9 kategori.
- Badge menampilkan jumlah marker, misalnya `70 marker`.
- State loading, empty, error, dan notice tile tersedia.

### Integrasi filter

- Peta mengikuti filter kategori, tanggal, provinsi, dan kabupaten/kota.
- Jika provinsi dipilih, peta fokus ke marker provinsi tersebut dengan `maxZoom = 9`.
- Jika filter tidak memiliki marker, peta menampilkan pesan yang sesuai.
- Reset filter mengembalikan peta ke extent Indonesia.
- Jika provinsi berubah, kabupaten direset dan URL tidak membawa kabupaten lama.
- `Tidak diketahui` tidak menampilkan pilihan kabupaten.

### Hasil filter peta

| Filter | Total event | Marker | Event tanpa koordinat |
|---|---:|---:|---:|
| Tanpa filter | 75 | 70 | 5 |
| Jawa Barat | 7 | 6 | 1 |
| Jawa Barat / Kota Bogor | 3 | 3 | 0 |
| Banten | 1 | 1 | 0 |
| Gunungapi | 2 | 0 | 2 |
| Oktober 2026 | 64 | 59 | 5 |
| Provinsi tidak diketahui | 44 | 41 | 3 |

## 6. Verifikasi browser

Verifikasi dilakukan dengan headless Chrome pada dashboard yang berjalan di `http://127.0.0.1:8765/`.

Hasil DOM setelah render final:

```text
Badge marker             : 70 marker
Loading peta             : hidden
Error peta               : hidden
Leaflet container        : ada
Marker pin pada zoom 5   : 9
Cluster pada zoom 5      : 15
Item legenda             : 9
Baris statistik peta     : 5
```

Jumlah pin dan cluster pada DOM tidak sama dengan 70 karena marker di luar viewport dan marker berdekatan dikelompokkan. Marker individual tetap dapat diakses dengan zoom atau klik cluster.

Verifikasi interaktif sebelumnya juga memastikan:

- awal `Jawa Barat + Kota Bogor` menampilkan `3 marker` dan kabupaten `Kota Bogor`;
- mengganti provinsi ke `Banten` menampilkan `1 marker`;
- pilihan kabupaten menjadi disabled;
- URL berubah menjadi `province=Banten` tanpa `kabupaten`;
- notice filter muncul.

Screenshot full-page:

```text
C:\Users\LENOVO\AppData\Local\Temp\opencode\geohazard-map-all.png
```

## 7. Test dan verifikasi

```text
.venv\Scripts\python.exe -m unittest test_dashboard -v
41 test, lulus semua (21 test lama + 20 test FIX 09)

.venv\Scripts\python.exe -m unittest discover -v
209 test dijalankan; 208 lulus; 1 error lama test_scraper

node --check dashboard/static/app.js
lulus

py_compile dashboard/repository.py dashboard/app.py test_dashboard.py
lulus
```

Error lama yang tidak terkait FIX 09:

```text
ImportError: cannot import name 'get_soup' from 'scraper.bmkg_scraper'
```

Cakupan test FIX 09:

1. Marker unik dan koordinat valid.
2. Koordinat non-numerik dan di luar domain diabaikan.
3. Event tanpa koordinat tidak menjadi marker.
4. Statistik event dan marker konsisten.
5. Dokumen pendukung marker hanya dokumen relevan dan tidak duplikat.
6. Marker tanpa dokumen tetap jujur.
7. Marker tidak mengarang provinsi/kabupaten.
8. Filter Jawa Barat, Kota Bogor, Banten, dan `Tidak diketahui`.
9. Filter kategori tanpa koordinat menghasilkan peta kosong.
10. Filter tanggal membatasi marker.
11. Validasi kabupaten tanpa provinsi.
12. Validasi provinsi `Tidak diketahui` + kabupaten.
13. Validasi kabupaten di luar provinsi.
14. API HTTP memakai filter wilayah yang sama.
15. Aset vendor Leaflet dan markercluster tersedia.
16. Kontrak HTML/JS peta tersedia.

## 8. Batasan dan rekomendasi

Batasan:

- Lima event belum memiliki koordinat valid dan tidak dapat ditampilkan sebagai marker.
- Sepuluh marker berada di luar Indonesia dan tetap ditampilkan sesuai keputusan di atas.
- Empat event GDACS memiliki marker tetapi belum memiliki dokumen relevan.
- Kebijakan penggunaan tile Esri/OpenTopoMap belum diaudit formal; fallback OpenStreetMap sudah disediakan.
- Jumlah pin pada DOM hasil headless dapat lebih kecil dari jumlah marker karena clustering dan viewport.
- Referensi visual `IWU_project(1).pdf` tidak ditemukan, sehingga desain mengikuti spesifikasi tekstual.

Rekomendasi:

1. Tambahkan kontrol lingkup `Indonesia saja` jika 10 marker luar Indonesia ingin disembunyikan secara default.
2. Lengkapi koordinat event yang belum memiliki koordinat melalui review bukti, bukan tebakan.
3. Tambahkan dokumen relevan untuk empat event GDACS yang masih kosong.
4. Audit kebijakan penggunaan tile dan sediakan mode offline bila diperlukan.
5. Tambahkan test browser otomatis untuk popup, layer switch, fallback tile, dan fokus provinsi.

## 9. File terkait

- `dashboard/repository.py`
- `dashboard/templates/index.html`
- `dashboard/static/styles.css`
- `dashboard/static/app.js`
- `dashboard/static/vendor/leaflet/`
- `dashboard/static/vendor/leaflet.markercluster/`
- `dashboard/app.py`
- `database/schema.sql`
- `database/geohazard.db`
- `test_dashboard.py`
- `reports/FIX08_FILTER_WILAYAH.md`
- `C:\Users\LENOVO\AppData\Local\Temp\opencode\geohazard-map-all.png`
