# Audit Stage 5.1 — Hasil Perbaikan

- Tanggal audit: 2026-11-01
- Mode: **read-only**; tidak ada perubahan pada CSV lama, CSV Stage 5, atau kode produksi.
- Dataset lama: `data/geohazard_news_located_20261029T143308Z.csv`
- Dataset Stage 5: `data/geohazard_news_located_20261030T125936Z_stage5.csv`
- Laporan Stage 5: `reports/perbaikan_kualitas_data_stage5.md`

## 1. Integritas dataset

| Pemeriksaan | Dataset lama | Dataset Stage 5 |
|---|---:|---:|
| Jumlah baris data | 787 | 787 |
| Jumlah kolom | 19 | 30 |
| SHA-256 | `5d1d3832e41fe6641ebedf4fe35c03a81aedf77d3bd3661e26ba91f6ffc7a6eb` | `4a0c3377bddc1672e32e2e1dd6ed313e3a9c2702f64c3d0cbc8f313c9d189f0f` |
| URL unik | 787 | 787 |
| Baris dengan judul duplikat | 10 | 10 |

Kesimpulan integritas:

- Tidak ada baris yang hilang atau bertambah: **787 → 787**.
- Urutan URL identik; tidak ada baris yang digandakan secara tidak sengaja.
- Dari 19 kolom lama, **15 kolom tidak berubah**. Hanya empat kolom yang berubah:
  `kategori` (50 baris), `provinsi` (2 baris), `kabupaten_kota` (7 baris), dan `alamat_detail` (7 baris).
- `isi_berita`, `event_time`, `published_time`, `sumber`, `url`, `latitude`, `longitude`, `koordinat_status`, dan `koordinat_sumber` tidak berubah.
- Tidak ada URL duplikat. Sepuluh judul duplikat adalah duplikasi judul yang sudah ada sejak dataset lama, bukan baris baru.
- Hash sumber tetap sama dengan hash yang tercatat pada laporan Stage 5.

## 2. Ringkasan temuan

### Didukung bukti

- **12/12 perubahan kategori substantif** didukung judul atau isi berita.
- **9/9 berita USGS luar Indonesia** tetap ditandai `domain_lokasi=luar_indonesia`, `koordinat_domain=luar_indonesia`, dan tidak diberi provinsi/kabupaten Indonesia.
- **2/2 perubahan provinsi** didukung toponimi/rujukan berita.
- **7/7 nama kabupaten/kota** yang baru diisi adalah nama administratif yang valid di gazetteer dan muncul sebagai toponimi rujukan pada judul/isi.
- Penandaan duplikat, kolom `kategori_asal`, `kategori_berubah`, `status_cakupan`, `koordinat_verifikasi`, dan `koordinat_domain` konsisten.
- Tidak ditemukan kategori bencana yang berubah hanya karena lokasi geografis berita.

### Meragukan

- **7/7 perubahan kabupaten/kota** didukung sebagai **toponimi rujukan**, tetapi **tidak satu pun** diverifikasi sebagai batas administratif tempat pusat gempa berada. Semua berasal dari frasa “X km arah <nama tempat>”, bukan pernyataan “pusat gempa berada di darat <kabupaten/kota>”.
- Empat baris berisiko tinggi: **14, 17, 18, dan 27**. Jarak rujukan jauh atau epicenter dinyatakan di laut, sehingga klaim kabupaten/kota sebagai lokasi pusat gempa tidak cukup.
- Tiga baris memerlukan verifikasi: **12, 19, dan 24**. Nama rujukan didukung, tetapi batas administratifnya belum terbukti.
- `domain_lokasi` tidak sepenuhnya konsisten dengan informasi lokasi lain: **59 baris memiliki provinsi Indonesia tetapi `domain_lokasi=tidak_diketahui`**, sedangkan **45 baris tanpa provinsi justru `domain_lokasi=indonesia`**. Kolom ini lebih tepat dibaca sebagai “domain konteks berita”, bukan “domain lokasi kejadian”.

### Tidak didukung bukti

- Nilai lama baris 27, **`Nusa Tenggara Barat` / `Kota Bima`**, tidak didukung sebagai lokasi pusat gempa. `Kota Bima` hanya muncul pada bagian “Dirasakan”, bukan pada bagian “Wilayah”.
- Klaim bahwa pusat gempa berada **di dalam** `Kota Bitung` (baris 14), `Kota Tarakan` (baris 17), `Kabupaten Aceh Jaya` (baris 18), dan `Kabupaten Sumba Barat Daya` (baris 27) tidak didukung oleh pernyataan eksplisit di sumber. Nama tempatnya didukung; batas administratifnya tidak.
- Tidak ditemukan perubahan kategori substantif yang sepenuhnya tanpa bukti.

## 3. Pemeriksaan khusus baris 27

Judul: `Gempa M4.6 Pusat gempa berada di laut 49 km Barat KODI-SUMBABARATDAYA`

| Kolom | Sebelum | Stage 5 |
|---|---|---|
| `provinsi` | `Nusa Tenggara Barat` | `Nusa Tenggara Timur` |
| `kabupaten_kota` | `Kota Bima` | `Kabupaten Sumba Barat Daya` |
| `kecamatan` | kosong | kosong |
| `desa_kelurahan` | kosong | kosong |
| `latitude` | `-9.52` | `-9.52` |
| `longitude` | `118.54` | `118.54` |
| `koordinat_status` | `tersedia_sumber` | `tersedia_sumber` |
| `koordinat_sumber` | `URL BMKG` | `URL BMKG` |

Bukti yang tersedia:

- `sumber`: `BMKG`; `event_time` kosong.
- `published_time`: `2026-10-17T12:46:17+00:00`.
- URL BMKG memuat timestamp `2026-10-17T12:46:17+00:00`, koordinat `9.52 LS / 118.54 BT`, dan magnitudo 4.6.
- Isi berita menyebut `Tanggal: 17 Okt 2026 19:46:17 WIB` (ekuivalen 12:46:17 UTC), sehingga timestamp konsisten.
- Isi bagian `Wilayah`: `Pusat gempa berada di laut 49 km Barat KODI-SUMBABARATDAYA`.
- Isi bagian `Dirasakan`: `III Sumba Barat Daya, III Kota Bima, III Kab. Bima, III Sumbawa, III Sumba Barat`.
- Koordinat `-9.52, 118.54` berada di domain Indonesia dan berstatus `belum_diverifikasi`.

Penilaian:

- Perubahan ke **Nusa Tenggara Timur / Kabupaten Sumba Barat Daya** didukung sebagai **wilayah rujukan BMKG**: Kodi dan Sumba Barat Daya disebut eksplisit, dan Sumba Barat Daya terdaftar di gazetteer sebagai bagian NTT.
- `Kota Bima` pada dataset lama berasal dari daftar wilayah yang merasakan guncangan, bukan dari lokasi pusat gempa. Karena itu, perubahan menjauhi `Kota Bima` adalah koreksi yang tepat.
- Namun, epicenter dinyatakan **di laut, 49 km barat Kodi**. Tidak ada bukti bahwa titik epicenter berada di dalam batas darat `Kabupaten Sumba Barat Daya`. Klaim administratif yang presisi belum terverifikasi.

Rekomendasi baris 27:

- Pertahankan `provinsi=Nusa Tenggara Timur`.
- Jangan kembalikan ke `Kota Bima`.
- Jika `kabupaten_kota` dimaksudkan sebagai lokasi administratif pusat gempa, tandai **`perlu_verifikasi`** atau kosongkan `kabupaten_kota` sambil mempertahankan provinsi.
- Jika `kabupaten_kota` dimaksudkan sebagai wilayah rujukan BMKG, pertahankan nilainya tetapi tambahkan penanda bahwa itu adalah **referensi toponimi, bukan pusat administratif terverifikasi**.

## 4. Pemeriksaan 12 perubahan kategori substantif

### 4.1 Sebelas baris USGS

| Baris | Judul | Domain Stage 5 | Provinsi/Kabupaten | Bukti kategori |
|---:|---|---|---|---|
| 49 | M 4.5 - Banda Sea | `indonesia` | kosong | Format judul `M ...`; koordinat USGS |
| 50 | M 4.9 - 68 km WSW of San Juan del Sur, Nicaragua | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 51 | M 4.5 - Fiji region | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 52 | M 5.1 - 129 km SSE of Kokopo, Papua New Guinea | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 53 | M 4.7 - 147 km SSW of Kokopo, Papua New Guinea | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 54 | M 5.2 - 71 km ESE of Ohonua, Tonga | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 55 | M 4.5 - 0 km NE of Rio Grande, Panama | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 56 | M 4.7 - 20 km SW of Sandy Point Town, Saint Kitts and Nevis | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 57 | M 4.6 - Carlsberg Ridge | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 58 | M 4.5 - Kermadec Islands, New Zealand | `luar_indonesia` | kosong | Judul USGS + koordinat luar Indonesia |
| 59 | M 5.2 - 55 km NNW of Ruteng, Indonesia | `indonesia` | kosong | Judul USGS + koordinat Indonesia |

Kesimpulan:

- Sebelas baris ini valid sebagai `Gempabumi` berdasarkan format judul USGS `M <magnitudo>` dan data koordinat.
- **Sembilan baris (50–58) adalah kejadian luar Indonesia** dan sudah ditandai `domain_lokasi=luar_indonesia` serta `koordinat_domain=luar_indonesia`.
- Tidak ada dari sembilan baris luar Indonesia yang diberi provinsi/kabupaten Indonesia.
- Baris 49 (Banda Sea) dan 59 (Ruteng, Indonesia) tetap berada di domain Indonesia; keduanya tidak memiliki provinsi/kabupaten terisi.
- Tidak ada pencampuran antara jenis bencana dan domain geografis: `Gempabumi` adalah jenis bencana; domain Indonesia/luar Indonesia adalah lokasi.

Catatan:

- Baris 59 memiliki bukti toponimi `Ruteng, Indonesia` yang cukup untuk NTT/Manggarai, tetapi kolom provinsi/kabupaten dibiarkan kosong. Ini bukan kesalahan lokasi baru, melainkan under-extraction yang tidak wajib diperbaiki pada audit ini.

### 4.2 Baris 510

| Baris | Judul | Kategori | Bukti |
|---:|---|---|---|
| 510 | Gubernur Lampung Alihkan KBM ke Daring Akibat Sebaran Abu Anak Krakatau | `Gunungapi` | Isi menyebut `sebaran abu vulkanik Gunung Anak Krakatau` |

Kesimpulan: perubahan `Lainnya → Gunungapi` didukung judul dan isi. Ini adalah klasifikasi jenis bencana, bukan klasifikasi lokasi.

### 4.3 Rekap 50 perubahan kategori

- **38 perubahan adalah penyeragaman nama**, bukan perubahan makna:
  - `Gempa Bumi → Gempabumi` (33 baris)
  - `Gunung Api → Gunungapi` (4 baris)
  - `Gerakan Tanah / Longsor → Gerakan Tanah/Tanah Longsor` (1 baris)
- **12 perubahan substantif**:
  - 11 baris `Lainnya → Gempabumi`
  - 1 baris `Lainnya → Gunungapi`
- Seluruh 50 baris memiliki `kategori_berubah=ya`; seluruh `kategori_alasan` terisi.

## 5. Pemeriksaan 7 perubahan kabupaten/kota dan 2 provinsi

### 5.1 Tujuh perubahan kabupaten/kota

| Baris | Judul | Sebelum | Sesudah | Bukti toponimi | Status audit |
|---:|---|---|---|---|---|
| 12 | Gempa M5.7 29 km BaratLaut POHUWATO-GORONTALO | kosong | `Kabupaten Pohuwato` | `POHUWATO-GORONTALO` di judul dan `Wilayah`; gazetteer: Kab. Pohuwato, Gorontalo | Nama didukung; batas administratif perlu verifikasi |
| 14 | Gempa M5.1 125 km Tenggara BITUNG-SULUT | kosong | `Kota Bitung` | `BITUNG-SULUT` di judul dan `Wilayah`; gazetteer: Kota Bitung, Sulawesi Utara | Nama rujukan didukung; pusat gempa 125 km dari Bitung tidak membuktikan berada di Kota Bitung |
| 17 | Gempa M5.3 219 km TimurLaut TARAKAN-KALTARA | kosong | `Kota Tarakan` | `TARAKAN-KALTARA` di judul dan `Wilayah`; gazetteer: Kota Tarakan, Kalimantan Utara | Nama rujukan didukung; jarak 219 km membuat klaim batas kota tidak didukung |
| 18 | Gempa M5.9 68 km BaratDaya CALANG-ACEHJAYA | kosong | `Kabupaten Aceh Jaya` | `CALANG-ACEHJAYA` di judul dan `Wilayah`; gazetteer: Kab. Aceh Jaya, Aceh | Nama dan provinsi didukung; batas kabupaten untuk epicenter tidak terbukti |
| 19 | Gempa M6.1 14 km BaratDaya KODI-SUMBABARATDAYA-NTT | kosong | `Kabupaten Sumba Barat Daya` | `KODI-SUMBABARATDAYA-NTT` di judul dan `Wilayah`; gazetteer valid | Nama dan provinsi didukung; batas administratif perlu verifikasi |
| 24 | Gempa M5.1 33 km TimurLaut SARMI-PAPUA | kosong | `Kabupaten Sarmi` | `SARMI-PAPUA` di judul dan `Wilayah`; gazetteer valid | Nama dan provinsi didukung; batas administratif perlu verifikasi |
| 27 | Gempa M4.6 Pusat gempa berada di laut 49 km Barat KODI-SUMBABARATDAYA | `Kota Bima` | `Kabupaten Sumba Barat Daya` | `KODI-SUMBABARATDAYA` di judul dan `Wilayah`; `III Sumba Barat Daya` di `Dirasakan` | Provinsi dan rujukan didukung; epicenter di laut, batas kabupaten belum terverifikasi |

Rekap:

- **7/7** nama kabupaten/kota valid dan didukung sebagai **toponimi rujukan**.
- **0/7** memiliki bukti eksplisit bahwa pusat gempa berada di dalam batas administratif tersebut.
- Risiko tinggi terhadap klaim administratif: **14, 17, 18, 27**.
- Perlu verifikasi lebih lanjut: **12, 19, 24**.

### 5.2 Dua perubahan provinsi

| Baris | Sebelum | Sesudah | Bukti | Status |
|---:|---|---|---|---|
| 18 | kosong | `Aceh` | `CALANG-ACEHJAYA`; Calang/Aceh Jaya berada di Aceh | Didukung |
| 27 | `Nusa Tenggara Barat` | `Nusa Tenggara Timur` | `KODI-SUMBABARATDAYA`; Sumba Barat Daya terdaftar di NTT; `III Sumba Barat Daya` | Didukung sebagai rujukan; bukan bukti batas epicenter |

Catatan: pada baris 27, teks `NTT` tidak muncul eksplisit di judul seperti pada baris 19. Provinsi NTT didukung melalui toponimi `Sumba Barat Daya` dan gazetteer, bukan melalui penanda `-NTT` langsung.

## 6. Pemeriksaan kolom tambahan Stage 5

| Kolom | Temuan | Status |
|---|---|---|
| `kategori_asal` | Sama dengan `kategori` dataset lama untuk seluruh 787 baris | Konsisten |
| `kategori_berubah` | 50 `ya`, 737 `tidak`; cocok dengan perbedaan kategori lama/baru | Konsisten |
| `kategori_alasan` | Terisi 787 baris; 12 alasan substantif didukung judul/isi; 38 alasan penyeragaman mengikuti aturan deteksi | Konsisten, dengan catatan alasan penyeragaman tidak selalu menyebut kata “normalisasi” |
| `status_cakupan` | 53 `dalam_8_kategori`, 102 `di_luar_8_kategori`, 632 `tidak_terklasifikasi`; total 787 | Konsisten |
| `domain_lokasi` | 74 `indonesia`, 9 `luar_indonesia`, 704 `tidak_diketahui`; 9 baris luar benar, tetapi 59 baris berprovinsi Indonesia justru `tidak_diketahui` | **Meragukan/tidak konsisten sebagai domain kejadian** |
| `duplikat_judul` | 10 baris: 8 `Green forest fire...` (39–46) dan 2 `Pengacara Kamaruddin...` (220, 642) | Konsisten |
| `duplikat_url` | 0 baris; seluruh 787 URL unik | Konsisten |
| `duplikat_dengan` | Rujukan silang benar dan timbal balik; memakai nomor baris | Konsisten; nomor baris bergantung pada urutan data yang kini stabil |
| `catatan_stage5` | 721 kosong; 43 `kategori_diubah`, 7 `kategori_diubah;lokasi_dinormalkan`, 10 `duplikat_ditandai`, 6 `alamat_palsu_dihapus` | Konsisten sebagian; baris 214 yang alamatnya dipangkas tidak diberi catatan, dan catatan lokasi tidak membedakan rujukan vs verifikasi |
| `koordinat_verifikasi` | 40 `belum_diverifikasi`, 747 `tidak_ada`; tidak ada koordinat yang diklaim terverifikasi | Konsisten |
| `koordinat_domain` | 31 `indonesia`, 9 `luar_indonesia`, 747 `tidak_diketahui`; cocok dengan ada/tidaknya koordinat | Konsisten |

Temuan penting pada `domain_lokasi`:

- Logika kolom ini memakai koordinat bila tersedia; jika tidak, ia hanya mencari kata `Indonesia` pada judul, lalu penanda negara tertentu. Kolom ini tidak memakai `provinsi` yang sudah terisi.
- Akibatnya, baris 1–9 yang jelas berprovinsi Jambi, Kalimantan Selatan, Kepulauan Riau, dan seterusnya tetap `domain_lokasi=tidak_diketahui`.
- Sebaliknya, baris non-geohazard seperti `Medali pertama Indonesia di Asian Para Games 2026` (95), `Menhan dukung kerja sama pertahanan antara Indonesia dan Mesir` (167), `5 ABK Indonesia Selamat dari Kapal Tenggelam di Sri Lanka` (629), dan `Kena Kabut Asap, Malaysia... Indonesia...` (704) diberi `domain_lokasi=indonesia` hanya karena kata `Indonesia` ada di judul.
- Kolom ini masih berguna sebagai indikator konteks berita, tetapi **tidak boleh dipakai sebagai domain lokasi kejadian** tanpa koreksi.

Catatan duplikasi:

- Duplikasi judul sudah ada pada dataset lama; Stage 5 tidak menghapus atau menggabungkannya.
- Delapan baris `Green forest fire notification in Indonesia` memiliki URL GDACS berbeda, sehingga bukan baris hasil penggandaan.
- Dua baris `Pengacara Kamaruddin Simanjuntak Meninggal Dunia` berasal dari dua URL berbeda; keduanya ditandai dengan benar.

## 7. Rekomendasi koreksi untuk Stage 5.2

1. **Baris 27**: pertahankan `Nusa Tenggara Timur`; jangan kembali ke `Kota Bima`. Tambahkan status `perlu_verifikasi` untuk `kabupaten_kota`, atau kosongkan `kabupaten_kota` bila kolom tersebut wajib berarti batas administratif epicenter.
2. **Tujuh baris kabupaten/kota (12, 14, 17, 18, 19, 24, 27)**: tambahkan kolom `lokasi_verifikasi` atau `lokasi_basis` dengan nilai seperti `rujukan_toponimi`, `perlu_verifikasi`, dan `terverifikasi_admin`. Jangan menganggap semuanya sebagai lokasi administratif final.
3. **Baris 14, 17, 18, dan 27**: prioritaskan verifikasi karena jarak rujukan jauh atau epicenter dinyatakan di laut; bila tidak ada bukti tambahan, jangan gunakan `kabupaten_kota` untuk analisis spasial presisi.
4. **`domain_lokasi`**: hitung ulang dengan urutan: koordinat domain → provinsi terisi → penanda lokasi eksplisit; atau ganti nama menjadi `domain_berita`. Jangan memakai kolom ini sendirian untuk memfilter kejadian Indonesia.
5. **`catatan_stage5`**: tambahkan catatan untuk baris 214 yang alamatnya dipangkas, serta catatan lokasi yang membedakan rujukan toponimi dari verifikasi administratif.
6. **`duplikat_dengan`**: pertahankan penandaan sekarang, tetapi untuk versi berikutnya gunakan ID stabil/URL agregat agar tidak bergantung pada nomor baris.
7. **Baris 59**: opsional, lengkapi provinsi/kabupaten dari toponimi `Ruteng, Indonesia` bila aturan ekstraksi ingin ditingkatkan; ini bukan kesalahan baru.

## 8. Status kelayakan dataset Stage 5

**Layak terbatas/bersyarat (conditional) untuk analisis eksploratif; belum layak untuk klaim tervalidasi penuh.**

- Integritas baris: **baik** — 787 baris, 787 URL unik, tidak ada penghapusan atau penggandaan tak sengaja.
- Klasifikasi jenis bencana: **baik untuk 12 perubahan substantif** — seluruhnya didukung judul/isi; sembilan kejadian USGS luar Indonesia tetap berada di domain luar Indonesia.
- Lokasi provinsi: **cukup baik sebagai rujukan** — dua perubahan didukung.
- Lokasi kabupaten/kota: **belum layak sebagai lokasi administratif presisi** — 7/7 baru berupa rujukan toponimi; 4 berisiko tinggi dan 3 perlu verifikasi.
- `domain_lokasi`: **belum layak sebagai filter domain kejadian** karena tidak konsisten dengan `provinsi` dan terlalu bergantung pada kata `Indonesia` di judul.
- Validasi koordinat: **belum ada verifikasi independen**; 40 koordinat tetap `belum_diverifikasi`.

Penggunaan yang disarankan: filter berdasarkan `kategori` dan `koordinat_domain`; gunakan `provinsi` sebagai rujukan; jangan memperlakukan `kabupaten_kota` pada tujuh baris tersebut sebagai batas administratif terverifikasi; jangan memakai `domain_lokasi` sendirian untuk memilih kejadian Indonesia.

## 9. Pengujian

- Perintah: `python -m unittest -q test_category_detector test_location_extractor test_stage5_quality`
- Hasil: **25 test lulus**.
- Catatan: test tersebut menguji aturan ekstraksi/klasifikasi, bukan kebenaran lokasi per baris. Kelulusan test tidak menghapus temuan audit lokasi di atas.
- `unittest discover` penuh masih memiliki masalah pre-existing pada `test_scraper` (`get_soup` tidak tersedia); masalah ini tidak terkait Stage 5 dan tidak diubah dalam audit ini.
