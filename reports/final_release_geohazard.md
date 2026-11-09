# Final Release GeoHazard News Locator

- Tanggal proses: 2026-11-01 15:05 UTC
- Sumber: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_located_20261101T144531Z_stage5_4.csv`
- SHA-256 sumber sebelum: `bb1bc6d4343d2b8bb1982677d09a1e6f4183dc5032f1845335299bc38c5c20db`
- SHA-256 sumber sesudah: `bb1bc6d4343d2b8bb1982677d09a1e6f4183dc5032f1845335299bc38c5c20db`
- Sumber tidak berubah: **True**
- Keluaran: `C:\Users\LENOVO\GeoHazard-News-Locator\data\geohazard_news_final_20261101T150501Z.csv`
- SHA-256 keluaran: `be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06`
- Mode: non-destruktif; 787 baris dipertahankan; tidak ada penghapusan baris.

## 1. Ringkasan

- Baris: **787 -> 787**.
- Kolom: **39 -> 51**.
- Field baru: **12**.
- `published_time` diproses: **787** baris; **758** berubah teks; **29** sudah ISO.
- Kategori dipetakan ke `Lainnya`: **85** baris.
- Koreksi `desa_kelurahan`: **1** sel.
- `event_time` dipertahankan: **64** baris terisi.
- Duplikat judul/isi/URL: **10 / 4 / 0** baris.

## 2. Perubahan yang disengaja

| Perubahan | Baris/sel | Alasan |
|---|---:|---|
| Normalisasi `published_time` | 758 berubah / 787 diproses | ISO 8601; nilai mentah dan zona sumber disimpan |
| `kategori` out-of-scope -> `Lainnya` | 85 | Kontrak final 8 kategori target + `Lainnya`; nilai asal disimpan |
| `desa_kelurahan` generik dikosongkan | 1 | Bukti audit: 'Banjir' adalah kata umum, bukan nama desa |

Kolom lama lain yang berubah di luar tiga perubahan di atas: **0 sel**.

## 3. Kontrak kategori

Kategori final hanya berisi 8 kategori target + `Lainnya`.

| Kategori final | Jumlah |
|---|---:|
| Abrasi dan Akresi | 3 |
| Gempabumi | 44 |
| Gerakan Tanah/Tanah Longsor | 1 |
| Gunungapi | 5 |
| Lainnya | 734 |
| Likuefaksi | 0 |
| Penurunan Muka Tanah | 0 |
| Semburan Gas dan Lumpur | 0 |
| Tsunami | 0 |

Kategori di luar cakupan tidak dipaksa menjadi kategori target. Nilai asal tetap tersimpan di `kategori_sebelum_final`, `kategori_asal`, dan `status_cakupan=di_luar_8_kategori`.

| Kategori sebelum final | Jumlah |
|---|---:|
| Lainnya | 649 |
| Kebakaran Hutan dan Lahan | 71 |
| Gempabumi | 44 |
| Cuaca Ekstrem | 14 |
| Gunungapi | 5 |
| Abrasi dan Akresi | 3 |
| Gerakan Tanah/Tanah Longsor | 1 |

## 4. Waktu

`published_time` memakai ISO 8601 dan mempertahankan offset sumber. Nilai mentah tetap tersedia di `published_time_mentah`.

| Format sumber | Jumlah |
|---|---:|
| rfc2822 | 727 |
| iso8601 | 40 |
| indonesia | 20 |

| Zona sumber | Jumlah |
|---|---:|
| +07:00 | 668 |
| +00:00 | 116 |
| +08:00 | 3 |

`event_time` tidak diisi dari `published_time`. Jenis waktu kejadian:

| event_time_jenis | Jumlah |
|---|---:|
| tidak_diketahui | 723 |
| aktual | 42 |
| tanggal_saja | 13 |
| prediksi_nowcast | 9 |

## 5. Lokasi

Lokasi kejadian dan lokasi yang hanya disebut berita dipisahkan. Koordinat tetap berstatus belum terverifikasi.

| lokasi_hubungan | Jumlah |
|---|---:|
| tidak_diketahui | 679 |
| rujukan_admin_belum_verifikasi | 59 |
| titik_kejadian_terindikasi | 40 |
| domain_disebut_dalam_judul | 9 |

| lokasi_presisi | Jumlah |
|---|---:|
| tidak_diketahui | 679 |
| provinsi | 40 |
| titik_terindikasi | 40 |
| kabupaten_kota | 19 |
| domain_negara | 9 |

## 6. Duplikat

| Pemeriksaan | Baris ditandai |
|---|---:|
| Judul sama | 10 |
| Isi berita identik | 4 |
| URL sama | 0 |

Kelompok duplikat:

| Kelompok | Anggota |
|---|---|
| isi:42-43 | 42,43 |
| isi:44-45 | 44,45 |
| judul:220,642 | 220,642 |
| judul:39-46 | 39,40,41,42,43,44,45,46 |

Tidak ada baris yang dihapus. Judul sama dengan event_id GDACS berbeda atau sumber/URL berbeda tetap dipertahankan sebagai kejadian/berita terpisah.

## 7. Validasi

| Pemeriksaan | Hasil |
|---|---:|
| Baris | 787 |
| URL unik | 787 |
| Field wajib kosong | 0 |
| Error validasi | 0 |
| Kategori final valid | 9 nilai kontrak; 5 terpakai |
| Event time berjenis | 4 nilai |

## 8. Batas dan status

- `Lainnya` belum terklasifikasi: **632** baris.
- Kategori di luar 8 target: **102** baris; semuanya ditandai.
- `event_time` tidak diketahui/perlu review: **723** baris.
- Tanpa lokasi kejadian: **679** baris.
- Koordinat belum terverifikasi: **40** baris.
- Lokasi administratif belum terverifikasi: **88** baris.
- Baris fokus `perlu_verifikasi`: **7** baris.
- Lima alamat tanpa provinsi tidak dipakai sebagai bukti lokasi kejadian.
- Tidak ada verifikasi online, geocoding, atau scraping baru.
- Dataset ini bukan data tervalidasi; gunakan status 'terindikasi' atau 'belum diverifikasi'.

## 9. Pengujian

- Perintah: `python -m unittest -q test_stage5_quality test_stage5_2_quality test_stage5_4_event_time test_final_release_geohazard`
- Hasil: **46 test lulus** (29 test lama + 17 test final release).
