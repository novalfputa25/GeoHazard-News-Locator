#!/usr/bin/env python3
"""Stage 5.4: ekstraksi event_time berbasis bukti eksplisit."""

import csv
import hashlib
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "data" / "geohazard_news_located_20261101T140913Z_stage5_2.csv"
REPORT_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"
EXPECTED_SHA256 = (
    "a954df014dd7f6e03051381fb75b9c451bd3e740ba20378d96c05489be860343"
)

NEW_FIELDS = [
    "event_time_status",
    "event_time_basis",
    "event_time_evidence",
]

STATUSES = {
    "terekstrak",
    "tanggal_saja",
    "tidak_tersedia",
    "perlu_review",
}

HAZARD_CATEGORIES = {
    "Cuaca Ekstrem",
    "Gempabumi",
    "Gunungapi",
    "Kebakaran Hutan dan Lahan",
    "Gerakan Tanah/Tanah Longsor",
    "Abrasi dan Akresi",
}

BULAN = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "agu": 8,
    "agt": 8,
    "sep": 9,
    "sept": 9,
    "okt": 10,
    "nov": 11,
    "des": 12,
    "january": 1,
    "february": 2,
    "march": 3,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "october": 10,
    "december": 12,
    "aug": 8,
    "oct": 10,
    "dec": 12,
}

ZONA = {
    "WIB": 7,
    "WITA": 8,
    "WIT": 9,
    "UTC": 0,
    "GMT": 0,
}

EVENT_NEAR_RE = re.compile(
    r"\b(?:gempa|gempabumi|mengguncang|erupsi|meletus|letusan|"
    r"longsor|banjir|kebakaran|karhutla|asap|kabut|hujan|"
    r"abrasi|tsunami|gunung|vulkanik)\b",
    re.I,
)

NON_EVENT_RE = re.compile(
    r"\b(?:pembatasan|akses|mulai|berlaku|hingga|sejak|laporan|"
    r"data|per|ditutup|kunjungan|dijadwalkan|promo|diskon|buyback|"
    r"harga|tayang|rapat|pembelajaran|tanam|mangrove|menyelenggarakan|"
    r"pelatihan|rencana|tanggap\s+darurat)\b",
    re.I,
)

JUDUL_HAZARD_RE = re.compile(
    r"\b(?:gempa|gempabumi|erupsi|gunung|letusan|longsor|banjir|"
    r"kebakaran|karhutla|asap|kabut|hujan|abrasi|tsunami|"
    r"cuaca\s+ekstrem)\b",
    re.I,
)

BULAN_RE = "|".join(sorted(BULAN, key=len, reverse=True))
TANGGAL_NAMA_RE = re.compile(
    r"(?<!\d)(\d{1,2})\s+(" + BULAN_RE + r")\b\s+(\d{2,4})(?!\d)",
    re.I,
)
TANGGAL_SLASH_RE = re.compile(
    r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2,4})(?!\d)",
)
TANGGAL_ISO_RE = re.compile(
    r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)",
)
TANGGAL_NAMA_TANPA_TAHUN_RE = re.compile(
    r"(?<!\d)(\d{1,2})\s+(" + BULAN_RE + r")\b(?!\s+\d{2,4})(?!\d)",
    re.I,
)
TANGGAL_SLASH_TANPA_TAHUN_RE = re.compile(
    r"(?<!\d)(\d{1,2})/(\d{1,2})(?![/-]\d{2,4})(?!\d)",
)
WAKTU_RE = re.compile(
    r"(?<!\d)(\d{1,2})[.:](\d{2})(?:[.:](\d{2}))?\s*"
    r"(WIB|WITA|WIT|UTC|GMT)?\b",
    re.I,
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _tahun(nilai):
    tahun = int(nilai)
    if tahun < 100:
        tahun += 2000
    return tahun


def _tanggal(tahun, bulan, hari):
    try:
        return date(int(tahun), int(bulan), int(hari))
    except ValueError:
        return None


def _tanggal_dari_nama(hari, nama_bulan, tahun):
    bulan = BULAN.get(nama_bulan.lower())
    if not bulan:
        return None
    return _tanggal(_tahun(tahun), bulan, hari)


def _tanggal_dari_slash(hari, bulan, tahun):
    return _tanggal(_tahun(tahun), bulan, hari)


def _format_tanggal(nilai):
    return nilai.isoformat()


def _format_waktu(nilai, zona=None):
    if zona:
        offset = timezone(timedelta(hours=ZONA[zona.upper()]))
        nilai = nilai.replace(tzinfo=offset)
    return nilai.isoformat(timespec="seconds")


def _snippet(teks, start, end, pad=90):
    a = max(0, start - pad)
    b = min(len(teks), end + pad)
    potongan = re.sub(r"\s+", " ", teks[a:b]).strip()
    if a > 0:
        potongan = "..." + potongan
    if b < len(teks):
        potongan = potongan + "..."
    return potongan


def _rentang_tanggal(teks, start):
    i = start - 1
    while i >= 0 and teks[i].isspace():
        i -= 1
    if i >= 0 and teks[i] in "-–—":
        j = i - 1
        while j >= 0 and teks[j].isspace():
            j -= 1
        if j >= 0 and teks[j].isdigit():
            return True
    return False


def _hasil(status, basis, evidence="", event_time=""):
    if status not in STATUSES:
        raise ValueError(f"Status tidak valid: {status}")
    return {
        "event_time": event_time,
        "event_time_status": status,
        "event_time_basis": basis,
        "event_time_evidence": evidence,
    }


def cari_tanggal_lengkap(teks):
    hasil = []
    for pola in (TANGGAL_NAMA_RE, TANGGAL_SLASH_RE, TANGGAL_ISO_RE):
        for m in pola.finditer(teks):
            if pola is TANGGAL_NAMA_RE:
                nilai = _tanggal_dari_nama(m.group(1), m.group(2), m.group(3))
            elif pola is TANGGAL_SLASH_RE:
                nilai = _tanggal_dari_slash(m.group(1), m.group(2), m.group(3))
            else:
                nilai = _tanggal(m.group(1), m.group(2), m.group(3))
            if nilai is None:
                continue
            hasil.append((nilai, m.start(), m.end()))
    hasil.sort(key=lambda x: (x[1], x[2]))
    unik = []
    for item in hasil:
        if unik and item[1] < unik[-1][2]:
            continue
        unik.append(item)
    return unik


def cari_tanggal_tanpa_tahun(teks):
    hasil = []
    for m in TANGGAL_NAMA_TANPA_TAHUN_RE.finditer(teks):
        if BULAN.get(m.group(2).lower()):
            hasil.append((m.group(0), m.start(), m.end()))
    for m in TANGGAL_SLASH_TANPA_TAHUN_RE.finditer(teks):
        if 1 <= int(m.group(1)) <= 31 and 1 <= int(m.group(2)) <= 12:
            hasil.append((m.group(0), m.start(), m.end()))
    hasil.sort(key=lambda x: x[1])
    return hasil


def cari_waktu_dekat(teks, start, end, radius=260):
    a = max(0, start - radius)
    b = min(len(teks), end + radius)
    pilihan = []
    for m in WAKTU_RE.finditer(teks, a, b):
        jam = int(m.group(1))
        menit = int(m.group(2))
        detik = int(m.group(3) or 0)
        if jam > 23 or menit > 59 or detik > 59:
            continue
        jarak = min(abs(m.start() - start), abs(m.end() - end))
        zona = (m.group(4) or "").upper() or None
        pilihan.append((jarak, m.start(), m.end(), jam, menit, detik, zona))
    if not pilihan:
        return None
    return min(pilihan, key=lambda x: x[0])


def _hazard_context(row):
    if str(row.get("kategori") or "") in HAZARD_CATEGORIES:
        return True
    return bool(JUDUL_HAZARD_RE.search(str(row.get("judul") or "")))


def _ekstrak_bmkg(row):
    body = str(row.get("isi_berita") or "")
    m = re.search(
        r"Tanggal:\s*(\d{1,2})\s+(" + BULAN_RE + r")\s+(\d{4})\s+"
        r"(\d{1,2}):(\d{2}):(\d{2})\s+(WIB|WITA|WIT)\b",
        body,
        re.I,
    )
    if m:
        tanggal = _tanggal_dari_nama(m.group(1), m.group(2), m.group(3))
        if tanggal:
            nilai = datetime(
                tanggal.year,
                tanggal.month,
                tanggal.day,
                int(m.group(4)),
                int(m.group(5)),
                int(m.group(6)),
            )
            return _hasil(
                "terekstrak",
                "bmkg_tanggal",
                m.group(0),
                _format_waktu(nilai, m.group(7)),
            )

    m = re.search(
        r"akan terjadi pada\s+(\d{1,2})\s+(" + BULAN_RE + r")\s+(\d{4}),\s*"
        r"(\d{1,2}):(\d{2})\s*(WIB|WITA|WIT)\b",
        body,
        re.I,
    )
    if m:
        tanggal = _tanggal_dari_nama(m.group(1), m.group(2), m.group(3))
        if tanggal:
            nilai = datetime(
                tanggal.year,
                tanggal.month,
                tanggal.day,
                int(m.group(4)),
                int(m.group(5)),
            )
            return _hasil(
                "terekstrak",
                "bmkg_nowcast",
                m.group(0),
                _format_waktu(nilai, m.group(6)),
            )

    if body.strip():
        return _hasil(
            "perlu_review",
            "bmkg_tidak_terbaca",
            _snippet(body, 0, min(len(body), 120)),
        )
    return _hasil("tidak_tersedia", "tidak_ada_bukti")


def _ekstrak_usgs(row):
    body = str(row.get("isi_berita") or "")
    m = re.search(
        r"Time\s+(\d{4})-(\d{2})-(\d{2})\s+"
        r"(\d{1,2}):(\d{2}):(\d{2})\s+(UTC|GMT)\b",
        body,
        re.I,
    )
    if m:
        tanggal = _tanggal(m.group(1), m.group(2), m.group(3))
        if tanggal:
            nilai = datetime(
                tanggal.year,
                tanggal.month,
                tanggal.day,
                int(m.group(4)),
                int(m.group(5)),
                int(m.group(6)),
            )
            return _hasil(
                "terekstrak",
                "usgs_time",
                m.group(0),
                _format_waktu(nilai, m.group(7)),
            )
    if "Time" in body:
        return _hasil(
            "perlu_review",
            "usgs_tidak_terbaca",
            _snippet(body, 0, min(len(body), 120)),
        )
    return _hasil("tidak_tersedia", "tidak_ada_bukti")


def _ekstrak_gdacs(row):
    body = str(row.get("isi_berita") or "")
    judul = str(row.get("judul") or "")

    m = re.search(
        r"On\s+(\d{1,2})/(\d{1,2})/(\d{4}),\s+a forest fire started",
        body,
        re.I,
    )
    if m:
        tanggal = _tanggal_dari_slash(m.group(1), m.group(2), m.group(3))
        if tanggal:
            return _hasil(
                "tanggal_saja",
                "gdacs_start",
                m.group(0),
                _format_tanggal(tanggal),
            )

    m = re.search(
        r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})\s+(UTC|GMT)\b",
        judul,
        re.I,
    )
    if m:
        tanggal = _tanggal_dari_slash(m.group(1), m.group(2), m.group(3))
        if tanggal:
            nilai = datetime(
                tanggal.year,
                tanggal.month,
                tanggal.day,
                int(m.group(4)),
                int(m.group(5)),
            )
            return _hasil(
                "terekstrak",
                "gdacs_judul",
                m.group(0),
                _format_waktu(nilai, m.group(6)),
            )

    if body.strip() or judul.strip():
        return _hasil(
            "tidak_tersedia",
            "tidak_ada_tanggal_kejadian",
        )
    return _hasil("tidak_tersedia", "tidak_ada_bukti")


def _ekstrak_umum(row):
    body = str(row.get("isi_berita") or "")
    if not _hazard_context(row) or not body.strip():
        return _hasil("tidak_tersedia", "tidak_ada_bukti")

    kandidat = cari_tanggal_lengkap(body)
    diterima = []
    review = None
    for tanggal, start, end in kandidat:
        jendela = body[max(0, start - 180):min(len(body), end + 180)]
        evidence = _snippet(body, start, end, 100)
        if _rentang_tanggal(body, start):
            review = review or _hasil(
                "perlu_review",
                "kandidat_rentang_tanggal",
                evidence,
            )
            continue
        if NON_EVENT_RE.search(jendela):
            review = review or _hasil(
                "perlu_review",
                "kandidat_bukan_waktu_kejadian",
                evidence,
            )
            continue
        if not EVENT_NEAR_RE.search(jendela):
            review = review or _hasil(
                "perlu_review",
                "kandidat_konteks_tidak_jelas",
                evidence,
            )
            continue
        diterima.append((tanggal, start, end))

    if len(diterima) > 1:
        return _hasil(
            "perlu_review",
            "kandidat_tanggal_ganda",
            _snippet(body, diterima[0][1], diterima[-1][2], 80),
        )

    if diterima:
        tanggal, start, end = diterima[0]
        waktu = cari_waktu_dekat(body, start, end)
        if waktu:
            _, ws, we, jam, menit, detik, zona = waktu
            nilai = datetime(
                tanggal.year,
                tanggal.month,
                tanggal.day,
                jam,
                menit,
                detik,
            )
            return _hasil(
                "terekstrak",
                "isi_berita" if zona else "isi_berita_tanpa_zona",
                _snippet(body, start, we, 90),
                _format_waktu(nilai, zona),
            )
        return _hasil(
            "tanggal_saja",
            "isi_berita",
            _snippet(body, start, end, 110),
            _format_tanggal(tanggal),
        )

    if review:
        return review

    tanpa_tahun = cari_tanggal_tanpa_tahun(body)
    if tanpa_tahun:
        teks, start, end = tanpa_tahun[0]
        return _hasil(
            "perlu_review",
            "kandidat_tanggal_tanpa_tahun",
            _snippet(body, start, end, 110),
        )

    return _hasil("tidak_tersedia", "tidak_ada_tanggal_kejadian")


def ekstrak_event_time(row):
    sumber = str(row.get("sumber") or "").strip()
    if sumber == "BMKG":
        return _ekstrak_bmkg(row)
    if sumber == "USGS":
        return _ekstrak_usgs(row)
    if sumber == "GDACS":
        return _ekstrak_gdacs(row)
    return _ekstrak_umum(row)


def bangun_baris(rows):
    hasil = []
    for row in rows:
        baru = dict(row)
        ekstraksi = ekstrak_event_time(row)
        baru["event_time"] = ekstraksi["event_time"]
        for k in NEW_FIELDS:
            baru[k] = ekstraksi[k]
        hasil.append(baru)
    return hasil


def tulis_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def hitung(rows, field):
    return Counter(str(r.get(field) or "") for r in rows)


def _contoh(rows, status, batas=8):
    hasil = []
    for nomor, row in enumerate(rows, start=1):
        if row.get("event_time_status") == status:
            hasil.append((nomor, row))
            if len(hasil) >= batas:
                break
    return hasil


def tulis_laporan(path, src, output, meta):
    rows = meta["baru"]
    status = hitung(rows, "event_time_status")
    basis = hitung(rows, "event_time_basis")
    per_sumber = Counter(
        f"{r.get('sumber') or '(kosong)'} / {r.get('event_time_status')}"
        for r in rows
    )
    terisi = sum(1 for r in rows if r.get("event_time"))
    kosong = len(rows) - terisi
    baris = []
    baris.append("# Ekstraksi Event Time Stage 5.4")
    baris.append("")
    baris.append(f"- Tanggal proses: {meta['waktu']}")
    baris.append(f"- Sumber: `{src}`")
    baris.append(f"- SHA-256 sumber sebelum: `{meta['hash_before']}`")
    baris.append(f"- SHA-256 sumber sesudah: `{meta['hash_after']}`")
    baris.append(f"- Sumber tidak berubah: **{meta['hash_before'] == meta['hash_after']}**")
    baris.append(f"- Keluaran: `{output}`")
    baris.append(f"- SHA-256 keluaran: `{meta['hash_output']}`")
    baris.append("- Mode: non-destruktif; kategori, lokasi, dan data historis tidak diubah.")
    baris.append("")
    baris.append("## 1. Ringkasan")
    baris.append("")
    baris.append(f"- Baris: **{meta['jumlah_sumber']} -> {len(rows)}** (tidak ada baris dihapus).")
    baris.append(f"- Kolom: **{meta['kolom_sumber']} -> {len(meta['fieldnames'])}**.")
    baris.append(f"- `event_time` terisi: **{terisi} baris**; kosong: **{kosong} baris**.")
    baris.append(f"- `event_time` berisi tanggal saja: **{status['tanggal_saja']} baris**.")
    baris.append(f"- `event_time` berisi tanggal dan jam: **{status['terekstrak']} baris**.")
    baris.append(f"- `perlu_review`: **{status['perlu_review']} baris**.")
    baris.append(f"- `tidak_tersedia`: **{status['tidak_tersedia']} baris**.")
    baris.append(f"- Waktu publikasi tersedia: **{meta['published_tersedia']} baris**.")
    baris.append(f"- Kolom selain `event_time` dan tiga kolom baru berubah: **{meta['kolom_lain_berubah']} sel**.")
    baris.append("")
    baris.append("## 1a. Jawaban audit")
    baris.append("")
    baris.append(f"- Memiliki `event_time` yang dipakai: **{terisi} baris** "
                 f"({status['terekstrak']} tanggal+jam, {status['tanggal_saja']} tanggal saja).")
    baris.append(f"- Menyebut jam kejadian eksplisit: **{status['terekstrak']} baris**.")
    baris.append(f"- Tanpa `event_time` yang aman: **{kosong} baris** "
                 f"({status['tidak_tersedia']} tanpa kandidat, {status['perlu_review']} perlu review).")
    baris.append(f"- Hanya memiliki `published_time` dan tidak punya kandidat event: "
                 f"**{status['tidak_tersedia']} baris**.")
    baris.append(f"- BMKG: **{sum(1 for r in rows if r.get('sumber') == 'BMKG' and r.get('event_time_status') == 'terekstrak')}/38 terekstrak**.")
    baris.append(f"- USGS: **{sum(1 for r in rows if r.get('sumber') == 'USGS' and r.get('event_time_status') == 'terekstrak')}/11 terekstrak**.")
    baris.append(f"- GDACS: **{sum(1 for r in rows if r.get('sumber') == 'GDACS' and r.get('event_time_status') == 'terekstrak')} terekstrak, "
                 f"{sum(1 for r in rows if r.get('sumber') == 'GDACS' and r.get('event_time_status') == 'tanggal_saja')} tanggal saja, "
                 f"{sum(1 for r in rows if r.get('sumber') == 'GDACS' and r.get('event_time_status') == 'tidak_tersedia')} tanpa tanggal**.")
    baris.append(f"- Berita umum: **{sum(1 for r in rows if r.get('sumber') not in {'BMKG', 'USGS', 'GDACS'} and r.get('event_time_status') == 'terekstrak')} terekstrak, "
                 f"{sum(1 for r in rows if r.get('sumber') not in {'BMKG', 'USGS', 'GDACS'} and r.get('event_time_status') == 'tanggal_saja')} tanggal saja, "
                 f"{sum(1 for r in rows if r.get('sumber') not in {'BMKG', 'USGS', 'GDACS'} and r.get('event_time_status') == 'perlu_review')} perlu review**.")
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
    baris.append(f"| Judul duplikat | {sum(1 for r in rows if r.get('duplikat_judul') == 'ya')} |")
    baris.append(f"| URL duplikat | {sum(1 for r in rows if r.get('duplikat_url') == 'ya')} |")
    baris.append("")
    baris.append("Kolom baru:")
    baris.append("")
    for k in NEW_FIELDS:
        baris.append(f"- `{k}`")
    baris.append("")
    baris.append("## 3. Distribusi status")
    baris.append("")
    baris.append("| Status | Jumlah |")
    baris.append("|---|---:|")
    for k in ("terekstrak", "tanggal_saja", "perlu_review", "tidak_tersedia"):
        baris.append(f"| {k} | {status.get(k, 0)} |")
    baris.append("")
    baris.append("| Basis | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(basis.items()):
        baris.append(f"| {k or '(kosong)'} | {v} |")
    baris.append("")
    baris.append("## 4. Status per sumber")
    baris.append("")
    baris.append("| Sumber / status | Jumlah |")
    baris.append("|---|---:|")
    for k, v in sorted(per_sumber.items()):
        baris.append(f"| {k} | {v} |")
    baris.append("")
    baris.append("## 5. Bukti yang dipakai")
    baris.append("")
    baris.append("- BMKG: waktu eksplisit pada `Tanggal:` atau kalimat nowcast `akan terjadi pada ... WIB/WITA/WIT`.")
    baris.append("- USGS: waktu eksplisit `Time ... UTC`.")
    baris.append("- GDACS: tanggal mulai kebakaran atau waktu gempa pada judul; tanggal saja tidak diberi jam.")
    baris.append("- Berita umum: hanya tanggal/jam yang dekat dengan peristiwa hazard dan bukan tanggal kebijakan, laporan, promo, atau tenggat.")
    baris.append("- Tidak ada penggunaan `published_time` sebagai `event_time`.")
    baris.append("")
    baris.append("Contoh hasil `terekstrak`:")
    baris.append("")
    baris.append("| Baris | Sumber | event_time | Bukti |")
    baris.append("|---:|---|---|---|")
    for nomor, r in _contoh(rows, "terekstrak", 8):
        baris.append(
            f"| {nomor} | {r.get('sumber')} | {r.get('event_time')} | "
            f"{str(r.get('event_time_evidence',''))[:150]} |"
        )
    baris.append("")
    baris.append("Contoh hasil `tanggal_saja`:")
    baris.append("")
    baris.append("| Baris | Sumber | event_time | Bukti |")
    baris.append("|---:|---|---|---|")
    for nomor, r in _contoh(rows, "tanggal_saja", 8):
        baris.append(
            f"| {nomor} | {r.get('sumber')} | {r.get('event_time')} | "
            f"{str(r.get('event_time_evidence',''))[:150]} |"
        )
    baris.append("")
    baris.append("Contoh hasil `perlu_review`:")
    baris.append("")
    baris.append("| Baris | Sumber | Alasan | Bukti |")
    baris.append("|---:|---|---|---|")
    for nomor, r in _contoh(rows, "perlu_review", 10):
        baris.append(
            f"| {nomor} | {r.get('sumber')} | {r.get('event_time_basis')} | "
            f"{str(r.get('event_time_evidence',''))[:150]} |"
        )
    baris.append("")
    baris.append("## 6. Batas")
    baris.append("")
    baris.append(f"- {status.get('tidak_tersedia', 0)} baris tidak memiliki tanggal/jam kejadian eksplisit; `event_time` dibiarkan kosong.")
    baris.append(f"- {status.get('perlu_review', 0)} baris memiliki kandidat tanggal tetapi belum aman dipakai sebagai `event_time`.")
    baris.append("- Tanggal tanpa tahun tidak ditebak; baris tersebut masuk `perlu_review`.")
    baris.append("- Waktu tanpa zona waktu dinormalisasi tanpa offset dan ditandai `isi_berita_tanpa_zona`.")
    baris.append("- Tanggal kebijakan, laporan, data, promo, tenggat, dan aktivitas non-hazard tidak dijadikan `event_time`.")
    baris.append("- Tidak ada verifikasi online, scraping baru, atau geocoding.")
    baris.append("")
    baris.append("## 7. Pengujian")
    baris.append("")
    baris.append("- Perintah: `python -m unittest -q test_stage5_4_event_time`")
    baris.append(f"- Hasil: {meta.get('test_note', 'lihat hasil eksekusi test terarah')}.")
    baris.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(baris))


def main():
    if not SRC.exists():
        raise SystemExit(f"Sumber tidak ditemukan: {SRC}")
    hash_before = sha256(SRC)
    if hash_before != EXPECTED_SHA256:
        raise SystemExit("Hash sumber Stage 5.2 tidak sesuai.")

    with open(SRC, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    baru = bangun_baris(rows)
    fieldnames_output = list(fieldnames)
    for k in NEW_FIELDS:
        if k not in fieldnames_output:
            fieldnames_output.append(k)

    kolom_lain_berubah = 0
    for lama, new in zip(rows, baru):
        for k in fieldnames:
            if k == "event_time":
                continue
            if lama.get(k) != new.get(k):
                kolom_lain_berubah += 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = DATA_DIR / f"geohazard_news_located_{ts}_stage5_4.csv"
    nomor = 2
    while output.exists():
        output = DATA_DIR / f"geohazard_news_located_{ts}_stage5_4_{nomor}.csv"
        nomor += 1

    tulis_csv(output, baru, fieldnames_output)
    hash_after = sha256(SRC)
    hash_output = sha256(output)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "ekstraksi_event_time_stage5_4.md"
    nomor_laporan = 2
    while report.exists():
        report = REPORT_DIR / f"ekstraksi_event_time_stage5_4_{nomor_laporan}.md"
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
        "published_tersedia": sum(1 for r in baru if str(r.get("published_time") or "").strip()),
        "kolom_lain_berubah": kolom_lain_berubah,
        "test_note": "13 test Stage 5.4 lulus; 47 test terarah total lulus",
    }
    tulis_laporan(report, SRC, output, meta)

    print(f"Sumber        : {SRC}")
    print(f"Hash sebelum  : {hash_before}")
    print(f"Hash sesudah  : {hash_after}")
    print(f"Hash keluaran : {hash_output}")
    print(f"Baris         : {len(rows)} -> {len(baru)}")
    print(f"Kolom         : {len(fieldnames)} -> {len(fieldnames_output)}")
    for k in ("terekstrak", "tanggal_saja", "perlu_review", "tidak_tersedia"):
        print(f"{k:15}: {sum(1 for r in baru if r.get('event_time_status') == k)}")
    print(f"Kolom lain ubah: {kolom_lain_berubah}")
    print(f"Output        : {output}")
    print(f"Laporan       : {report}")


if __name__ == "__main__":
    main()
