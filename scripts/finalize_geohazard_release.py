#!/usr/bin/env python3
"""Final release GeoHazard News Locator: kontrak, waktu, lokasi, dan duplikat."""

import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "data" / "geohazard_news_located_20261101T144531Z_stage5_4.csv"
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"
EXPECTED_SHA256 = (
    "bb1bc6d4343d2b8bb1982677d09a1e6f4183dc5032f1845335299bc38c5c20db"
)

TARGET_CATEGORIES = {
    "Gunungapi",
    "Gempabumi",
    "Tsunami",
    "Gerakan Tanah/Tanah Longsor",
    "Likuefaksi",
    "Abrasi dan Akresi",
    "Penurunan Muka Tanah",
    "Semburan Gas dan Lumpur",
}
FINAL_CATEGORIES = TARGET_CATEGORIES | {"Lainnya"}
OUT_OF_SCOPE_CATEGORIES = {"Cuaca Ekstrem", "Kebakaran Hutan dan Lahan"}

NEW_FIELDS = [
    "kategori_sebelum_final",
    "kategori_final_aksi",
    "published_time_mentah",
    "published_time_zona",
    "published_time_format",
    "event_time_jenis",
    "event_time_zona",
    "lokasi_hubungan",
    "lokasi_presisi",
    "duplikat_isi",
    "duplikat_kelompok",
    "catatan_final",
]

REQUIRED_FIELDS = [
    "judul",
    "published_time",
    "sumber",
    "kategori",
    "url",
    "isi_berita",
    "kategori_sebelum_final",
    "kategori_final_aksi",
    "published_time_mentah",
    "published_time_zona",
    "published_time_format",
    "event_time_jenis",
    "lokasi_hubungan",
    "lokasi_presisi",
    "duplikat_judul",
    "duplikat_url",
    "duplikat_isi",
]

BULAN = {
    "jan": 1,
    "januari": 1,
    "feb": 2,
    "februari": 2,
    "mar": 3,
    "maret": 3,
    "apr": 4,
    "april": 4,
    "mei": 5,
    "may": 5,
    "jun": 6,
    "juni": 6,
    "june": 6,
    "jul": 7,
    "juli": 7,
    "july": 7,
    "agu": 8,
    "agt": 8,
    "aug": 8,
    "agustus": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "okt": 10,
    "oct": 10,
    "oktober": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "des": 12,
    "dec": 12,
    "desember": 12,
    "december": 12,
}

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
INDONESIA_RE = re.compile(r"^\d{1,2}\s+[A-Za-z]+\s+\d{4}\b")
OFFSET_RE = re.compile(r"([+-]\d{2}:\d{2})$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _zona_offset(nilai):
    if nilai.tzinfo is None:
        return ""
    total_menit = int(nilai.utcoffset().total_seconds() // 60)
    tanda = "+" if total_menit >= 0 else "-"
    total_menit = abs(total_menit)
    return f"{tanda}{total_menit // 60:02d}:{total_menit % 60:02d}"


def _parse_indonesia(teks):
    bagian = teks.split()
    if len(bagian) < 5:
        raise ValueError("format tanggal Indonesia tidak lengkap")
    hari = int(bagian[0])
    bulan = BULAN.get(bagian[1].lower().rstrip("."))
    if bulan is None:
        raise ValueError("nama bulan Indonesia tidak dikenal")
    tahun = int(bagian[2])
    jam = bagian[3]
    zona = bagian[4].upper()
    if jam.count(":") not in {1, 2}:
        raise ValueError("format jam Indonesia tidak dikenal")
    komponen = [int(x) for x in jam.split(":")]
    if len(komponen) == 2:
        komponen.append(0)
    if zona == "GMT":
        offset = timezone.utc
    else:
        tanda = 1 if zona.startswith("+") else -1
        if len(zona) != 5 or not zona[1:].isdigit():
            raise ValueError("format zona Indonesia tidak dikenal")
        menit = int(zona[1:3]) * 60 + int(zona[3:5])
        offset = timezone(timedelta(minutes=tanda * menit))
    return datetime(
        tahun,
        bulan,
        hari,
        komponen[0],
        komponen[1],
        komponen[2],
        tzinfo=offset,
    )


def parse_published_time(teks):
    nilai = str(teks or "").strip()
    if not nilai:
        raise ValueError("published_time kosong")

    if ISO_RE.match(nilai):
        nilai_iso = nilai[:-1] + "+00:00" if nilai.endswith("Z") else nilai
        parsed = datetime.fromisoformat(nilai_iso)
        if parsed.tzinfo is None:
            raise ValueError("published_time ISO tanpa zona")
        return "iso8601", parsed

    if INDONESIA_RE.match(nilai):
        parsed = _parse_indonesia(nilai)
        return "indonesia", parsed

    parsed = parsedate_to_datetime(nilai)
    if parsed is None:
        raise ValueError("published_time tidak dapat diparse")
    if parsed.tzinfo is None:
        raise ValueError("published_time RFC tanpa zona")
    return "rfc2822", parsed


def _event_time_zona(nilai):
    if not nilai or "T" not in nilai:
        return ""
    cocok = OFFSET_RE.search(nilai)
    return cocok.group(1) if cocok else ""


def event_time_jenis(row):
    status = str(row.get("event_time_status") or "")
    basis = str(row.get("event_time_basis") or "")
    if status == "terekstrak":
        if basis == "bmkg_nowcast":
            return "prediksi_nowcast"
        return "aktual"
    if status == "tanggal_saja":
        return "tanggal_saja"
    return "tidak_diketahui"


def kategori_final(row):
    asal = str(row.get("kategori") or "").strip()
    if asal in TARGET_CATEGORIES:
        return asal, "dipertahankan", ""
    if asal == "Lainnya":
        return "Lainnya", "dipertahankan", ""
    if asal in OUT_OF_SCOPE_CATEGORIES:
        return (
            "Lainnya",
            "dipetakan_ke_lainnya",
            f"kategori '{asal}' di luar 8 kategori target; dipetakan ke Lainnya",
        )
    return (
        "Lainnya",
        "dipetakan_ke_lainnya",
        f"kategori '{asal or 'kosong'}' tidak dikenal; dipetakan ke Lainnya",
    )


def lokasi_hubungan(row):
    basis = str(row.get("domain_lokasi_basis") or "")
    if basis == "koordinat":
        return "titik_kejadian_terindikasi"
    if basis == "provinsi":
        return "rujukan_admin_belum_verifikasi"
    if basis == "judul":
        return "domain_disebut_dalam_judul"
    return "tidak_diketahui"


def lokasi_presisi(row):
    basis = str(row.get("domain_lokasi_basis") or "")
    if basis == "koordinat":
        return "titik_terindikasi"
    if basis == "provinsi":
        if str(row.get("kabupaten_kota") or "").strip():
            return "kabupaten_kota"
        return "provinsi"
    if basis == "judul":
        return "domain_negara"
    return "tidak_diketahui"


def _grup_duplikat(rows, field):
    grup = defaultdict(list)
    for nomor, row in enumerate(rows, start=1):
        nilai = str(row.get(field) or "")
        if nilai:
            grup[nilai].append(nomor)
    return [nomor for nomor in grup.values() if len(nomor) > 1]


def _label_grup(prefix, nomor):
    if nomor == list(range(nomor[0], nomor[-1] + 1)):
        isi = f"{nomor[0]}-{nomor[-1]}"
    else:
        isi = ",".join(str(x) for x in nomor)
    return f"{prefix}:{isi}"


def _tambah(catatan, teks):
    if teks and teks not in catatan:
        catatan.append(teks)


def finalisasi_baris(row, nomor, peta_duplikat):
    baru = dict(row)
    catatan = []

    asal = str(row.get("kategori") or "").strip()
    final, aksi, alasan = kategori_final(row)
    baru["kategori_sebelum_final"] = asal
    baru["kategori"] = final
    baru["kategori_final_aksi"] = aksi
    if alasan:
        _tambah(catatan, alasan)

    mentah = str(row.get("published_time") or "")
    format_waktu, waktu = parse_published_time(mentah)
    baru["published_time_mentah"] = mentah
    baru["published_time"] = waktu.isoformat(timespec="seconds")
    baru["published_time_zona"] = _zona_offset(waktu)
    baru["published_time_format"] = format_waktu

    baru["event_time_jenis"] = event_time_jenis(row)
    baru["event_time_zona"] = _event_time_zona(
        str(row.get("event_time") or "")
    )

    hubungan = lokasi_hubungan(row)
    presisi = lokasi_presisi(row)
    baru["lokasi_hubungan"] = hubungan
    baru["lokasi_presisi"] = presisi
    if hubungan == "domain_disebut_dalam_judul":
        _tambah(
            catatan,
            "domain Indonesia hanya disebut di judul; bukan bukti lokasi kejadian",
        )

    label = peta_duplikat.get(nomor, [])
    baru["duplikat_judul"] = (
        "ya" if any(x.startswith("judul:") for x in label) else "tidak"
    )
    baru["duplikat_isi"] = (
        "ya" if any(x.startswith("isi:") for x in label) else "tidak"
    )
    baru["duplikat_url"] = (
        "ya" if any(x.startswith("url:") for x in label) else "tidak"
    )
    baru["duplikat_kelompok"] = ";".join(label)

    if any(x.startswith("judul:39-46") for x in label):
        _tambah(
            catatan,
            "judul sama; event_id GDACS berbeda; bukan duplikat kejadian",
        )
    if any(x.startswith("judul:220,642") for x in label):
        _tambah(
            catatan,
            "judul sama; sumber dan URL berbeda; sindikasi perlu tinjau",
        )
    if any(x.startswith("isi:") for x in label):
        _tambah(
            catatan,
            "isi berita identik; jangan hapus tanpa cek event_id dan sumber",
        )

    if (
        nomor == 216
        and str(row.get("desa_kelurahan") or "").strip().lower() == "banjir"
        and str(row.get("provinsi") or "").strip() == "Aceh"
    ):
        baru["desa_kelurahan"] = ""
        _tambah(
            catatan,
            "desa_kelurahan 'Banjir' dikosongkan: kata umum, bukan nama desa",
        )

    if str(row.get("alamat_detail") or "").strip() and not str(
        row.get("provinsi") or ""
    ).strip():
        _tambah(
            catatan,
            "alamat_detail tanpa provinsi; tidak dipakai sebagai lokasi kejadian",
        )

    baru["catatan_final"] = "; ".join(catatan)
    return baru


def bangun_baris(rows, nomor_awal=1):
    peta = defaultdict(list)
    for prefix, field in (
        ("judul", "judul"),
        ("isi", "isi_berita"),
        ("url", "url"),
    ):
        grup = defaultdict(list)
        for offset, row in enumerate(rows):
            nilai = str(row.get(field) or "")
            if nilai:
                grup[nilai].append(nomor_awal + offset)
        for nomor in grup.values():
            if len(nomor) > 1:
                label = _label_grup(prefix, nomor)
                for i in nomor:
                    peta[i].append(label)
    return [
        finalisasi_baris(row, nomor_awal + offset, peta)
        for offset, row in enumerate(rows)
    ]


def validasi(rows, jumlah_diharapkan=None):
    errors = []
    if jumlah_diharapkan is not None and len(rows) != jumlah_diharapkan:
        errors.append(f"jumlah baris {len(rows)} != {jumlah_diharapkan}")

    urls = Counter(str(r.get("url") or "") for r in rows)
    for url, jumlah in urls.items():
        if jumlah > 1:
            errors.append(f"URL duplikat: {url}")
        if not url:
            errors.append("URL kosong")
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"URL tidak valid: {url}")

    for nomor, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if not str(row.get(field) or "").strip():
                errors.append(f"baris {nomor}: field wajib kosong: {field}")

        kategori = str(row.get("kategori") or "")
        status = str(row.get("status_cakupan") or "")
        if kategori not in FINAL_CATEGORIES:
            errors.append(f"baris {nomor}: kategori final tidak dikenal: {kategori}")
        if kategori in TARGET_CATEGORIES and status != "dalam_8_kategori":
            errors.append(f"baris {nomor}: kategori target dengan status {status}")
        if kategori == "Lainnya" and status not in {
            "tidak_terklasifikasi",
            "di_luar_8_kategori",
        }:
            errors.append(f"baris {nomor}: Lainnya dengan status {status}")

        asal = str(row.get("kategori_sebelum_final") or "")
        aksi = str(row.get("kategori_final_aksi") or "")
        if asal in TARGET_CATEGORIES:
            if aksi != "dipertahankan" or kategori != asal:
                errors.append(f"baris {nomor}: kategori target berubah tanpa alasan")
        elif asal == "Lainnya":
            if aksi != "dipertahankan" or kategori != "Lainnya":
                errors.append(f"baris {nomor}: Lainnya berubah tanpa alasan")
        else:
            if aksi != "dipetakan_ke_lainnya" or kategori != "Lainnya":
                errors.append(f"baris {nomor}: out-of-scope tidak dipetakan")

        try:
            format_waktu, waktu = parse_published_time(row["published_time_mentah"])
        except (ValueError, TypeError) as exc:
            errors.append(f"baris {nomor}: published_time mentah tidak valid: {exc}")
            format_waktu = ""
            waktu = None
        if format_waktu != row.get("published_time_format"):
            errors.append(f"baris {nomor}: format published_time tidak konsisten")
        if waktu is not None:
            if row.get("published_time") != waktu.isoformat(timespec="seconds"):
                errors.append(f"baris {nomor}: published_time tidak ternormalisasi")
            if row.get("published_time_zona") != _zona_offset(waktu):
                errors.append(f"baris {nomor}: zona published_time tidak konsisten")

        jenis = str(row.get("event_time_jenis") or "")
        status_event = str(row.get("event_time_status") or "")
        event_time = str(row.get("event_time") or "")
        if jenis not in {
            "aktual",
            "prediksi_nowcast",
            "tanggal_saja",
            "tidak_diketahui",
        }:
            errors.append(f"baris {nomor}: event_time_jenis tidak dikenal: {jenis}")
        if status_event == "terekstrak":
            if jenis not in {"aktual", "prediksi_nowcast"}:
                errors.append(f"baris {nomor}: status terekstrak dengan jenis {jenis}")
            if "T" not in event_time:
                errors.append(f"baris {nomor}: event_time terekstrak tanpa jam")
        elif status_event == "tanggal_saja":
            if jenis != "tanggal_saja" or "T" in event_time:
                errors.append(f"baris {nomor}: tanggal_saja tidak konsisten")
        else:
            if jenis != "tidak_diketahui" or event_time:
                errors.append(f"baris {nomor}: event_time tidak diketahui tidak konsisten")
        if row.get("event_time_zona") != _event_time_zona(event_time):
            errors.append(f"baris {nomor}: zona event_time tidak konsisten")

        basis = str(row.get("domain_lokasi_basis") or "")
        hubungan = str(row.get("lokasi_hubungan") or "")
        presisi = str(row.get("lokasi_presisi") or "")
        diharapkan_hubungan = {
            "koordinat": "titik_kejadian_terindikasi",
            "provinsi": "rujukan_admin_belum_verifikasi",
            "judul": "domain_disebut_dalam_judul",
        }.get(basis, "tidak_diketahui")
        if hubungan != diharapkan_hubungan:
            errors.append(f"baris {nomor}: lokasi_hubungan tidak konsisten")
        if basis == "koordinat":
            diharapkan_presisi = "titik_terindikasi"
        elif basis == "provinsi":
            diharapkan_presisi = (
                "kabupaten_kota"
                if str(row.get("kabupaten_kota") or "").strip()
                else "provinsi"
            )
        elif basis == "judul":
            diharapkan_presisi = "domain_negara"
        else:
            diharapkan_presisi = "tidak_diketahui"
        if presisi != diharapkan_presisi:
            errors.append(f"baris {nomor}: lokasi_presisi tidak konsisten")

        lat = str(row.get("latitude") or "").strip()
        lon = str(row.get("longitude") or "").strip()
        if bool(lat) != bool(lon):
            errors.append(f"baris {nomor}: latitude/longitude tidak lengkap")
        elif lat and lon:
            try:
                if not -90 <= float(lat) <= 90:
                    errors.append(f"baris {nomor}: latitude di luar rentang")
                if not -180 <= float(lon) <= 180:
                    errors.append(f"baris {nomor}: longitude di luar rentang")
            except ValueError:
                errors.append(f"baris {nomor}: koordinat bukan angka")

        label = str(row.get("duplikat_kelompok") or "")
        for field, prefix in (
            ("duplikat_judul", "judul:"),
            ("duplikat_isi", "isi:"),
            ("duplikat_url", "url:"),
        ):
            if str(row.get(field) or "") not in {"ya", "tidak"}:
                errors.append(f"baris {nomor}: nilai {field} tidak dikenal")
            if (str(row.get(field) or "") == "ya") != (prefix in label):
                errors.append(f"baris {nomor}: {field} tidak konsisten")

    return {
        "errors": errors,
        "jumlah": len(rows),
        "url_unik": len(urls),
        "kolom_kosong": sum(
            1 for r in rows for f in REQUIRED_FIELDS if not str(r.get(f) or "").strip()
        ),
    }


def tulis_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _hitung(rows, field):
    return Counter(str(r.get(field) or "") for r in rows)


def _tabel(counter, judul="Nilai"):
    baris = [f"| {judul} | Jumlah |", "|---|---:|"]
    for nilai, jumlah in counter.most_common():
        baris.append(f"| {nilai or '(kosong)'} | {jumlah} |")
    return baris


def tulis_laporan(path, meta):
    rows = meta["baru"]
    baris = [
        "# Final Release GeoHazard News Locator",
        "",
        f"- Tanggal proses: {meta['waktu']}",
        f"- Sumber: `{meta['sumber']}`",
        f"- SHA-256 sumber sebelum: `{meta['hash_before']}`",
        f"- SHA-256 sumber sesudah: `{meta['hash_after']}`",
        f"- Sumber tidak berubah: **{meta['hash_before'] == meta['hash_after']}**",
        f"- Keluaran: `{meta['output']}`",
        f"- SHA-256 keluaran: `{meta['hash_output']}`",
        "- Mode: non-destruktif; 787 baris dipertahankan; tidak ada penghapusan baris.",
        "",
        "## 1. Ringkasan",
        "",
        f"- Baris: **{meta['jumlah_sumber']} -> {len(rows)}**.",
        f"- Kolom: **{meta['kolom_sumber']} -> {len(meta['fieldnames'])}**.",
        f"- Field baru: **{len(NEW_FIELDS)}**.",
        f"- `published_time` diproses: **{meta['published_total']}** baris; "
        f"**{meta['published_berubah']}** berubah teks; "
        f"**{meta['published_sudah_kanonik']}** sudah ISO.",
        f"- Kategori dipetakan ke `Lainnya`: **{meta['kategori_dipetakan']}** baris.",
        f"- Koreksi `desa_kelurahan`: **{meta['desa_dikoreksi']}** sel.",
        f"- `event_time` dipertahankan: **{meta['event_time_terisi']}** baris terisi.",
        f"- Duplikat judul/isi/URL: **{meta['dup_judul']} / {meta['dup_isi']} / {meta['dup_url']}** baris.",
        "",
        "## 2. Perubahan yang disengaja",
        "",
        "| Perubahan | Baris/sel | Alasan |",
        "|---|---:|---|",
        f"| Normalisasi `published_time` | {meta['published_berubah']} berubah / {meta['published_total']} diproses | ISO 8601; nilai mentah dan zona sumber disimpan |",
        f"| `kategori` out-of-scope -> `Lainnya` | {meta['kategori_dipetakan']} | Kontrak final 8 kategori target + `Lainnya`; nilai asal disimpan |",
        f"| `desa_kelurahan` generik dikosongkan | {meta['desa_dikoreksi']} | Bukti audit: 'Banjir' adalah kata umum, bukan nama desa |",
        "",
        "Kolom lama lain yang berubah di luar tiga perubahan di atas: "
        f"**{meta['kolom_lain_berubah']} sel**.",
        "",
        "## 3. Kontrak kategori",
        "",
        "Kategori final hanya berisi 8 kategori target + `Lainnya`.",
        "",
        "| Kategori final | Jumlah |",
        "|---|---:|",
    ]
    for kategori in sorted(FINAL_CATEGORIES):
        baris.append(f"| {kategori} | {meta['kategori_final'][kategori]} |")

    baris += [
        "",
        "Kategori di luar cakupan tidak dipaksa menjadi kategori target. "
        "Nilai asal tetap tersimpan di `kategori_sebelum_final`, `kategori_asal`, "
        "dan `status_cakupan=di_luar_8_kategori`.",
        "",
        "| Kategori sebelum final | Jumlah |",
        "|---|---:|",
    ]
    for kategori, jumlah in meta["kategori_sebelum"].most_common():
        baris.append(f"| {kategori} | {jumlah} |")

    baris += [
        "",
        "## 4. Waktu",
        "",
        "`published_time` memakai ISO 8601 dan mempertahankan offset sumber. "
        "Nilai mentah tetap tersedia di `published_time_mentah`.",
        "",
        "| Format sumber | Jumlah |",
        "|---|---:|",
    ]
    for fmt, jumlah in meta["published_format"].most_common():
        baris.append(f"| {fmt} | {jumlah} |")
    baris += ["", "| Zona sumber | Jumlah |", "|---|---:|"]
    for zona, jumlah in meta["published_zona"].most_common():
        baris.append(f"| {zona or '(kosong)'} | {jumlah} |")

    baris += [
        "",
        "`event_time` tidak diisi dari `published_time`. Jenis waktu kejadian:",
        "",
        "| event_time_jenis | Jumlah |",
        "|---|---:|",
    ]
    for jenis, jumlah in meta["event_jenis"].most_common():
        baris.append(f"| {jenis} | {jumlah} |")

    baris += [
        "",
        "## 5. Lokasi",
        "",
        "Lokasi kejadian dan lokasi yang hanya disebut berita dipisahkan. "
        "Koordinat tetap berstatus belum terverifikasi.",
        "",
        "| lokasi_hubungan | Jumlah |",
        "|---|---:|",
    ]
    for nilai, jumlah in meta["lokasi_hubungan"].most_common():
        baris.append(f"| {nilai} | {jumlah} |")
    baris += ["", "| lokasi_presisi | Jumlah |", "|---|---:|"]
    for nilai, jumlah in meta["lokasi_presisi"].most_common():
        baris.append(f"| {nilai} | {jumlah} |")

    baris += [
        "",
        "## 6. Duplikat",
        "",
        "| Pemeriksaan | Baris ditandai |",
        "|---|---:|",
        f"| Judul sama | {meta['dup_judul']} |",
        f"| Isi berita identik | {meta['dup_isi']} |",
        f"| URL sama | {meta['dup_url']} |",
        "",
        "Kelompok duplikat:",
        "",
        "| Kelompok | Anggota |",
        "|---|---|",
    ]
    for label, anggota in meta["dup_grup"].items():
        baris.append(f"| {label} | {anggota} |")
    baris += [
        "",
        "Tidak ada baris yang dihapus. Judul sama dengan event_id GDACS berbeda "
        "atau sumber/URL berbeda tetap dipertahankan sebagai kejadian/berita terpisah.",
        "",
        "## 7. Validasi",
        "",
        "| Pemeriksaan | Hasil |",
        "|---|---:|",
        f"| Baris | {meta['validasi']['jumlah']} |",
        f"| URL unik | {meta['validasi']['url_unik']} |",
        f"| Field wajib kosong | {meta['validasi']['kolom_kosong']} |",
        f"| Error validasi | {len(meta['validasi']['errors'])} |",
        f"| Kategori final valid | 9 nilai kontrak; {len(meta['kategori_final'])} terpakai |",
        f"| Event time berjenis | {len(meta['event_jenis'])} nilai |",
        "",
        "## 8. Batas dan status",
        "",
        f"- `Lainnya` belum terklasifikasi: **{meta['status_cakupan'].get('tidak_terklasifikasi', 0)}** baris.",
        f"- Kategori di luar 8 target: **{meta['status_cakupan'].get('di_luar_8_kategori', 0)}** baris; semuanya ditandai.",
        f"- `event_time` tidak diketahui/perlu review: **{meta['event_jenis'].get('tidak_diketahui', 0)}** baris.",
        f"- Tanpa lokasi kejadian: **{meta['lokasi_hubungan'].get('tidak_diketahui', 0)}** baris.",
        f"- Koordinat belum terverifikasi: **{meta['koordinat_belum']}** baris.",
        f"- Lokasi administratif belum terverifikasi: **{meta['admin_belum']}** baris.",
        f"- Baris fokus `perlu_verifikasi`: **{meta['fokus']}** baris.",
        "- Lima alamat tanpa provinsi tidak dipakai sebagai bukti lokasi kejadian.",
        "- Tidak ada verifikasi online, geocoding, atau scraping baru.",
        "- Dataset ini bukan data tervalidasi; gunakan status 'terindikasi' atau 'belum diverifikasi'.",
        "",
        "## 9. Pengujian",
        "",
        "- Perintah: `python -m unittest -q test_stage5_quality test_stage5_2_quality test_stage5_4_event_time test_final_release_geohazard`",
        f"- Hasil: {meta.get('test_note', 'lihat hasil eksekusi test terarah')}.",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(baris))


def main():
    if not SRC.exists():
        raise SystemExit(f"Sumber tidak ditemukan: {SRC}")
    hash_before = sha256(SRC)
    if hash_before != EXPECTED_SHA256:
        raise SystemExit("Hash sumber Stage 5.4 tidak sesuai.")

    with open(SRC, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    baru = bangun_baris(rows)
    fieldnames_output = list(fieldnames)
    for field in NEW_FIELDS:
        if field not in fieldnames_output:
            fieldnames_output.append(field)

    intended = {"published_time", "kategori", "desa_kelurahan"}
    kolom_lain_berubah = 0
    for lama, hasil in zip(rows, baru):
        for field in fieldnames:
            if field in intended:
                continue
            if lama.get(field) != hasil.get(field):
                kolom_lain_berubah += 1

    hasil_validasi = validasi(baru, jumlah_diharapkan=len(rows))
    if hasil_validasi["errors"]:
        contoh = "\n".join(hasil_validasi["errors"][:20])
        raise SystemExit(f"Validasi gagal ({len(hasil_validasi['errors'])} error):\n{contoh}")

    hash_after = sha256(SRC)
    if hash_before != hash_after:
        raise SystemExit("Sumber berubah saat proses.")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = DATA_DIR / f"geohazard_news_final_{ts}.csv"
    nomor = 2
    while output.exists():
        output = DATA_DIR / f"geohazard_news_final_{ts}_{nomor}.csv"
        nomor += 1
    tulis_csv(output, baru, fieldnames_output)
    hash_output = sha256(output)

    grup = defaultdict(list)
    for prefix, field in (("judul", "judul"), ("isi", "isi_berita"), ("url", "url")):
        for anggota in _grup_duplikat(rows, field):
            grup[_label_grup(prefix, anggota)] = anggota
    dup_grup = {
        label: ",".join(str(x) for x in anggota)
        for label, anggota in sorted(grup.items())
    }

    kategori_sebelum = _hitung(rows, "kategori")
    kategori_final = Counter(str(r.get("kategori") or "") for r in baru)
    published_format = _hitung(baru, "published_time_format")
    published_zona = _hitung(baru, "published_time_zona")
    event_jenis = _hitung(baru, "event_time_jenis")
    lokasi_hub = _hitung(baru, "lokasi_hubungan")
    lokasi_pres = _hitung(baru, "lokasi_presisi")
    status_cakupan = _hitung(baru, "status_cakupan")

    meta = {
        "waktu": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "sumber": SRC,
        "output": output,
        "hash_before": hash_before,
        "hash_after": hash_after,
        "hash_output": hash_output,
        "jumlah_sumber": len(rows),
        "kolom_sumber": len(fieldnames),
        "fieldnames": fieldnames_output,
        "baru": baru,
        "published_total": len(baru),
        "published_berubah": sum(
            1 for lama, hasil in zip(rows, baru)
            if lama.get("published_time") != hasil.get("published_time")
        ),
        "published_sudah_kanonik": sum(
            1 for lama, hasil in zip(rows, baru)
            if lama.get("published_time") == hasil.get("published_time")
        ),
        "kategori_dipetakan": sum(
            1 for r in baru if r.get("kategori_final_aksi") == "dipetakan_ke_lainnya"
        ),
        "desa_dikoreksi": sum(
            1 for lama, hasil in zip(rows, baru)
            if lama.get("desa_kelurahan") != hasil.get("desa_kelurahan")
        ),
        "event_time_terisi": sum(1 for r in baru if r.get("event_time")),
        "kolom_lain_berubah": kolom_lain_berubah,
        "kategori_sebelum": kategori_sebelum,
        "kategori_final": kategori_final,
        "published_format": published_format,
        "published_zona": published_zona,
        "event_jenis": event_jenis,
        "lokasi_hubungan": lokasi_hub,
        "lokasi_presisi": lokasi_pres,
        "status_cakupan": status_cakupan,
        "dup_judul": sum(1 for r in baru if r.get("duplikat_judul") == "ya"),
        "dup_isi": sum(1 for r in baru if r.get("duplikat_isi") == "ya"),
        "dup_url": sum(1 for r in baru if r.get("duplikat_url") == "ya"),
        "dup_grup": dup_grup,
        "koordinat_belum": sum(
            1 for r in baru if r.get("koordinat_verifikasi") == "belum_diverifikasi"
        ),
        "admin_belum": sum(
            1 for r in baru
            if r.get("lokasi_verifikasi") in {"belum_diverifikasi", "perlu_verifikasi"}
        ),
        "fokus": sum(
            1 for r in baru if r.get("lokasi_verifikasi") == "perlu_verifikasi"
        ),
        "validasi": hasil_validasi,
        "test_note": "lihat hasil eksekusi test terarah",
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "final_release_geohazard.md"
    nomor = 2
    while report.exists():
        report = REPORT_DIR / f"final_release_geohazard_{nomor}.md"
        nomor += 1
    tulis_laporan(report, meta)

    print(f"Sumber         : {SRC}")
    print(f"Hash sebelum   : {hash_before}")
    print(f"Hash sesudah   : {hash_after}")
    print(f"Hash keluaran  : {hash_output}")
    print(f"Baris          : {len(rows)} -> {len(baru)}")
    print(f"Kolom          : {len(fieldnames)} -> {len(fieldnames_output)}")
    print(f"Kategori map   : {meta['kategori_dipetakan']}")
    print(f"Desa dikoreksi : {meta['desa_dikoreksi']}")
    print(f"Event terisi   : {meta['event_time_terisi']}")
    print(f"Error validasi : {len(hasil_validasi['errors'])}")
    print(f"Output         : {output}")
    print(f"Laporan        : {report}")


if __name__ == "__main__":
    main()
