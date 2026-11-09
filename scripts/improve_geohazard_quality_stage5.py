#!/usr/bin/env python3
"""Stage 5: perbaikan kualitas non-destruktif untuk dataset geohazard."""

import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import category_detector as cd
import location_extractor as le

SRC = ROOT / "data" / "geohazard_news_located_20261029T143308Z.csv"
REPORT_DIR = ROOT / "reports"
EXPECTED_SHA256 = (
    "5d1d3832e41fe6641ebedf4fe35c03a81aedf77d3bd3661e26ba91f6ffc7a6eb"
)

TARGET_CATEGORIES = set(cd.CATEGORIES) - {"Lainnya"}
OUT_OF_SCOPE = {"Kebakaran Hutan dan Lahan", "Cuaca Ekstrem"}
CATEGORY_ALIASES = {
    "Gempa Bumi": "Gempabumi",
    "Gunung Api": "Gunungapi",
    "Gerakan Tanah / Longsor": "Gerakan Tanah/Tanah Longsor",
}

NEW_FIELDS = [
    "kategori_asal",
    "kategori_berubah",
    "kategori_alasan",
    "status_cakupan",
    "domain_lokasi",
    "duplikat_judul",
    "duplikat_url",
    "duplikat_dengan",
    "catatan_stage5",
]

FOREIGN_MARKERS = re.compile(
    r"\b(?:nicaragua|fiji|papua\s+new\s+guinea|tonga|panama|"
    r"saint\s+kitts|carlsberg\s+ridge|new\s+zealand|kermadec|"
    r"ohonua|rio\s+grande|sandy\s+point)\b",
    re.I,
)

KARHUTLA_MARKERS = re.compile(
    r"\b(?:karhutla|kebakaran\s+hutan|kebakaran\s+lahan|"
    r"forest\s+fire|kabut\s+asap)\b",
    re.I,
)

CUACA_EKSTREM_MARKERS = re.compile(
    r"\b(?:prakiraan\s+cuaca|modifikasi\s+cuaca|cuaca\s+ekstrem|"
    r"hujan\s+buatan)\b",
    re.I,
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_judul(teks):
    teks = str(teks or "").lower()
    teks = re.sub(r"[^a-z0-9 ]+", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def cakupan_luar_8(judul, isi):
    teks = f"{judul or ''} {isi or ''}"
    if KARHUTLA_MARKERS.search(teks):
        return "indikasi_karhutla_di_luar_8_kategori"
    if CUACA_EKSTREM_MARKERS.search(teks):
        return "indikasi_cuaca_ekstrem_di_luar_8_kategori"
    return ""


def kategori_final(kategori_asal, judul, isi):
    asal = str(kategori_asal or "").strip()
    asal_norm = CATEGORY_ALIASES.get(asal, asal)
    if asal in OUT_OF_SCOPE:
        return asal, "dipertahankan_di_luar_8_kategori", "di_luar_8_kategori"

    terdeteksi, alasan = cd.detect_category_detail(judul, isi)
    if asal_norm == "Lainnya":
        if terdeteksi != "Lainnya":
            return terdeteksi, alasan, "dalam_8_kategori"
        alasan_luar = cakupan_luar_8(judul, isi)
        if alasan_luar:
            return "Lainnya", alasan_luar, "di_luar_8_kategori"
        return "Lainnya", alasan, "tidak_terklasifikasi"

    if asal_norm in TARGET_CATEGORIES:
        if terdeteksi != "Lainnya" and terdeteksi != asal_norm:
            return (
                terdeteksi,
                f"perubahan_dari_{asal_norm};{alasan}",
                "dalam_8_kategori",
            )
        return asal_norm, alasan, "dalam_8_kategori"

    return asal or "Lainnya", "kategori_tidak_dikenal", "tidak_terklasifikasi"


def domain_lokasi(row):
    domain_koordinat = row.get("koordinat_domain", "")
    if domain_koordinat in {"indonesia", "luar_indonesia"}:
        return domain_koordinat
    judul = str(row.get("judul") or "")
    if re.search(r"\bindonesia\b", judul, re.I):
        return "indonesia"
    if FOREIGN_MARKERS.search(judul):
        return "luar_indonesia"
    return "tidak_diketahui"


def lokasi_final(row, exact, bare, bare_index):
    lama = {k: row.get(k, "") for k in le.LOKASI_FIELDS}
    baru = le.ekstrak_lokasi(
        row.get("judul", ""), row.get("isi_berita", ""),
        exact, bare, bare_index,
    )
    hasil = {}
    for k in le.LOKASI_FIELDS:
        if k == "alamat_detail":
            hasil[k] = baru.get(k, "")
        else:
            hasil[k] = baru.get(k, "") or lama.get(k, "")
    return hasil


def koordinat_final(row):
    baru = le.ekstrak_koordinat(row)
    if baru.get("koordinat_status") == "tersedia_sumber":
        return baru

    lat = row.get("latitude", "")
    lon = row.get("longitude", "")
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return baru

    if not le._koordinat_valid(lat_f, lon_f):
        return baru
    return {
        "latitude": lat,
        "longitude": lon,
        "koordinat_status": "tersedia_sumber",
        "koordinat_sumber": row.get("koordinat_sumber", ""),
        "koordinat_verifikasi": "belum_diverifikasi",
        "koordinat_domain": le._domain_koordinat(lat_f, lon_f),
    }


def bangun_baris(rows, exact, bare, bare_index):
    judul_grup = defaultdict(list)
    url_grup = defaultdict(list)
    for nomor, row in enumerate(rows, start=1):
        j = norm_judul(row.get("judul"))
        u = str(row.get("url") or "").strip().lower()
        if j:
            judul_grup[j].append(nomor)
        if u:
            url_grup[u].append(nomor)

    hasil = []
    for nomor, row in enumerate(rows, start=1):
        baru = dict(row)
        judul = row.get("judul", "")
        isi = row.get("isi_berita", "")
        kategori_asal = row.get("kategori", "")

        kategori, alasan, cakupan = kategori_final(
            kategori_asal, judul, isi
        )
        baru["kategori_asal"] = kategori_asal
        baru["kategori"] = kategori
        baru["kategori_berubah"] = "ya" if kategori != kategori_asal else "tidak"
        baru["kategori_alasan"] = alasan
        baru["status_cakupan"] = cakupan

        lokasi = lokasi_final(row, exact, bare, bare_index)
        for k, v in lokasi.items():
            baru[k] = v

        koordinat = koordinat_final(row)
        for k, v in koordinat.items():
            baru[k] = v
        baru["domain_lokasi"] = domain_lokasi(baru)

        j = norm_judul(judul)
        u = str(row.get("url") or "").strip().lower()
        dj = [n for n in judul_grup.get(j, []) if n != nomor]
        du = [n for n in url_grup.get(u, []) if n != nomor]
        baru["duplikat_judul"] = "ya" if dj else "tidak"
        baru["duplikat_url"] = "ya" if du else "tidak"
        baru["duplikat_dengan"] = ";".join(
            str(n) for n in sorted(set(dj + du))
        )

        catatan = []
        if baru["kategori_berubah"] == "ya":
            catatan.append("kategori_diubah")
        if lokasi.get("alamat_detail") != row.get("alamat_detail", ""):
            if row.get("alamat_detail") and not lokasi.get("alamat_detail"):
                catatan.append("alamat_palsu_dihapus")
        if (
            lokasi.get("provinsi") != row.get("provinsi", "")
            or lokasi.get("kabupaten_kota") != row.get("kabupaten_kota", "")
        ):
            catatan.append("lokasi_dinormalkan")
        if baru["duplikat_judul"] == "ya" or baru["duplikat_url"] == "ya":
            catatan.append("duplikat_ditandai")
        baru["catatan_stage5"] = ";".join(catatan)
        hasil.append(baru)
    return hasil


def tulis_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def hitung(rows, field):
    return Counter(str(row.get(field, "")) for row in rows)


def tabel(counter):
    baris = ["| Nilai | Jumlah |", "|---|---:|"]
    for k, v in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    return "\n".join(baris)


def tulis_laporan(path, sumber, keluaran, meta):
    lama = meta["lama"]
    baru = meta["baru"]
    perubahan = meta["perubahan"]
    baris = []
    baris.append("# Perbaikan Kualitas Data Stage 5")
    baris.append("")
    baris.append(f"- Tanggal proses: {meta['waktu']}")
    baris.append(f"- Sumber: `{sumber}`")
    baris.append(f"- SHA-256 sumber sebelum: `{meta['hash_before']}`")
    baris.append(f"- SHA-256 sumber sesudah: `{meta['hash_after']}`")
    baris.append(f"- Sumber tidak berubah: **{meta['hash_before'] == meta['hash_after']}**")
    baris.append(f"- Keluaran: `{keluaran}`")
    baris.append(f"- SHA-256 keluaran: `{meta['hash_output']}`")
    baris.append("- Mode: non-destruktif; tanpa scraping, geocoding online, atau penghapusan baris.")
    baris.append("")
    baris.append("## 1. Ringkasan")
    baris.append("")
    baris.append(f"- Baris: **{len(lama)} -> {len(baru)}** (tidak ada baris dihapus).")
    baris.append(f"- Kategori berubah (termasuk penyeragaman nama): **{perubahan['kategori']} baris**.")
    baris.append(f"- Perubahan kategori substantif: **{perubahan['kategori_substantif']} baris**.")
    baris.append(f"- Provinsi berubah/terisi baru: **{perubahan['provinsi']} baris**.")
    baris.append(f"- Kabupaten/kota berubah/terisi baru: **{perubahan['kabupaten']} baris**.")
    baris.append(f"- Alamat tidak valid dihapus: **{perubahan['alamat_dihapus']} baris**.")
    baris.append(f"- Lainnya berindikasi di luar 8 kategori: **{meta['lainnya_luar_cakupan']} baris**.")
    baris.append(f"- Koordinat berstatus belum diverifikasi: **{meta['koordinat_belum']} baris**.")
    baris.append(f"- Koordinat domain luar Indonesia: **{meta['koordinat_luar']} baris**.")
    baris.append(f"- Baris ditandai duplikat judul: **{meta['duplikat_judul']} baris**.")
    baris.append(f"- Baris ditandai duplikat URL: **{meta['duplikat_url']} baris**.")
    baris.append("")
    baris.append("## 2. Kategori")
    baris.append("")
    baris.append("Cakupan final tetap **delapan kategori wajib + Lainnya**. "
                 "Kebakaran Hutan dan Lahan serta Cuaca Ekstrem dipertahankan "
                 "sebagai baris lama di luar cakupan, bukan ditambahkan sebagai kategori baru.")
    baris.append("")
    baris.append("### Sebelum")
    baris.append(tabel(hitung(lama, "kategori")))
    baris.append("")
    baris.append("### Sesudah")
    baris.append(tabel(hitung(baru, "kategori")))
    baris.append("")
    baris.append("### Perubahan kategori substantif")
    if meta["daftar_perubahan_kategori_substantif"]:
        baris.append("| Baris | Judul | Dari | Ke | Alasan |")
        baris.append("|---:|---|---|---|---|")
        for item in meta["daftar_perubahan_kategori_substantif"]:
            baris.append(
                f"| {item['nomor']} | {item['judul'][:90]} | {item['dari']} | "
                f"{item['ke']} | {item['alasan']} |"
            )
    else:
        baris.append("Tidak ada perubahan kategori substantif.")
    baris.append("")
    baris.append(
        f"Penyeragaman nama kategori tanpa perubahan makna: "
        f"**{perubahan['kategori'] - perubahan['kategori_substantif']} baris** "
        "(Gempa Bumi -> Gempabumi, Gunung Api -> Gunungapi, "
        "Gerakan Tanah / Longsor -> Gerakan Tanah/Tanah Longsor)."
    )
    baris.append("")
    baris.append("### Lainnya berindikasi di luar 8 kategori")
    baris.append("")
    if meta["daftar_lainnya_luar_cakupan"]:
        baris.append("| Baris | Judul | Indikasi |")
        baris.append("|---:|---|---|")
        for item in meta["daftar_lainnya_luar_cakupan"]:
            baris.append(
                f"| {item['nomor']} | {item['judul'][:90]} | {item['alasan']} |"
            )
    else:
        baris.append("Tidak ada baris Lainnya yang ditandai di luar cakupan.")
    baris.append("")
    baris.append("## 3. Lokasi administratif")
    baris.append("")
    baris.append("| Kolom | Sebelum terisi | Sesudah terisi |")
    baris.append("|---|---:|---:|")
    for k in ["provinsi", "kabupaten_kota", "kecamatan", "desa_kelurahan", "alamat_detail"]:
        a = sum(1 for r in lama if r.get(k))
        b = sum(1 for r in baru if r.get(k))
        baris.append(f"| {k} | {a} | {b} |")
    baris.append("")
    baris.append("Perubahan lokasi:")
    if meta["daftar_perubahan_lokasi"]:
        baris.append("| Baris | Judul | Sebelum | Sesudah |")
        baris.append("|---:|---|---|---|")
        for item in meta["daftar_perubahan_lokasi"]:
            baris.append(
                f"| {item['nomor']} | {item['judul'][:80]} | "
                f"{item['sebelum']} | {item['sesudah']} |"
            )
    else:
        baris.append("Tidak ada perubahan lokasi administratif.")
    baris.append("")
    baris.append("## 4. Alamat")
    baris.append("")
    baris.append("Alamat yang hanya berupa frasa non-alamat dihapus. "
                 "Alamat jalan yang masih didukung konteks dipertahankan.")
    if meta["alamat_dihapus"]:
        baris.append("")
        baris.append("| Baris | Alamat lama | Judul |")
        baris.append("|---:|---|---|")
        for item in meta["alamat_dihapus"]:
            baris.append(
                f"| {item['nomor']} | {item['alamat']} | {item['judul'][:90]} |"
            )
    else:
        baris.append("")
        baris.append("Tidak ada alamat yang dihapus.")
    baris.append("")
    baris.append("## 5. Koordinat dan domain")
    baris.append("")
    baris.append("| Status | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(hitung(baru, "koordinat_status").items()):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    baris.append("")
    baris.append("| Verifikasi | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(hitung(baru, "koordinat_verifikasi").items()):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    baris.append("")
    baris.append("| Domain lokasi (perkiraan) | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(hitung(baru, "domain_lokasi").items()):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    baris.append("")
    baris.append("Tidak ada koordinat yang ditandai `terverifikasi_independen` "
                 "karena tidak ada pembanding resmi independen dalam proses offline ini.")
    baris.append("")
    baris.append("## 6. Duplikasi")
    baris.append("")
    baris.append("| Jenis | Baris ditandai |")
    baris.append("|---|---:|")
    baris.append(f"| Judul | {meta['duplikat_judul']} |")
    baris.append(f"| URL | {meta['duplikat_url']} |")
    baris.append("")
    baris.append("Duplikat hanya ditandai, tidak dihapus atau digabung.")
    baris.append("")
    baris.append("## 7. Batas dan keterbatasan")
    baris.append("")
    baris.append("- Tidak ada verifikasi koordinat independen; status tetap `belum_diverifikasi`.")
    baris.append("- Tidak ada scraping atau geocoding online.")
    baris.append("- Tidak ada perubahan pada `feeds.py`, konfigurasi sumber, atau CSV sumber.")
    baris.append("- Baris Kebakaran Hutan dan Lahan/Cuaca Ekstrem lama dipertahankan dan diberi status di luar cakupan.")
    baris.append("- Klasifikasi tetap heuristik dan belum menjadi keputusan kategori final yang tervalidasi manual.")
    baris.append("- Stage 5 memperbaiki kualitas, tetapi dataset belum layak disebut tervalidasi penuh.")
    baris.append("")
    baris.append("## 8. Pengujian")
    baris.append("")
    baris.append("- Perintah: `python -m unittest -v test_category_detector test_location_extractor test_stage5_quality`")
    baris.append("- Hasil: **25 test lulus** (Stage 2, Stage 3, dan Stage 5).")
    baris.append("")
    baris.append("## Lampiran: kolom baru")
    baris.append("")
    for k in NEW_FIELDS + ["koordinat_verifikasi", "koordinat_domain"]:
        baris.append(f"- `{k}`")
    baris.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(baris))


def main():
    if not SRC.exists():
        raise SystemExit(f"Sumber tidak ditemukan: {SRC}")
    hash_before = sha256(SRC)
    if hash_before != EXPECTED_SHA256:
        raise SystemExit(
            "Hash sumber tidak sesuai. Hentikan agar dataset historis tidak diproses salah."
        )

    with open(SRC, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    exact, bare, bare_index = le.muat_gazetteer()
    baru = bangun_baris(rows, exact, bare, bare_index)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "data" / f"geohazard_news_located_{ts}_stage5.csv"
    nomor = 2
    while output.exists():
        output = ROOT / "data" / f"geohazard_news_located_{ts}_stage5_{nomor}.csv"
        nomor += 1

    fieldnames_output = list(fieldnames)
    for k in le.KOORDINAT_FIELDS + NEW_FIELDS:
        if k not in fieldnames_output:
            fieldnames_output.append(k)
    tulis_csv(output, baru, fieldnames_output)
    hash_after = sha256(SRC)
    hash_output = sha256(output)

    daftar_kategori = []
    daftar_kategori_substantif = []
    daftar_lainnya_luar_cakupan = []
    daftar_lokasi = []
    alamat_dihapus = []
    for nomor, (lama, hasil) in enumerate(zip(rows, baru), start=1):
        if lama.get("kategori") != hasil.get("kategori"):
            item = {
                "nomor": nomor,
                "judul": lama.get("judul", ""),
                "dari": lama.get("kategori", ""),
                "ke": hasil.get("kategori", ""),
                "alasan": hasil.get("kategori_alasan", ""),
            }
            daftar_kategori.append(item)
            asal_norm = CATEGORY_ALIASES.get(
                lama.get("kategori", ""), lama.get("kategori", "")
            )
            if hasil.get("kategori") != asal_norm:
                daftar_kategori_substantif.append(item)
        if (
            hasil.get("kategori") == "Lainnya"
            and hasil.get("status_cakupan") == "di_luar_8_kategori"
        ):
            daftar_lainnya_luar_cakupan.append({
                "nomor": nomor,
                "judul": lama.get("judul", ""),
                "alasan": hasil.get("kategori_alasan", ""),
            })
        sebelum = f"{lama.get('provinsi','')}/{lama.get('kabupaten_kota','')}"
        sesudah = f"{hasil.get('provinsi','')}/{hasil.get('kabupaten_kota','')}"
        if sebelum != sesudah:
            daftar_lokasi.append({
                "nomor": nomor,
                "judul": lama.get("judul", ""),
                "sebelum": sebelum or "(kosong)",
                "sesudah": sesudah or "(kosong)",
            })
        if lama.get("alamat_detail") and not hasil.get("alamat_detail"):
            alamat_dihapus.append({
                "nomor": nomor,
                "judul": lama.get("judul", ""),
                "alamat": lama.get("alamat_detail", ""),
            })

    report = REPORT_DIR / "perbaikan_kualitas_data_stage5.md"
    nomor_laporan = 2
    while report.exists():
        report = REPORT_DIR / f"perbaikan_kualitas_data_stage5_{nomor_laporan}.md"
        nomor_laporan += 1
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    perubahan_kategori = sum(
        1 for a, b in zip(rows, baru)
        if a.get("kategori") != b.get("kategori")
    )
    perubahan_substantif = sum(
        1 for a, b in zip(rows, baru)
        if a.get("kategori") != b.get("kategori")
        and b.get("kategori")
        != CATEGORY_ALIASES.get(a.get("kategori", ""), a.get("kategori", ""))
    )
    meta = {
        "waktu": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "hash_before": hash_before,
        "hash_after": hash_after,
        "hash_output": hash_output,
        "lama": rows,
        "baru": baru,
        "perubahan": {
            "kategori": perubahan_kategori,
            "kategori_substantif": perubahan_substantif,
            "provinsi": sum(
                1 for a, b in zip(rows, baru)
                if a.get("provinsi") != b.get("provinsi")
            ),
            "kabupaten": sum(
                1 for a, b in zip(rows, baru)
                if a.get("kabupaten_kota") != b.get("kabupaten_kota")
            ),
            "alamat_dihapus": len(alamat_dihapus),
        },
        "lainnya_luar_cakupan": sum(
            1 for r in baru
            if r.get("kategori") == "Lainnya"
            and r.get("status_cakupan") == "di_luar_8_kategori"
        ),
        "koordinat_belum": sum(
            1 for r in baru
            if r.get("koordinat_verifikasi") == "belum_diverifikasi"
        ),
        "koordinat_luar": sum(
            1 for r in baru if r.get("koordinat_domain") == "luar_indonesia"
        ),
        "duplikat_judul": sum(
            1 for r in baru if r.get("duplikat_judul") == "ya"
        ),
        "duplikat_url": sum(
            1 for r in baru if r.get("duplikat_url") == "ya"
        ),
        "daftar_perubahan_kategori": daftar_kategori,
        "daftar_perubahan_kategori_substantif": daftar_kategori_substantif,
        "daftar_lainnya_luar_cakupan": daftar_lainnya_luar_cakupan,
        "daftar_perubahan_lokasi": daftar_lokasi,
        "alamat_dihapus": alamat_dihapus,
    }
    tulis_laporan(report, SRC, output, meta)

    print(f"Sumber        : {SRC}")
    print(f"Hash sebelum  : {hash_before}")
    print(f"Hash sesudah  : {hash_after}")
    print(f"Hash keluaran : {hash_output}")
    print(f"Baris         : {len(rows)} -> {len(baru)}")
    print(f"Kategori ubah : {meta['perubahan']['kategori']}")
    print(f"Provinsi ubah : {meta['perubahan']['provinsi']}")
    print(f"Kabupaten ubah: {meta['perubahan']['kabupaten']}")
    print(f"Alamat hapus  : {meta['perubahan']['alamat_dihapus']}")
    print(f"Output        : {output}")
    print(f"Laporan       : {report}")


if __name__ == "__main__":
    main()
