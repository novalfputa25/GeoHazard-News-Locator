# Matriks Cakupan 8 Kategori

Tanggal: **2026-11-02**  
Baseline: `data/geohazard_news_final_20261101T150501Z.csv` (787 baris)  
Sumber acuan: `docs/MASTER_SOURCE_REGISTER.csv`

## 1. Definisi cakupan

Kategori dianggap **tercakup secara operasional** hanya jika memenuhi seluruh syarat berikut:

1. Ada sumber resmi atau sumber terstruktur yang dapat diakses sah.
2. Sumber menghasilkan kejadian, bukan hanya peta risiko, profil, atau artikel umum.
3. Ada bukti uji akses dan contoh field yang dapat dipetakan.
4. Ada izin/lisensi atau dasar penggunaan yang jelas.
5. Kejadian dapat diidentifikasi dengan waktu dan lokasi yang dapat diverifikasi.

Berita, peta risiko, atlas, dan dashboard manual **tidak** memenuhi syarat sebagai feed kejadian.

## 2. Ringkasan

- Baris yang masuk 8 kategori target: **53 dari 787 (6,7%)**.
- Kategori yang memiliki baris target: **4 dari 8**.
- Kategori tanpa satu pun baris: **Tsunami, Likuefaksi, Penurunan Muka Tanah, Semburan Gas dan Lumpur**.
- Hanya **Gempabumi** yang memiliki kombinasi sumber resmi terstruktur aktif + data lokasi + waktu kejadian.
- Gunungapi hanya terwakili berita; sumber resmi PVMBG/MAGMA memerlukan izin.
- Tsunami tidak memiliki feed kejadian mandiri; BMKG hanya menyediakan field potensi pada gempa.
- Likuefaksi, penurunan muka tanah, dan semburan belum memiliki feed kejadian yang terverifikasi.
- Abrasi hanya terwakili berita; peta risiko BNPB tidak dapat dihitung sebagai kejadian.

## 3. Matriks utama

| Kategori | Baris final | Komposisi sumber | Sumber resmi/struktural | Status cakupan | Waktu kejadian | Koordinat | Gap utama | Prioritas |
|---|---:|---|---|---|---:|---:|---|---|
| **Gempabumi** | 44 | BMKG 29; USGS 11; GDACS 1; berita 3 (ANTARA, BBC, CNBC) | BMKG XML aktif; USGS Atom aktif | **AKTIF_RESMI_SEBAGIAN** | 41 aktual; 1 tanggal saja; 2 tidak diketahui | 40/44 | 3 berita tanpa struktur; arsip BMKG terbatas; USGS global | P1 |
| **Gunungapi** | 5 | CNN 2; Liputan6 1; Media Indonesia 1; Tempo 1 | PVMBG/MAGMA ada, tetapi `PERLU_IZIN` | **PERLU_IZIN** | 2 tanggal saja; 3 tidak diketahui | 0/5 | Tidak ada feed resmi aktif; semua baris berasal dari berita | P0 |
| **Tsunami** | 0 | — | BMKG hanya field “Potensi” pada gempa | **TIDAK_ADA_FEED_KEJADIAN** | 0 | 0 | 15 baris Gempabumi menyebut tsunami, tetapi bukan kejadian tsunami terpisah | P1 |
| **Gerakan Tanah/Tanah Longsor** | 1 | Mongabay 1 | Portal MBG `field-reports` 2.397 titik, tetapi `PERLU_IZIN`; BNPB `TanahLongsor_2022` statis | **PERLU_IZIN + BERITA** | 1 aktual | 0/1 | Tidak ada feed aktif; sumber resmi belum diizinkan; layer BNPB 2022 bukan terkini | P0 |
| **Likuefaksi** | 0 | — | Atlas Badan Geologi 2019 (timeout); InaRISK layer 521 | **PETA_RISIKO_SAJA** | 0 | 0 | Tidak ada feed kejadian; peta kerentanan bukan kejadian | P2 |
| **Abrasi dan Akresi** | 3 | CNN 1; Mongabay 1; kumparan 1 | InaRISK layer 521; KKP BPISDKP 404 | **BERITA + PETA_RISIKO** | 0 aktual; 3 tidak diketahui | 0/3 | Tidak ada feed resmi; semua baris berita; halaman KKP tidak tersedia | P2 |
| **Penurunan Muka Tanah** | 0 | — | Publikasi PATGTL/BIG; tidak ada feed kejadian | **PUBLIKASI_SAJA** | 0 | 0 | Tidak ada katalog kejadian; publikasi/riset tidak dapat dijadikan feed | P2 |
| **Semburan Gas dan Lumpur** | 0 | — | BPLS Sidoarjo hanya halaman informasi | **INFORMASI_MANUAL** | 0 | 0 | Tidak ada API/katalog kejadian; perlu riset sumber | P2 |

## 4. Rincian bukti per kategori

### Gempabumi

- Sumber aktif: `bmkg_autogempa`, `bmkg_gempa_terkini`, `bmkg_gempa_dirasakan`, `usgs_m45`, `gdacs_all`.
- 41 dari 44 baris memiliki waktu kejadian aktual; 40 memiliki koordinat.
- Koordinat: 29 dari URL BMKG, 11 dari isi USGS; 31 di Indonesia, 9 di luar Indonesia; semua `belum_diverifikasi`.
- Keterbatasan: feed BMKG adalah jendela terbatas; USGS/GDACS bukan sumber resmi Indonesia; 3 baris berita tidak punya struktur kejadian.
- Status: **paling siap**, tetapi belum lengkap untuk arsip dan verifikasi lokasi.

### Gunungapi

- 5 baris berasal dari CNN, Liputan6, Media Indonesia, dan Tempo.
- Tidak ada baris yang memakai PVMBG/MAGMA.
- PVMBG/MAGMA menyediakan informasi letusan, laporan, level aktivitas, dan VONA, tetapi `robots.txt` melarang akses dan penggunaan otomatis memerlukan izin.
- Tidak ada koordinat pada 5 baris; hanya 2 baris memiliki tanggal kejadian.
- Status: **belum tercakup secara operasional**.

### Tsunami

- 0 baris kategori Tsunami.
- 15 baris Gempabumi menyebut “tsunami”, umumnya sebagai potensi atau konteks, bukan kejadian tsunami terpisah.
- BMKG memiliki field “Potensi” pada XML gempa, tetapi tidak ada feed tsunami mandiri yang terverifikasi.
- Jangan memecah satu baris gempa menjadi dua kejadian (gempa dan tsunami) tanpa bukti peristiwa terpisah.
- Status: **belum ada feed kejadian**.

### Gerakan Tanah/Tanah Longsor

- 1 baris berasal dari Mongabay.
- Portal MBG memiliki 2.397 titik laporan lapangan, 619 `doc_id`, dan 363 tanggal unik, tetapi berada di balik `robots.txt` yang melarang dan memerlukan izin.
- BNPB `TanahLongsor_2022` adalah layer titik statis 2022; query data langsung gagal 500.
- Tidak ada koordinat pada satu-satunya baris target.
- Status: **sumber resmi menjanjikan, tetapi belum boleh dipakai otomatis**.

### Likuefaksi

- 0 baris.
- Atlas Zona Kerentanan Likuefaksi Indonesia (Badan Geologi, 2019) adalah peta kerentanan, bukan katalog kejadian.
- Halaman atlas ditemukan melalui pencarian, tetapi GET langsung timeout.
- InaRISK layer likuefaksi mengembalikan 521.
- Status: **peta risiko saja**.

### Abrasi dan Akresi

- 3 baris berasal dari CNN, Mongabay, dan kumparan; tidak ada waktu kejadian aktual atau koordinat.
- InaRISK layer abrasi mengembalikan 521; halaman BPISDKP KKP berakhir 404.
- KKP root hanya portal informasi.
- Status: **berita + peta risiko**, bukan feed kejadian.

### Penurunan Muka Tanah

- 0 baris.
- PATGTL/BIG memiliki publikasi dan peta tematik, tetapi tidak ada feed kejadian yang terverifikasi.
- Status: **publikasi saja**.

### Semburan Gas dan Lumpur

- 0 baris.
- BPLS Sidoarjo memiliki halaman informasi, tetapi bukan API/katalog kejadian.
- Status: **informasi manual**; perlu riset sumber khusus.

## 5. Kesiapan sumber per kategori

| Kebutuhan | Gempabumi | Gunungapi | Tsunami | Gerakan Tanah | Likuefaksi | Abrasi | Penurunan Muka Tanah | Semburan |
|---|---|---|---|---|---|---|---|---|
| Feed resmi aktif | Ya (BMKG) | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak | Tidak |
| Sumber resmi tersedia tetapi perlu izin | Sebagian | Ya | Sebagian | Ya | Ya (peta) | Ya (peta) | Ya (publikasi) | Sebagian |
| Data berita | Ya | Ya | Tidak langsung | Ya | Tidak | Ya | Tidak | Tidak |
| Peta risiko | Ya | Ya | Ya | Ya | Ya | Ya | Ya | Tidak |
| Waktu kejadian aktual | 41/44 | 0/5 | 0 | 1/1 | 0 | 0/3 | 0 | 0 |
| Koordinat | 40/44 | 0/5 | 0 | 0/1 | 0 | 0/3 | 0 | 0 |
| Status operasional | **Sebagian** | **Belum** | **Belum** | **Belum** | **Belum** | **Belum** | **Belum** | **Belum** |

## 6. Interpretasi

1. **Jumlah baris bukan cakupan.** Ada 787 baris, tetapi hanya 53 yang masuk kategori target dan hanya Gempabumi yang memiliki data resmi terstruktur.
2. **Peta risiko tidak sama dengan kejadian.** InaRISK/BIG dapat menjadi konteks, tetapi tidak boleh menambah hitungan event.
3. **Berita tidak sama dengan laporan resmi.** Berita bisa menjadi sinyal awal, tetapi tidak boleh menjadi bukti tunggal untuk status kejadian, waktu, atau koordinat.
4. **Izin adalah blocker utama.** Untuk Gunungapi dan Gerakan Tanah, sumber terbaik sudah ada, tetapi tidak boleh diakses otomatis tanpa izin.
5. **Kategori kosong bukan berarti tidak ada bahaya.** Itu berarti belum ada sumber kejadian yang layak dan terverifikasi.

## 7. Rekomendasi prioritas

### P0

- Urus izin PVMBG/Badan Geologi untuk Portal MBG, API PVMBG, dan MAGMA.
- Validasi mekanisme resmi DIBI/BNPB untuk data kejadian individual.
- Tetapkan kebijakan agar tidak mengklaim kategori tercakup hanya karena ada berita atau peta risiko.

### P1

- Stabilkan pipeline Gempabumi: `event_id`, `source_id`, `collected_at`, snapshot mentah, validasi koordinat.
- Pisahkan tsunami sebagai atribut gempa sampai ada feed tsunami mandiri.
- Audit manual kandidat underclassification Gunungapi, terutama status Gunung Sinabung.

### P2

- Riset sumber resmi untuk Likuefaksi, Abrasi, Penurunan Muka Tanah, dan Semburan.
- Jangan mengotomatiskan PDF, atlas, atau dashboard sebelum ada API/ekspor resmi.

## 8. Kesimpulan

Matriks ini menunjukkan bahwa **cakupan 8 kategori belum terpenuhi**. Yang tersedia saat ini adalah:

- Gempabumi: sumber resmi terstruktur sebagian.
- Gunungapi, Gerakan Tanah, Tsunami: sumber resmi belum aktif atau hanya berupa potensi/berita.
- Likuefaksi, Abrasi, Penurunan Muka Tanah, Semburan: belum ada feed kejadian yang terverifikasi.

Karena itu, dataset tidak boleh dipromosikan sebagai “lengkap 8 kategori” sampai register sumber, izin, dan bukti kejadian untuk kategori yang hilang tersedia.
