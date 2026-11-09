# Source Coverage 8 Kategori

Tanggal: **2026-11-04**  
Registry: `docs/SOURCE_COVERAGE_SOURCES.csv`  
Pemetaan: `docs/SOURCE_CATEGORY_MAP.csv`  
Status: **implementasi registry dan generator ringkasan**

## 1. Batas dan definisi

- Registry ini memetakan sumber ke delapan kategori geohazard target.
- `kejadian_aktual` hanya dihitung sebagai cakupan operasional bila sumber aktif di pipeline dan pemetaan berstatus `terverifikasi`.
- `laporan_berita`, `katalog_historis`, `peta_risiko`, `informasi_kerentanan`, `penelitian_kajian`, `informasi_manual`, `atribut_bahaya`, dan `katalog_data` tidak dihitung sebagai feed kejadian aktif.
- Status akses, izin, dan implementasi disimpan terpisah agar akses HTTP tidak otomatis dianggap sebagai izin atau kesiapan operasional.
- Komposisi jenis data mencakup semua status; hitungan operasional tetap memakai kolom event aktif terverifikasi.
- Baseline dan database tidak diubah oleh generator laporan ini.

## 2. Ringkasan registry

- Sumber terdaftar: **42**.
- Baris pemetaan sumber-kategori: **111**.
- Sumber aktif pipeline: **7**.
- Sumber dengan status izin `perlu_izin`: **15**.
- Sumber belum tersedia/tidak sesuai: **6**.
- Sumber belum diverifikasi: **4**.

### Status akses (teknis)

| Status akses | Jumlah |
|---|---:|
| `belum_diverifikasi` | 4 |
| `belum_tersedia` | 6 |
| `perlu_izin` | 14 |
| `terverifikasi_aktif` | 7 |
| `terverifikasi_manual` | 11 |

### Status izin (legal)

| Status izin | Jumlah |
|---|---:|
| `belum_jelas` | 20 |
| `perlu_izin` | 15 |
| `terbuka` | 7 |

### Status implementasi

| Status implementasi | Jumlah |
|---|---:|
| `aktif_pipeline` | 7 |
| `belum_diimplementasikan` | 16 |
| `manual` | 9 |
| `tersedia_nonaktif` | 1 |
| `tidak_direncanakan` | 9 |

### Rekonsiliasi status

- Status izin `perlu_izin`: **15** sumber.
- Status akses `perlu_izin`: **14** sumber.
- Sumber dengan status izin `perlu_izin` tetapi status akses bukan `perlu_izin`: **1** (`reliefweb_v2`).
- `status_akses` dan `status_izin` adalah dimensi berbeda; angka pada kedua tabel tidak dipaksakan sama.

## 3. Matriks cakupan

| Kategori | Sumber | Aktif pipeline | Event aktif terverifikasi | Event resmi aktif | Kandidat event resmi | Berita | Katalog historis | Peta risiko | Manual/kajian | Status cakupan | Prioritas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| **Gunungapi** | 19 | 2 | 0 | 0 | 4 | 3 | 1 | 2 | 8 | **KANDIDAT_RESMI_PERLU_IZIN** | P0 |
| **Gempabumi** | 20 | 7 | 5 | 3 | 3 | 3 | 2 | 2 | 3 | **TERCAKUP_OPERASIONAL** | P1 |
| **Tsunami** | 16 | 5 | 0 | 0 | 0 | 3 | 1 | 3 | 7 | **KANDIDAT_KEJADIAN** | P1 |
| **Gerakan Tanah/Tanah Longsor** | 16 | 2 | 0 | 0 | 4 | 3 | 3 | 2 | 3 | **KANDIDAT_RESMI_PERLU_IZIN** | P0 |
| **Likuefaksi** | 11 | 2 | 0 | 0 | 0 | 3 | 0 | 3 | 3 | **HANYA_BERITA_DAN_PETA_RISIKO_DAN_INFORMASI_MANUAL** | P2 |
| **Abrasi dan Akresi** | 11 | 2 | 0 | 0 | 0 | 3 | 0 | 2 | 5 | **HANYA_BERITA_DAN_PETA_RISIKO_DAN_INFORMASI_MANUAL** | P2 |
| **Penurunan Muka Tanah** | 9 | 2 | 0 | 0 | 0 | 3 | 0 | 0 | 5 | **HANYA_BERITA_DAN_INFORMASI_MANUAL** | P2 |
| **Semburan Gas dan Lumpur** | 9 | 2 | 0 | 0 | 0 | 3 | 0 | 0 | 5 | **HANYA_BERITA_DAN_INFORMASI_MANUAL** | P2 |

## 4. Rincian sumber per kategori

### Gunungapi

- Status cakupan: **KANDIDAT_RESMI_PERLU_IZIN**.
- Prioritas: **P0**.
- Sumber: 19.
- Komposisi jenis data: `informasi_kerentanan`=2, `informasi_manual`=5, `katalog_data`=1, `katalog_historis`=1, `kejadian_aktual`=5, `laporan_berita`=3, `peta_risiko`=2.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `big_atlas_kebencanaan` - BIG - Atlas Kebencanaan [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `bnpb_gis_inarisk_catalog` - BNPB InaRISK - Katalog ArcGIS [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `magma_informasi_letusan` - MAGMA - Informasi Letusan [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `magma_laporan_harian` - MAGMA - Laporan Harian/Aktivitas [perlu_izin; perlu_izin; belum_diimplementasikan]: informasi_manual (kandidat; P0).
- `magma_tingkat_aktivitas` - MAGMA - Tingkat Aktivitas [perlu_izin; perlu_izin; belum_diimplementasikan]: informasi_manual (kandidat; P0).
- `magma_vona` - MAGMA - VONA [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `portalmbg_volcano` - Portal MBG - Gunung Api [perlu_izin; perlu_izin; belum_diimplementasikan]: informasi_kerentanan (kandidat; P0).
- `pvmbg_data_dasar` - PVMBG - Data Dasar Gunung Api [perlu_izin; perlu_izin; belum_diimplementasikan]: informasi_kerentanan (kandidat; P0).
- `pvmbg_kajian_kejadian` - PVMBG - Kajian Kejadian [perlu_izin; perlu_izin; belum_diimplementasikan]: katalog_historis (kandidat; P0).
- `pvmbg_laporan_singkat` - PVMBG - Laporan Singkat [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `pvmbg_press_release` - PVMBG - Press Release [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `pvmbg_tingkat_aktivitas` - PVMBG - Tingkat Aktivitas [perlu_izin; perlu_izin; belum_diimplementasikan]: informasi_manual (kandidat; P0).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).

### Gempabumi

- Status cakupan: **TERCAKUP_OPERASIONAL**.
- Prioritas: **P1**.
- Sumber: 20.
- Komposisi jenis data: `informasi_manual`=2, `katalog_data`=1, `katalog_historis`=2, `kejadian_aktual`=10, `laporan_berita`=3, `peta_risiko`=2.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `big_atlas_kebencanaan` - BIG - Atlas Kebencanaan [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bmkg_autogempa` - BMKG Open Data - Autogempa [terverifikasi_aktif; terbuka; aktif_pipeline]: kejadian_aktual (terverifikasi; P1).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `bmkg_gempa_dirasakan` - BMKG Open Data - Gempa Dirasakan [terverifikasi_aktif; terbuka; aktif_pipeline]: kejadian_aktual (terverifikasi; P1).
- `bmkg_gempa_terkini` - BMKG Open Data - Gempa Terkini [terverifikasi_aktif; terbuka; aktif_pipeline]: kejadian_aktual (terverifikasi; P1).
- `bmkg_tsunami_catalog` - BMKG - Katalog Gempa Bumi dan Tsunami [belum_diverifikasi; belum_jelas; manual]: katalog_historis (kandidat; P1).
- `bnpb_gis_inarisk_catalog` - BNPB InaRISK - Katalog ArcGIS [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `gdacs_all` - GDACS RSS semua kejadian [terverifikasi_aktif; terbuka; aktif_pipeline]: kejadian_aktual (terverifikasi; P1).
- `gdacs_eq_24h` - GDACS - Gempa 24 jam [terverifikasi_manual; belum_jelas; tersedia_nonaktif]: kejadian_aktual (kandidat; P2).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `portalmbg_destructive_eq` - Portal MBG - Gempa Merusak [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P1).
- `pvmbg_kajian_kejadian` - PVMBG - Kajian Kejadian [perlu_izin; perlu_izin; belum_diimplementasikan]: katalog_historis (kandidat; P1).
- `pvmbg_laporan_singkat` - PVMBG - Laporan Singkat [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P1).
- `pvmbg_press_release` - PVMBG - Press Release [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P1).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).
- `usgs_m45` - USGS M4.5+ Atom [terverifikasi_aktif; terbuka; aktif_pipeline]: kejadian_aktual (terverifikasi; P1).

### Tsunami

- Status cakupan: **KANDIDAT_KEJADIAN**.
- Prioritas: **P1**.
- Sumber: 16.
- Komposisi jenis data: `atribut_bahaya`=3, `informasi_manual`=3, `katalog_data`=1, `katalog_historis`=1, `kejadian_aktual`=2, `laporan_berita`=3, `peta_risiko`=3.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `big_atlas_kebencanaan` - BIG - Atlas Kebencanaan [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bmkg_autogempa` - BMKG Open Data - Autogempa [terverifikasi_aktif; terbuka; aktif_pipeline]: atribut_bahaya (kandidat; P1).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `bmkg_gempa_terkini` - BMKG Open Data - Gempa Terkini [terverifikasi_aktif; terbuka; aktif_pipeline]: atribut_bahaya (kandidat; P1).
- `bmkg_tsunami_catalog` - BMKG - Katalog Gempa Bumi dan Tsunami [belum_diverifikasi; belum_jelas; manual]: katalog_historis (kandidat; P1).
- `bmkg_tsunami_page` - BMKG - Gempa Berpotensi Tsunami [terverifikasi_manual; terbuka; manual]: informasi_manual (kandidat; P1).
- `bnpb_gis_inarisk_catalog` - BNPB InaRISK - Katalog ArcGIS [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bnpb_inarisk_tsunami_map` - BNPB InaRISK - Peta Bahaya Tsunami [belum_diverifikasi; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `gdacs_all` - GDACS RSS semua kejadian [terverifikasi_aktif; terbuka; aktif_pipeline]: kejadian_aktual (kandidat; P1).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `portalmbg_destructive_eq` - Portal MBG - Gempa Merusak [perlu_izin; perlu_izin; belum_diimplementasikan]: atribut_bahaya (kandidat; P1).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).

### Gerakan Tanah/Tanah Longsor

- Status cakupan: **KANDIDAT_RESMI_PERLU_IZIN**.
- Prioritas: **P0**.
- Sumber: 16.
- Komposisi jenis data: `informasi_manual`=2, `katalog_data`=1, `katalog_historis`=3, `kejadian_aktual`=5, `laporan_berita`=3, `peta_risiko`=2.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `big_atlas_kebencanaan` - BIG - Atlas Kebencanaan [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `bnpb_gis_inarisk_catalog` - BNPB InaRISK - Katalog ArcGIS [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bnpb_gis_tanahlongsor_2022` - BNPB - TanahLongsor_2022 [terverifikasi_manual; belum_jelas; tidak_direncanakan]: katalog_historis (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `portalmbg_field_reports` - Portal MBG - Field Reports [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `portalmbg_sigab` - Portal MBG - SIGAB [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `pvmbg_gerakan_tanah` - PVMBG - Gerakan Tanah (rekap) [perlu_izin; perlu_izin; belum_diimplementasikan]: katalog_historis (kandidat; P0).
- `pvmbg_kajian_kejadian` - PVMBG - Kajian Kejadian [perlu_izin; perlu_izin; belum_diimplementasikan]: katalog_historis (kandidat; P0).
- `pvmbg_laporan_singkat` - PVMBG - Laporan Singkat [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `pvmbg_press_release` - PVMBG - Press Release [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P0).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).

### Likuefaksi

- Status cakupan: **HANYA_BERITA_DAN_PETA_RISIKO_DAN_INFORMASI_MANUAL**.
- Prioritas: **P2**.
- Sumber: 11.
- Komposisi jenis data: `informasi_manual`=2, `katalog_data`=1, `kejadian_aktual`=2, `laporan_berita`=3, `peta_risiko`=3.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `bnpb_gis_inarisk_catalog` - BNPB InaRISK - Katalog ArcGIS [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bnpb_gis_likuefaksi` - BNPB InaRISK - Bahaya Likuefaksi [belum_tersedia; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_likuefaksi_atlas` - Badan Geologi - Atlas Zona Kerentanan Likuefaksi [belum_tersedia; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `portalmbg_field_reports` - Portal MBG - Field Reports [perlu_izin; perlu_izin; belum_diimplementasikan]: kejadian_aktual (belum_terverifikasi; P2).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).

### Abrasi dan Akresi

- Status cakupan: **HANYA_BERITA_DAN_PETA_RISIKO_DAN_INFORMASI_MANUAL**.
- Prioritas: **P2**.
- Sumber: 11.
- Komposisi jenis data: `informasi_manual`=4, `katalog_data`=1, `kejadian_aktual`=1, `laporan_berita`=3, `peta_risiko`=2.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `bnpb_gis_abrasi` - BNPB InaRISK - Kerentanan Gelombang Ekstrem/Abrasi [belum_tersedia; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bnpb_gis_inarisk_catalog` - BNPB InaRISK - Katalog ArcGIS [terverifikasi_manual; belum_jelas; tidak_direncanakan]: peta_risiko (kandidat; P2).
- `bpisdkp_abrasi` - BPISDKP - Abrasi Akresi [belum_tersedia; belum_jelas; tidak_direncanakan]: informasi_manual (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `kkp_root` - KKP - Portal Kementerian [terverifikasi_manual; belum_jelas; tidak_direncanakan]: informasi_manual (kandidat; P2).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).

### Penurunan Muka Tanah

- Status cakupan: **HANYA_BERITA_DAN_INFORMASI_MANUAL**.
- Prioritas: **P2**.
- Sumber: 9.
- Komposisi jenis data: `informasi_kerentanan`=1, `informasi_manual`=3, `katalog_data`=1, `kejadian_aktual`=1, `laporan_berita`=3.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_patgtl` - Badan Geologi - PATGTL [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_subsidence_pantura` - Badan Geologi - Penurunan Muka Tanah Pantura [belum_diverifikasi; belum_jelas; manual]: informasi_kerentanan (kandidat; P2).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).

### Semburan Gas dan Lumpur

- Status cakupan: **HANYA_BERITA_DAN_INFORMASI_MANUAL**.
- Prioritas: **P2**.
- Sumber: 9.
- Komposisi jenis data: `informasi_manual`=4, `katalog_data`=1, `kejadian_aktual`=1, `laporan_berita`=3.

- `antaranews_warta_bumi` - ANTARA - Warta Bumi [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `bmkg_berita` - BMKG - Berita [terverifikasi_manual; terbuka; manual]: laporan_berita (kandidat; P2).
- `bpls_sda` - BPLS - Pusat Pengendalian Lumpur Sidoarjo [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `bpls_sidoarjo_history` - BPLS - Sejarah Semburan Sidoarjo [belum_diverifikasi; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `data_bnpb_satu_data` - Portal Satu Data Bencana BNPB [belum_tersedia; belum_jelas; belum_diimplementasikan]: katalog_data (kandidat; P2).
- `dibi_dashboard` - DIBI BNPB - Dashboard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `geologi_geohazard` - Badan Geologi - GeoHazard [terverifikasi_manual; belum_jelas; manual]: informasi_manual (kandidat; P2).
- `mongabay_indonesia` - Mongabay Indonesia [terverifikasi_aktif; belum_jelas; aktif_pipeline]: laporan_berita (kandidat; P2).
- `reliefweb_v2` - ReliefWeb API v2 [belum_tersedia; perlu_izin; belum_diimplementasikan]: kejadian_aktual (kandidat; P2).

## 5. Temuan utama

- **Gempabumi** memiliki sumber resmi aktif terverifikasi dari BMKG dan sumber internasional pendukung. Ini satu-satunya kategori dengan cakupan operasional.
- **Gunungapi dan Gerakan Tanah/Tanah Longsor** memiliki kandidat sumber resmi (PVMBG/Portal MBG/MAGMA) dengan status izin `perlu_izin`; belum boleh diotomatisasi.
- **Tsunami** memiliki atribut potensi pada feed BMKG, kandidat kejadian internasional dari GDACS, katalog historis BMKG, dan peta bahaya BNPB. Tidak ada feed peringatan tsunami mandiri yang terverifikasi aktif.
- **Likuefaksi, Abrasi dan Akresi, Penurunan Muka Tanah, dan Semburan Gas dan Lumpur** belum memiliki feed kejadian aktif terverifikasi. Yang tersedia adalah berita, peta risiko, atlas, publikasi, atau informasi manual.
- Peta risiko, atlas, dashboard, dan katalog data tidak boleh menambah hitungan kejadian aktual.

## 6. Sumber yang perlu ditindaklanjuti

### Perlu izin (status izin)

- `magma_informasi_letusan` (`status_akses`: `perlu_izin`)
- `magma_laporan_harian` (`status_akses`: `perlu_izin`)
- `magma_tingkat_aktivitas` (`status_akses`: `perlu_izin`)
- `magma_vona` (`status_akses`: `perlu_izin`)
- `portalmbg_destructive_eq` (`status_akses`: `perlu_izin`)
- `portalmbg_field_reports` (`status_akses`: `perlu_izin`)
- `portalmbg_sigab` (`status_akses`: `perlu_izin`)
- `portalmbg_volcano` (`status_akses`: `perlu_izin`)
- `pvmbg_data_dasar` (`status_akses`: `perlu_izin`)
- `pvmbg_gerakan_tanah` (`status_akses`: `perlu_izin`)
- `pvmbg_kajian_kejadian` (`status_akses`: `perlu_izin`)
- `pvmbg_laporan_singkat` (`status_akses`: `perlu_izin`)
- `pvmbg_press_release` (`status_akses`: `perlu_izin`)
- `pvmbg_tingkat_aktivitas` (`status_akses`: `perlu_izin`)
- `reliefweb_v2` (`status_akses`: `belum_tersedia`)

### Belum tersedia atau tidak sesuai

- `bnpb_gis_abrasi`
- `bnpb_gis_likuefaksi`
- `bpisdkp_abrasi`
- `data_bnpb_satu_data`
- `geologi_likuefaksi_atlas`
- `reliefweb_v2`

### Belum diverifikasi

- `bmkg_tsunami_catalog`
- `bnpb_inarisk_tsunami_map`
- `bpls_sidoarjo_history`
- `geologi_subsidence_pantura`

## 7. Rekomendasi

1. Pertahankan klaim cakupan operasional hanya untuk Gempabumi sampai ada sumber kejadian resmi aktif untuk kategori lain.
2. Urus izin tertulis PVMBG/Badan Geologi sebelum mengaktifkan API PVMBG, Portal MBG, atau MAGMA.
3. Validasi katalog tsunami BMKG dan layer InaRISK sebagai sumber historis/peta, bukan feed kejadian.
4. Cari sumber kejadian terstruktur untuk Likuefaksi, Abrasi dan Akresi, Penurunan Muka Tanah, dan Semburan Gas dan Lumpur.
5. Jangan mengubah baseline atau database hanya karena registry ini diperbarui.

## 8. Kesimpulan

Registry menunjukkan bahwa delapan kategori sudah memiliki pemetaan sumber, tetapi baru Gempabumi yang tercakup secara operasional. Kategori lain memiliki kandidat resmi, berita, katalog historis, peta risiko, atau informasi manual yang harus dibedakan dari feed kejadian aktif.
