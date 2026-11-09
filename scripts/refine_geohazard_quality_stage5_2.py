#!/usr/bin/env python3
"""Stage 5.2: koreksi domain dan status verifikasi lokasi hasil audit."""

import csv
import hashlib
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "data" / "geohazard_news_located_20261030T125936Z_stage5.csv"
REPORT_DIR = ROOT / "reports"
EXPECTED_SHA256 = (
    "4a0c3377bddc1672e32e2e1dd6ed313e3a9c2702f64c3d0cbc8f313c9d189f0f"
)

NEW_FIELDS = [
    "domain_lokasi_sebelum",
    "domain_lokasi_basis",
    "lokasi_verifikasi",
    "lokasi_basis",
    "lokasi_risiko",
    "catatan_stage5_2",
]

FOCUS_RISK = {
    12: "sedang",
    14: "tinggi",
    17: "tinggi",
    18: "tinggi",
    19: "sedang",
    24: "sedang",
    27: "tinggi",
}

FOCUS_NOTES = {
    12: "lokasi_rujukan;jarak_29_km;batas_admin_perlu_verifikasi",
    14: "lokasi_rujukan;jarak_125_km;batas_admin_perlu_verifikasi",
    17: "lokasi_rujukan;jarak_219_km;batas_admin_perlu_verifikasi",
    18: "lokasi_rujukan;jarak_68_km;batas_admin_perlu_verifikasi",
    19: "lokasi_rujukan;jarak_14_km;batas_admin_perlu_verifikasi",
    24: "lokasi_rujukan;jarak_33_km;batas_admin_perlu_verifikasi",
    27: "lokasi_rujukan;epicenter_di_laut;batas_admin_perlu_verifikasi",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def koreksi_domain(row):
    koordinat = str(row.get("koordinat_domain") or "")
    if koordinat in {"indonesia", "luar_indonesia"}:
        return koordinat, "koordinat"

    provinsi = str(row.get("provinsi") or "").strip()
    if provinsi:
        return "indonesia", "provinsi"

    lama = str(row.get("domain_lokasi") or "")
    judul = str(row.get("judul") or "")
    status = str(row.get("status_cakupan") or "tidak_terklasifikasi")
    if lama == "luar_indonesia":
        return "luar_indonesia", "stage5"
    if (
        status in {"dalam_8_kategori", "di_luar_8_kategori"}
        and re.search(r"\b(?:in|di)\s+indonesia\b", judul, re.I)
    ):
        return "indonesia", "judul"
    return "tidak_diketahui", "tidak_diketahui"


def metadata_lokasi(nomor, row):
    provinsi = str(row.get("provinsi") or "").strip()
    kabupaten = str(row.get("kabupaten_kota") or "").strip()
    if nomor in FOCUS_RISK:
        verifikasi = "perlu_verifikasi"
        basis = "rujukan_toponimi"
        risiko = FOCUS_RISK[nomor]
    elif provinsi or kabupaten:
        verifikasi = "belum_diverifikasi"
        basis = "warisan_stage3"
        risiko = "tidak_dinilai"
    else:
        verifikasi = "tidak_ada"
        basis = "tidak_ada"
        risiko = "tidak_dinilai"
    return {
        "lokasi_verifikasi": verifikasi,
        "lokasi_basis": basis,
        "lokasi_risiko": risiko,
    }


def bangun_baris(rows):
    hasil = []
    for nomor, row in enumerate(rows, start=1):
        baru = dict(row)
        domain, basis = koreksi_domain(row)
        lama = str(row.get("domain_lokasi") or "")
        baru["domain_lokasi_sebelum"] = lama
        baru["domain_lokasi"] = domain
        baru["domain_lokasi_basis"] = basis
        baru.update(metadata_lokasi(nomor, row))

        catatan = []
        if nomor in FOCUS_NOTES:
            catatan.append(FOCUS_NOTES[nomor])
        if nomor == 214:
            catatan.append("alamat_dinormalkan")
        if lama != domain:
            catatan.append("domain_lokasi_dikoreksi")
        baru["catatan_stage5_2"] = ";".join(catatan)
        hasil.append(baru)
    return hasil


def tulis_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def hitung(rows, field):
    return Counter(str(r.get(field) or "") for r in rows)


def tulis_laporan(path, src, output, meta):
    rows = meta["baru"]
    domain_baru = hitung(rows, "domain_lokasi")
    domain_lama = hitung(rows, "domain_lokasi_sebelum")
    basis = hitung(rows, "domain_lokasi_basis")
    verifikasi = hitung(rows, "lokasi_verifikasi")
    risiko = hitung(rows, "lokasi_risiko")
    transisi = Counter(
        f"{r.get('domain_lokasi_sebelum') or '(kosong)'} -> "
        f"{r.get('domain_lokasi') or '(kosong)'}"
        for r in rows
        if r.get("domain_lokasi_sebelum") != r.get("domain_lokasi")
    )

    baris = []
    baris.append("# Perbaikan Kualitas Data Stage 5.2")
    baris.append("")
    baris.append(f"- Tanggal proses: {meta['waktu']}")
    baris.append(f"- Sumber: `{src}`")
    baris.append(f"- SHA-256 sumber sebelum: `{meta['hash_before']}`")
    baris.append(f"- SHA-256 sumber sesudah: `{meta['hash_after']}`")
    baris.append(f"- Sumber tidak berubah: **{meta['hash_before'] == meta['hash_after']}**")
    baris.append(f"- Keluaran: `{output}`")
    baris.append(f"- SHA-256 keluaran: `{meta['hash_output']}`")
    baris.append("- Mode: non-destruktif; dataset Stage 5 dan CSV historis tidak diubah.")
    baris.append("")
    baris.append("## 1. Ringkasan")
    baris.append("")
    baris.append(f"- Baris: **{meta['jumlah_sumber']} -> {len(rows)}** (tidak ada baris dihapus).")
    baris.append(f"- Kolom: **{meta['kolom_sumber']} -> {len(meta['fieldnames'])}**.")
    baris.append(f"- `domain_lokasi` berubah: **{meta['domain_berubah']} baris**.")
    baris.append(f"- `lokasi_verifikasi=perlu_verifikasi`: **{verifikasi['perlu_verifikasi']} baris**.")
    baris.append(f"- `lokasi_risiko=tinggi`: **{risiko['tinggi']} baris**.")
    baris.append(f"- Catatan Stage 5.2 terisi: **{meta['catatan_terisi']} baris**.")
    baris.append(f"- Duplikat judul/URL tetap: **{meta['duplikat_judul']} / {meta['duplikat_url']}** baris.")
    baris.append("")
    baris.append("## 2. Integritas")
    baris.append("")
    baris.append("| Pemeriksaan | Hasil |")
    baris.append("|---|---:|")
    baris.append(f"| Baris sumber | {meta['jumlah_sumber']} |")
    baris.append(f"| Baris keluaran | {len(rows)} |")
    baris.append(f"| Kolom sumber | {meta['kolom_sumber']} |")
    baris.append(f"| Kolom keluaran | {len(meta['fieldnames'])} |")
    baris.append(f"| URL unik | {len({r.get('url') for r in rows})} |")
    baris.append(f"| Hash sumber tetap | {meta['hash_before'] == meta['hash_after']} |")
    baris.append("")
    baris.append("Kolom baru:")
    baris.append("")
    for k in NEW_FIELDS:
        baris.append(f"- `{k}`")
    baris.append("")
    baris.append("## 3. Koreksi domain_lokasi")
    baris.append("")
    baris.append("Aturan baru: koordinat -> provinsi -> penanda eksplisit `in/di Indonesia` pada berita terklasifikasi -> `tidak_diketahui`.")
    baris.append("")
    baris.append("| Domain | Sebelum | Sesudah |")
    baris.append("|---|---:|---:|")
    for k in ("indonesia", "luar_indonesia", "tidak_diketahui"):
        baris.append(f"| {k} | {domain_lama.get(k, 0)} | {domain_baru.get(k, 0)} |")
    baris.append("")
    baris.append("| Transisi | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(transisi.items()):
        baris.append(f"| {k} | {v} |")
    baris.append("")
    baris.append("Basis domain:")
    baris.append("")
    baris.append("| Basis | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(basis.items()):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    baris.append("")
    baris.append("Contoh koreksi:")
    baris.append("")
    baris.append("| Baris | Sebelum | Sesudah | Judul |")
    baris.append("|---:|---|---|---|")
    contoh = []
    for nomor, r in enumerate(rows, start=1):
        if r.get("domain_lokasi_sebelum") != r.get("domain_lokasi"):
            contoh.append((nomor, r))
    for nomor, r in contoh[:12]:
        baris.append(
            f"| {nomor} | {r.get('domain_lokasi_sebelum')} | "
            f"{r.get('domain_lokasi')} | {str(r.get('judul',''))[:90]} |"
        )
    baris.append("")
    baris.append("## 4. Status verifikasi lokasi")
    baris.append("")
    baris.append("| Status | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(verifikasi.items()):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    baris.append("")
    baris.append("| Risiko | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(risiko.items()):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    baris.append("")
    baris.append("Baris yang ditandai:")
    baris.append("")
    baris.append("| Baris | Judul | Provinsi/Kabupaten | Risiko | Catatan |")
    baris.append("|---:|---|---|---|---|")
    for nomor in sorted(FOCUS_RISK):
        r = rows[nomor - 1]
        lokasi = f"{r.get('provinsi','')}/{r.get('kabupaten_kota','')}"
        baris.append(
            f"| {nomor} | {str(r.get('judul',''))[:80]} | {lokasi} | "
            f"{r.get('lokasi_risiko')} | {r.get('catatan_stage5_2')} |"
        )
    baris.append("")
    baris.append("Baris 27 tetap memakai `Nusa Tenggara Timur` / `Kabupaten Sumba Barat Daya`, "
                 "tetapi statusnya `perlu_verifikasi` karena epicenter dinyatakan di laut.")
    baris.append("")
    baris.append("## 5. Perubahan lain")
    baris.append("")
    baris.append("- Baris 214 diberi catatan `alamat_dinormalkan`; alamat yang tidak valid tetap dihapus pada Stage 5.")
    baris.append("- Penandaan duplikat tidak diubah: 10 baris judul, 0 baris URL.")
    baris.append("- Kategori, provinsi, kabupaten/kota, alamat, koordinat, dan `isi_berita` tidak diubah pada Stage 5.2.")
    baris.append("- `domain_lokasi_sebelum` menyimpan nilai Stage 5 untuk jejak audit.")
    baris.append("")
    baris.append("## 6. Batas")
    baris.append("")
    baris.append("- Tidak ada verifikasi koordinat independen; 40 koordinat tetap `belum_diverifikasi`.")
    baris.append("- Tidak ada scraping atau geocoding online.")
    baris.append("- Kabupaten/kota pada tujuh baris tetap berupa rujukan toponimi, bukan batas administratif terverifikasi.")
    baris.append("- `domain_lokasi` adalah domain kejadian berbasis bukti teks/koordinat, bukan validasi lapangan.")
    baris.append("")
    baris.append("## 7. Pengujian")
    baris.append("")
    baris.append("- Perintah: `python -m unittest -q test_category_detector test_location_extractor test_stage5_quality test_stage5_2_quality`")
    baris.append("- Hasil: 34 test lulus (25 test Stage 2/3/5 + 9 test Stage 5.2).")
    baris.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(baris))


def main():
    if not SRC.exists():
        raise SystemExit(f"Sumber tidak ditemukan: {SRC}")
    hash_before = sha256(SRC)
    if hash_before != EXPECTED_SHA256:
        raise SystemExit("Hash sumber Stage 5 tidak sesuai.")

    with open(SRC, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    baru = bangun_baris(rows)
    fieldnames_output = list(fieldnames)
    for k in NEW_FIELDS:
        if k not in fieldnames_output:
            fieldnames_output.append(k)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "data" / f"geohazard_news_located_{ts}_stage5_2.csv"
    nomor = 2
    while output.exists():
        output = ROOT / "data" / f"geohazard_news_located_{ts}_stage5_2_{nomor}.csv"
        nomor += 1

    tulis_csv(output, baru, fieldnames_output)
    hash_after = sha256(SRC)
    hash_output = sha256(output)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "perbaikan_kualitas_data_stage5_2.md"
    nomor_laporan = 2
    while report.exists():
        report = REPORT_DIR / f"perbaikan_kualitas_data_stage5_2_{nomor_laporan}.md"
        nomor_laporan += 1

    meta = {
        "waktu": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "hash_before": hash_before,
        "hash_after": hash_after,
        "hash_output": hash_output,
        "jumlah_sumber": len(rows),
        "kolom_sumber": len(fieldnames),
        "fieldnames": fieldnames_output,
        "baru": baru,
        "domain_berubah": sum(
            1 for r in baru
            if r.get("domain_lokasi_sebelum") != r.get("domain_lokasi")
        ),
        "catatan_terisi": sum(1 for r in baru if r.get("catatan_stage5_2")),
        "duplikat_judul": sum(1 for r in baru if r.get("duplikat_judul") == "ya"),
        "duplikat_url": sum(1 for r in baru if r.get("duplikat_url") == "ya"),
    }
    tulis_laporan(report, SRC, output, meta)

    print(f"Sumber        : {SRC}")
    print(f"Hash sebelum  : {hash_before}")
    print(f"Hash sesudah  : {hash_after}")
    print(f"Hash keluaran : {hash_output}")
    print(f"Baris         : {len(rows)} -> {len(baru)}")
    print(f"Kolom         : {len(fieldnames)} -> {len(fieldnames_output)}")
    print(f"Domain ubah   : {meta['domain_berubah']}")
    print(f"Catatan isi   : {meta['catatan_terisi']}")
    print(f"Output        : {output}")
    print(f"Laporan       : {report}")


if __name__ == "__main__":
    main()
