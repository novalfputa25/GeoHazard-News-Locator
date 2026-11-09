# ============================================================
# GEOHAZARD NEWS LOCATOR
# LOCATION EXTRACTOR
# ============================================================
#
# Mengisi kolom lokasi pada CSV hasil scraper berdasarkan teks
# berita (judul + isi_berita):
#   provinsi, kabupaten_kota, kecamatan, desa_kelurahan,
#   dusun_kampung, rw, rt, alamat_detail
#
# Sumber acuan wilayah: data/wilayah_gazetteer.json
# (dibuat oleh build_gazetteer.py) + 38 provinsi di
# wilayah_reference.py.
#
# Bila gazetteer belum ada, script tetap jalan mode
# "pola saja" (hanya mencocokkan kata kunci Kabupaten/Kota/
# Kecamatan/Desa/... di dalam teks).
#
# Jalankan:
#   python location_extractor.py
# ============================================================

import csv
import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote_plus

from wilayah_reference import PROVINCES, PROVINCE_ALIASES

INPUT_FILE = Path("data/geohazard_news.csv")
GAZETTEER_FILE = Path("data/wilayah_gazetteer.json")
OUTPUT_FILE = Path("data/geohazard_news_located.csv")
OUTPUT_DIR = Path("data")
OUTPUT_PREFIX = "geohazard_news_located_"
INPUT_PREFIX = "geohazard_news_scrape_"

LOKASI_FIELDS = [
    "provinsi",
    "kabupaten_kota",
    "kecamatan",
    "desa_kelurahan",
    "dusun_kampung",
    "rw",
    "rt",
    "alamat_detail",
]

KOORDINAT_FIELDS = [
    "latitude",
    "longitude",
    "koordinat_status",
    "koordinat_sumber",
    "koordinat_verifikasi",
    "koordinat_domain",
]

FIELDNAMES = [
    "judul",
    "published_time",
    "event_time",
    "sumber",
    "source_id",
    "kategori",
    *LOKASI_FIELDS,
    "url",
    "isi_berita",
    "duplicate_of",
    "duplicate_reason",
    *KOORDINAT_FIELDS,
]

# Kata sambung/umum yang sering "menempel" di belakang nama tempat.
EKOR_DIBUANG = {
    "dan", "di", "yang", "pada", "dengan", "untuk", "ini", "itu",
    "tersebut", "sebagai", "akibat", "karena", "warga", "ke", "dari",
    "oleh", "saat", "telah", "masih", "kembali", "juga", "agar",
    "bisa", "dapat", "akan", "tidak", "belum", "sekitar", "hingga",
    "sampai", "sejak", "setelah", "sebelum", "diduga", "penyebab",
    "senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu",
    "januari", "februari", "maret", "april", "mei", "juni", "juli",
    "agustus", "september", "oktober", "november", "desember",
    "pagi", "siang", "sore", "malam", "hari", "wib", "wita", "wit",
}

# Nama wilayah yang terlalu umum -> rawan salah cocok.
BARE_DIBLOKIR = {
    "kota", "tanah", "laut", "buru", "besar", "barat", "timur",
    "utara", "selatan", "tengah", "hulu", "hilir", "pulau",
    "kepulauan", "induk", "ibu", "sunda", "bangka", "seram",
    "batu", "manggarai",
}

# Bentuk menempel dari judul BMKG. Alias hanya menormalkan ejaan;
# nama wilayah tetap diambil dari gazetteer, bukan dikarang.
ALIAS_TOPONIM = {
    "acehjaya": "aceh jaya",
    "sumbabaratdaya": "sumba barat daya",
}

ALAMAT_PALSU = re.compile(
    r"^(?:jl\.?|jalan)\s+(?:terus|dievakuasi|pemberdayaan|"
    r"desa\s+terpencil|ditutup)\b",
    re.I,
)


# ------------------------------------------------------------
# NORMALISASI
# ------------------------------------------------------------

def normal(kunci):
    kunci = kunci.lower()
    kunci = re.sub(r"[^a-z0-9 ]", " ", kunci)
    return re.sub(r"\s+", " ", kunci).strip()


def buang_ekor(nama):
    kata = nama.split()
    while kata and kata[-1].lower() in EKOR_DIBUANG:
        kata.pop()
    return " ".join(kata)


def bersihkan_nama(nama):
    nama = re.sub(r"\s+", " ", nama).strip(" ,.;:-")
    return buang_ekor(nama)


def rapikan_alamat(alamat):
    alamat = re.sub(r"\s+", " ", str(alamat or "")).strip(" ,.;:-")
    if ALAMAT_PALSU.search(alamat):
        return ""

    m = re.match(r"^(Jl\.?|Jalan)\s+(.+)$", alamat, re.I)
    if not m:
        return ""
    prefix, sisa = m.group(1), m.group(2)

    kata = []
    for bagian in sisa.split():
        bagian = bagian.strip(" ,.;:-")
        if not bagian or not bagian[0].isupper():
            break
        kata.append(bagian)
    if not kata:
        return ""

    hasil = bersihkan_nama(f"{prefix} {' '.join(kata)}")
    if ALAMAT_PALSU.search(hasil):
        return ""
    return hasil


# ------------------------------------------------------------
# GAZETTEER
# ------------------------------------------------------------

def muat_gazetteer():
    if not GAZETTEER_FILE.exists():
        print("  (gazetteer tidak ada - mode pola saja)")
        return {}, [], {}
    with open(GAZETTEER_FILE, encoding="utf-8") as f:
        data = json.load(f)

    exact = {}
    bare = {}
    for kab in data.get("kabupaten_kota", []):
        nama = kab["nama"]
        prov = kab["provinsi"]
        tipe = kab["tipe"]
        exact[normal(nama)] = (nama, prov)

        bare_nama = re.sub(r"^(kabupaten|kota)\s+", "", nama, flags=re.I)
        kunci = normal(bare_nama)
        bare.setdefault(kunci, []).append((nama, prov, tipe))

    for alias, kanonik in ALIAS_TOPONIM.items():
        if kanonik in bare:
            bare.setdefault(alias, []).extend(bare[kanonik])

    # Kunci untuk pemindaian teks, diurutkan terpanjang dulu
    kunci_pindai = sorted(
        (k for k in bare if len(k) >= 4 and k not in BARE_DIBLOKIR),
        key=len,
        reverse=True,
    )
    return exact, bare, {k: bare[k] for k in kunci_pindai}


# ------------------------------------------------------------
# POLA EKSPLISIT
# ------------------------------------------------------------

POLA_RW = re.compile(r"\bRW\s*[-:.]?\s*0*(\d{1,3})\b", re.I)
POLA_RT = re.compile(r"\bRT\s*[-:.]?\s*0*(\d{1,3})\b", re.I)
POLA_ALAMAT = re.compile(
    r"\b((?:Jl|Jalan)\.?\s+[A-Z][\w' .\-]{2,60}?)(?=[,.;]|\s+(?:RT|RW|Kel|Kec|Kab)\b|$)"
)

EVENT_RE = re.compile(
    r"\b(?:gempa(?:bumi)?|gempabumi|erupsi|letusan|tsunami|longsor|"
    r"likuefaksi|liquefaction|banjir|hujan|cuaca|angin|puting beliung|"
    r"kekeringan|kebakaran|karhutla|asap|kabut asap|terbakar|abrasi|"
    r"akresi|penurunan muka tanah|land subsidence|semburan|mud volcano|"
    r"abu vulkanik|evakuasi|"
    r"dirasakan|mengguncang|guncang|melanda|menimpa|menghantam|merusak|merendam|"
    r"menggenangi|berpusat|pusat gempa|magnitudo|magnitud|kekuatan)\b",
    re.I,
)

EVENT_KUAT_RE = re.compile(
    r"\b(?:gempa(?:bumi)?|gempabumi|erupsi|letusan|tsunami|longsor|"
    r"likuefaksi|liquefaction|banjir|hujan|cuaca|angin|puting beliung|"
    r"kekeringan|kebakaran|karhutla|asap|kabut asap|terbakar|abrasi|"
    r"akresi|penurunan muka tanah|land subsidence|semburan|mud volcano|"
    r"abu vulkanik|dirasakan|mengguncang|guncang|melanda|menimpa|"
    r"menghantam|merusak|merendam|menggenangi|berpusat|pusat gempa|"
    r"magnitudo|magnitud|kekuatan)\b",
    re.I,
)

NON_EVENT_RE = re.compile(
    r"\b(?:kantor|narasumber|juru bicara|kepala|menteri|gubernur|bupati|"
    r"walikota|wawancara|konferensi|seminar|rapat|sosialisasi|edukasi|"
    r"mitigasi|kunjungan|markas|balai|gedung|hotel|kampus|sekolah|wisma|"
    r"pendopo|istana|prakiraan|ramalan|proyeksi|polda|polres|polresta|"
    r"polsek|mapolres|mapolresta|pemkab|pemkot|pemprov|pemda|dprd|"
    r"pengadilan|kejaksaan|kementerian)\b",
    re.I,
)

SUMBER_ORG_RE = re.compile(
    r"\b(?:bmkg|bnpb|pvmbg|bpptkg|badan meteorologi|badan geologi|"
    r"badan nasional penanggulangan bencana|pusat vulkanologi)\b",
    re.I,
)

PERBANDINGAN_RE = re.compile(
    r"\b(?:dibandingkan|seperti|sebelumnya|tahun lalu|dulu|pernah|"
    r"historis|masa lalu)\b",
    re.I,
)

PRAKIRAAN_RE = re.compile(
    r"\b(?:prakiraan|ramalan|proyeksi|memprakirakan|memperkirakan|"
    r"modifikasi cuaca)\b",
    re.I,
)

NON_KEJADIAN_KUAT_RE = re.compile(
    r"\b(?:korupsi|saham|dana bencana|dana itu|anggaran bencana|"
    r"temuan kpk|peneliti|tanam mangrove|"
    r"penanaman mangrove|mencegah abrasi|kontainer|truk|"
    r"kecelakaan|tabrakan)\b",
    re.I,
)

TAHUN_LAMA_RE = re.compile(r"\btahun\s+(?:19|20)\d{2}\b", re.I)

EVENT_DEKAT_RE = re.compile(
    r"\b(?:berpusat|terjadi|melanda|mengguncang|menimpa|menghantam|"
    r"merusak|merendam|menggenangi|pusat gempa|lokasi|di)\s+"
    r"(?:kecamatan|kabupaten|kota|desa|kelurahan|nagari|gampong|dusun|"
    r"dukuh|kampung|wilayah|daerah|sekitar)?\s*$",
    re.I,
)

POLA_KOORD_BMKG_URL = re.compile(r"[?&]lat=([^&]+).*?[?&]lon=([^&]+)", re.I)
POLA_KOORD_BMKG_ISI = re.compile(
    r"Koordinat\s*:\s*(-?\d+(?:[.,]\d+)?)\s*,\s*(-?\d+(?:[.,]\d+)?)",
    re.I,
)
POLA_KOORD_USGS = re.compile(
    r"Location\s+(\d+(?:\.\d+)?)\s*[^\s\w]?\s*([NS])\s+"
    r"(\d+(?:\.\d+)?)\s*[^\s\w]?\s*([EW])",
    re.I,
)


def _pola_frasa(kata_kunci, maks_kata=4):
    return re.compile(
        rf"\b(?i:{kata_kunci})\b[\s.\-]+"
        rf"((?:[A-Z][\w']+)(?:\s+[A-Z][\w']+){{0,{maks_kata - 1}}})"
    )


def cari_frasa(teks, kata_kunci, maks_kata=4):
    m = _pola_frasa(kata_kunci, maks_kata).search(teks)
    if not m:
        return ""
    return bersihkan_nama(m.group(1))


def cari_frasa_semua(teks, kata_kunci, maks_kata=4):
    for m in _pola_frasa(kata_kunci, maks_kata).finditer(teks):
        nama = bersihkan_nama(m.group(1))
        if nama:
            yield nama, m.start(), m.end()


def _batas_klausa(teks, posisi):
    kiri = 0
    for m in re.finditer(r"[.!?;](?=\s|$)", teks[:posisi]):
        kiri = m.end()
    kanan = len(teks)
    for m in re.finditer(r"[.!?;](?=\s|$)", teks[posisi:]):
        kanan = posisi + m.start()
        break
    return kiri, kanan


def _konteks(teks, start, end):
    kiri, kanan = _batas_klausa(teks, start)
    return teks[kiri:kanan], teks[kiri:start]


def _ada_kejadian(teks, kuat=False):
    pola = EVENT_KUAT_RE if kuat else EVENT_RE
    return bool(pola.search(teks or ""))


def _konteks_non_kejadian(prefix, sumber):
    if PERBANDINGAN_RE.search(prefix) or PRAKIRAAN_RE.search(prefix):
        return True
    if sumber == "isi" and TAHUN_LAMA_RE.search(prefix):
        return True

    non_event = [
        m.end() for m in NON_EVENT_RE.finditer(prefix)
    ] + [
        m.end() for m in SUMBER_ORG_RE.finditer(prefix)
    ]
    if not non_event:
        return False

    event = [m.end() for m in EVENT_RE.finditer(prefix)]
    return max(non_event) > max(event, default=-1)


def _skor_kandidat(prefix, eksplisit, sumber):
    skor = 10 if sumber == "judul" else 0
    if eksplisit:
        skor += 8
    if EVENT_DEKAT_RE.search(prefix[-45:]):
        skor += 4
    if sumber == "isi":
        event = list(EVENT_RE.finditer(prefix))
        if event:
            jarak = len(prefix) - event[-1].end()
            skor += max(0, 4 - jarak // 20)
    return skor


def _buat_kandidat(nama, prov, start, end, sumber, eksplisit, tipe, teks):
    if not nama or NON_KEJADIAN_KUAT_RE.search(teks):
        return None
    klausa, prefix = _konteks(teks, start, end)
    if sumber == "judul":
        if not _ada_kejadian(teks):
            return None
    elif not _ada_kejadian(klausa, kuat=True):
        return None
    if _konteks_non_kejadian(prefix, sumber):
        return None
    return {
        "nama": nama,
        "prov": prov,
        "start": start,
        "tipe": tipe,
        "sumber": sumber,
        "skor": _skor_kandidat(prefix, eksplisit, sumber),
    }


def _kandidat_sama_start(kandidat, teks):
    sebelum = teks[max(0, kandidat[0]["start"] - 20):kandidat[0]["start"]].lower()
    if re.search(r"\b(kabupaten|kab)\b", sebelum):
        for k in kandidat:
            if k["tipe"] == "kabupaten":
                return k
    if re.search(r"\b(kota|kot)\b", sebelum):
        for k in kandidat:
            if k["tipe"] == "kota":
                return k
    if len(kandidat) == 1:
        return kandidat[0]

    provinsi = {k["prov"] for k in kandidat if k["prov"]}
    if len(provinsi) == 1:
        return {
            "nama": "",
            "prov": next(iter(provinsi)),
            "start": kandidat[0]["start"],
            "tipe": "ambigu",
            "sumber": kandidat[0]["sumber"],
            "skor": kandidat[0]["skor"],
        }
    return None


def pilih_kandidat(kandidat, teks, posisi):
    group = [
        {
            "nama": nama,
            "prov": prov,
            "start": posisi,
            "tipe": tipe,
            "sumber": "isi",
            "skor": 0,
        }
        for nama, prov, tipe in kandidat
    ]
    hasil = _kandidat_sama_start(group, teks)
    if not hasil:
        return "", ""
    return hasil["nama"], hasil["prov"]


def _pilih_terbaik(kandidat, teks):
    kandidat = [k for k in kandidat if k]
    if not kandidat:
        return None

    unik = {}
    for k in kandidat:
        kunci = (k["nama"], k["start"], k["sumber"])
        if kunci not in unik or k["skor"] > unik[kunci]["skor"]:
            unik[kunci] = k
    kandidat = list(unik.values())

    skor_max = max(k["skor"] for k in kandidat)
    teratas = [k for k in kandidat if k["skor"] == skor_max]
    posisi = sorted({k["start"] for k in teratas})

    if len(posisi) == 1:
        group = [k for k in teratas if k["start"] == posisi[0]]
        return _kandidat_sama_start(group, teks)

    nama = {normal(k["nama"]) for k in teratas if k["nama"]}
    if len(nama) == 1:
        return teratas[0]

    provinsi = {k["prov"] for k in teratas if k["prov"]}
    if len(provinsi) == 1:
        return {
            "nama": "",
            "prov": next(iter(provinsi)),
            "start": teratas[0]["start"],
            "tipe": "ambigu",
            "sumber": teratas[0]["sumber"],
            "skor": skor_max,
        }
    return None


def _kandidat_eksplisit(teks, sumber, exact):
    hasil = []
    for nama, start, end in cari_frasa_semua(teks, r"Kabupaten|Kab"):
        kandidat = exact.get(normal(f"kabupaten {nama}"))
        if kandidat:
            nama_kab, prov = kandidat
        else:
            nama_kab, prov = f"Kabupaten {nama}", ""
        k = _buat_kandidat(
            nama_kab, prov, start, end, sumber, True, "kabupaten", teks
        )
        if k:
            hasil.append(k)

    for nama, start, end in cari_frasa_semua(teks, r"Kota"):
        kandidat = exact.get(normal(f"kota {nama}"))
        if not kandidat:
            continue
        k = _buat_kandidat(
            kandidat[0], kandidat[1], start, end, sumber, True, "kota", teks
        )
        if k:
            hasil.append(k)
    return hasil


@lru_cache(maxsize=8)
def _pola_bare(kunci):
    urut = sorted(kunci, key=len, reverse=True)
    return re.compile(
        r"\b(?:" + "|".join(re.escape(k) for k in urut) + r")\b",
        re.I,
    )


def _kandidat_bare(teks, sumber, bare_index):
    hasil = []
    for m in _pola_bare(tuple(bare_index)).finditer(teks):
        if not teks[m.start():m.start() + 1].isupper():
            continue
        kunci = m.group(0).lower()
        if kunci not in bare_index:
            continue
        sebelum = teks[max(0, m.start() - 20):m.start()]
        if (
            kunci not in ALIAS_TOPONIM
            and re.search(r"[A-Z]{3,}\s*[-–—]\s*$", sebelum)
            and not re.search(r"\b(?:kabupaten|kab|kota|kot)\b", sebelum, re.I)
        ):
            continue
        if m.group(0).isupper() and not re.search(
            r"\b(?:kabupaten|kab|kota|kot)\b", sebelum, re.I
        ):
            sesudah = teks[m.end():]
            m_ekor = re.match(r"\s*[-–—]?\s*([A-Z]{2,})\b", sesudah)
            if m_ekor and kunci not in ALIAS_TOPONIM:
                if normal(m_ekor.group(1)) not in _peta_provinsi():
                    continue
        for nama, prov, tipe in bare_index[kunci]:
            k = _buat_kandidat(
                nama, prov, m.start(), m.end(), sumber, False, tipe, teks
            )
            if k:
                hasil.append(k)
    return hasil


def cocok_gazetteer(teks, bare_index):
    hasil = _pilih_terbaik(_kandidat_bare(teks, "isi", bare_index), teks)
    if not hasil:
        return "", ""
    return hasil["nama"], hasil["prov"]


def _peta_provinsi():
    peta = {normal(p): p for p in PROVINCES}
    peta.update(PROVINCE_ALIASES)
    peta.update({
        "kep. riau": "Kepulauan Riau",
        "kep riau": "Kepulauan Riau",
        "kep. bangka belitung": "Kepulauan Bangka Belitung",
        "kep bangka belitung": "Kepulauan Bangka Belitung",
    })
    return peta


def _kandidat_provinsi(teks, sumber):
    peta = _peta_provinsi()
    hasil = []
    for kunci in sorted(peta, key=len, reverse=True):
        for m in re.finditer(rf"\b{re.escape(kunci)}\b", teks, re.I):
            if kunci == "papua":
                sesudah = teks[m.end():m.end() + 20]
                if re.match(r"\s+nugini\b", sesudah, re.I):
                    continue
            k = _buat_kandidat(
                peta[kunci], peta[kunci], m.start(), m.end(),
                sumber, False, "provinsi", teks,
            )
            if k:
                hasil.append(k)
    return hasil


def cari_provinsi(teks):
    peta = _peta_provinsi()
    for kunci in sorted(peta, key=len, reverse=True):
        if re.search(rf"\b{re.escape(kunci)}\b", teks, re.I):
            return peta[kunci]
    return ""


# ------------------------------------------------------------
# EKSTRAKSI UTAMA
# ------------------------------------------------------------

def _hasil_kabupaten(judul, isi, exact, bare_index):
    kandidat_judul = (
        _kandidat_eksplisit(judul, "judul", exact)
        + _kandidat_bare(judul, "judul", bare_index)
    )
    hasil_judul = _pilih_terbaik(kandidat_judul, judul)
    if hasil_judul and hasil_judul["nama"]:
        return hasil_judul

    kandidat_isi = (
        _kandidat_eksplisit(isi, "isi", exact)
        + _kandidat_bare(isi, "isi", bare_index)
    )
    hasil_isi = _pilih_terbaik(kandidat_isi, isi)
    if hasil_isi and hasil_isi["nama"]:
        return hasil_isi
    return hasil_judul or hasil_isi


def _hasil_provinsi(judul, isi, kabupaten, provinsi_judul=None):
    if provinsi_judul is None:
        provinsi_judul = _pilih_terbaik(
            _kandidat_provinsi(judul, "judul"), judul
        )

    if provinsi_judul and provinsi_judul["nama"]:
        if (
            kabupaten
            and kabupaten["prov"]
            and kabupaten["prov"] != provinsi_judul["nama"]
        ):
            return provinsi_judul["nama"]
        if kabupaten and kabupaten["prov"]:
            return kabupaten["prov"]
        return provinsi_judul["nama"]

    if kabupaten and kabupaten["prov"]:
        return kabupaten["prov"]

    hasil_isi = _pilih_terbaik(_kandidat_provinsi(isi, "isi"), isi)
    if hasil_isi and hasil_isi["nama"]:
        return hasil_isi["nama"]
    return ""


def _cari_sub_lokasi(judul, isi, kata_kunci):
    for teks, sumber in ((judul, "judul"), (isi, "isi")):
        kandidat = []
        for nama, start, end in cari_frasa_semua(teks, kata_kunci):
            k = _buat_kandidat(
                nama, "", start, end, sumber, True, "sub", teks
            )
            if k:
                kandidat.append(k)
        hasil = _pilih_terbaik(kandidat, teks)
        if hasil and hasil["nama"]:
            return hasil["nama"]
    return ""


def ekstrak_lokasi(judul, isi, exact, bare, bare_index):
    judul = str(judul or "")
    isi = str(isi or "")
    teks = f"{judul}. {isi}" if judul and isi else f"{judul}{isi}"

    hasil = {k: "" for k in LOKASI_FIELDS}
    kabupaten = _hasil_kabupaten(judul, isi, exact, bare_index)
    provinsi_judul = _pilih_terbaik(_kandidat_provinsi(judul, "judul"), judul)
    if (
        kabupaten
        and provinsi_judul
        and provinsi_judul["nama"]
        and kabupaten["prov"]
        and kabupaten["prov"] != provinsi_judul["nama"]
    ):
        kabupaten = None
    if kabupaten:
        hasil["kabupaten_kota"] = kabupaten["nama"]
        hasil["provinsi"] = kabupaten["prov"]
    hasil["provinsi"] = _hasil_provinsi(
        judul, isi, kabupaten, provinsi_judul
    )

    hasil["kecamatan"] = _cari_sub_lokasi(judul, isi, r"Kecamatan|Kec")
    hasil["desa_kelurahan"] = _cari_sub_lokasi(
        judul, isi, r"Kelurahan|Desa|Nagari|Gampong|Kel"
    )
    hasil["dusun_kampung"] = _cari_sub_lokasi(
        judul, isi, r"Dusun|Dukuh|Kampung"
    )

    m = POLA_RW.search(teks)
    if m:
        hasil["rw"] = m.group(1)
    m = POLA_RT.search(teks)
    if m:
        hasil["rt"] = m.group(1)
    m = POLA_ALAMAT.search(teks)
    if m:
        hasil["alamat_detail"] = rapikan_alamat(m.group(1))

    return hasil


def _angka_koordinat(nilai):
    teks = unquote_plus(str(nilai)).strip().upper()
    m = re.match(r"^(-?\d+(?:[.,]\d+)?)\s*(LS|LU|BT|BB)?$", teks)
    if not m:
        return None
    try:
        angka = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    arah = m.group(2)
    if arah in {"LS", "BB"}:
        angka = -abs(angka)
    elif arah in {"LU", "BT"}:
        angka = abs(angka)
    return angka


def _format_koordinat(nilai):
    teks = f"{nilai:.6f}".rstrip("0").rstrip(".")
    return "0" if teks in {"", "-0"} else teks


def _koordinat_valid(latitude, longitude):
    return (
        latitude is not None
        and longitude is not None
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def _domain_koordinat(latitude, longitude):
    if -11.0 <= latitude <= 6.0 and 94.0 <= longitude <= 142.0:
        return "indonesia"
    return "luar_indonesia"


def _hasil_koordinat(latitude, longitude, sumber):
    if not _koordinat_valid(latitude, longitude):
        return None
    return {
        "latitude": _format_koordinat(latitude),
        "longitude": _format_koordinat(longitude),
        "koordinat_status": "tersedia_sumber",
        "koordinat_sumber": sumber,
        "koordinat_verifikasi": "belum_diverifikasi",
        "koordinat_domain": _domain_koordinat(latitude, longitude),
    }


def ekstrak_koordinat(row):
    url = str(row.get("url") or "")
    isi = str(row.get("isi_berita") or "")

    m = POLA_KOORD_BMKG_URL.search(url)
    if m:
        hasil = _hasil_koordinat(
            _angka_koordinat(m.group(1)),
            _angka_koordinat(m.group(2)),
            "URL BMKG",
        )
        if hasil:
            return hasil

    m = POLA_KOORD_BMKG_ISI.search(isi)
    if m:
        hasil = _hasil_koordinat(
            _angka_koordinat(m.group(1)),
            _angka_koordinat(m.group(2)),
            "isi BMKG",
        )
        if hasil:
            return hasil

    m = POLA_KOORD_USGS.search(isi)
    if m:
        try:
            latitude = float(m.group(1))
            longitude = float(m.group(3))
        except ValueError:
            latitude = longitude = None
        if latitude is not None and m.group(2).upper() == "S":
            latitude = -latitude
        if longitude is not None and m.group(4).upper() == "W":
            longitude = -longitude
        hasil = _hasil_koordinat(latitude, longitude, "isi USGS")
        if hasil:
            return hasil

    return {
        "latitude": "",
        "longitude": "",
        "koordinat_status": "tidak_ada",
        "koordinat_sumber": "",
        "koordinat_verifikasi": "tidak_ada",
        "koordinat_domain": "tidak_diketahui",
    }


# ------------------------------------------------------------
# PROGRAM UTAMA
# ------------------------------------------------------------

def buat_output_path(now=None):
    waktu = now or datetime.now(timezone.utc)
    if waktu.tzinfo is not None:
        waktu = waktu.astimezone(timezone.utc)
    stamp = waktu.strftime("%Y%m%dT%H%M%SZ")
    path = OUTPUT_DIR / f"{OUTPUT_PREFIX}{stamp}.csv"
    nomor = 2
    while path.exists():
        path = OUTPUT_DIR / f"{OUTPUT_PREFIX}{stamp}_{nomor}.csv"
        nomor += 1
    return path


def pilih_input_file():
    if OUTPUT_DIR.exists():
        kandidat = sorted(
            OUTPUT_DIR.glob(f"{INPUT_PREFIX}*.csv"),
            key=lambda p: p.name,
            reverse=True,
        )
        if kandidat:
            return kandidat[0]
    return INPUT_FILE


def _fieldnames_output(fieldnames):
    hasil = list(fieldnames or [])
    for k in [*LOKASI_FIELDS, *KOORDINAT_FIELDS]:
        if k not in hasil:
            hasil.append(k)
    return hasil or list(FIELDNAMES)


def baca_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return rows, fieldnames


def main():
    print("=" * 70)
    print("GEOHAZARD NEWS LOCATOR")
    print("LOCATION EXTRACTOR")
    print("=" * 70)

    input_file = pilih_input_file()
    if not input_file.exists():
        print(f"\nERROR: file tidak ditemukan: {input_file}")
        print("Jalankan rss_scraper.py terlebih dahulu.")
        return

    print(f"\nMemuat gazetteer: {GAZETTEER_FILE}")
    exact, bare, bare_index = muat_gazetteer()

    print(f"Membaca data    : {input_file}")
    rows, fieldnames_input = baca_csv(input_file)
    fieldnames = _fieldnames_output(fieldnames_input)
    print(f"Jumlah baris    : {len(rows)}")

    for row in rows:
        lokasi = ekstrak_lokasi(
            row.get("judul", ""),
            row.get("isi_berita", ""),
            exact, bare, bare_index,
        )
        row.update(lokasi)
        row.update(ekstrak_koordinat(row))

    output_file = buat_output_path()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        penulis = csv.DictWriter(f, fieldnames=fieldnames)
        penulis.writeheader()
        for row in rows:
            penulis.writerow({k: row.get(k, "") for k in fieldnames})

    print("\n" + "=" * 70)
    print("KOLOM LOKASI TERISI")
    print("=" * 70)
    for k in LOKASI_FIELDS:
        jumlah = sum(1 for row in rows if row.get(k))
        persen = jumlah / len(rows) * 100 if rows else 0
        print(f"{k:<18}: {jumlah:>4} baris ({persen:.1f}%)")

    jumlah_koordinat = sum(
        1 for row in rows if row.get("koordinat_status") == "tersedia_sumber"
    )
    persen = jumlah_koordinat / len(rows) * 100 if rows else 0
    print(f"{'koordinat':<18}: {jumlah_koordinat:>4} baris ({persen:.1f}%)")

    print("\n" + "=" * 70)
    print("TOP 15 PROVINSI")
    print("=" * 70)
    hitung = {}
    for row in rows:
        provinsi = row.get("provinsi", "")
        if provinsi:
            hitung[provinsi] = hitung.get(provinsi, 0) + 1
    for prov, jumlah in sorted(hitung.items(), key=lambda x: -x[1])[:15]:
        print(f"{prov:<30}: {jumlah}")

    print("\n" + "=" * 70)
    print("SELESAI")
    print("=" * 70)
    print(f"File hasil: {output_file}")


if __name__ == "__main__":
    main()
