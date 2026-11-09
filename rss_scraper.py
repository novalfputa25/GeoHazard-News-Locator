# ============================================================
# GEOHAZARD NEWS LOCATOR
# SCRAPER RSS / ATOM
# ============================================================
#
# Membaca daftar sumber dari feeds.py, mengambil berita dari
# RSS/Atom serta data gempa BMKG (XML), lalu menyimpannya ke
# CSV dengan skema kolom yang sama seperti pipeline lama.
#
# Kolom lokasi (provinsi ... alamat_detail) sengaja dibiarkan
# kosong karena RSS tidak selalu memuat lokasi terstruktur;
# pengisian lokasi menjadi tugas tahap berikutnya (locator).
#
# Jalankan:
#   python rss_scraper.py
# ============================================================

import csv
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

import feedparser
import requests
from bs4 import BeautifulSoup

from feeds import FEEDS, get_active_feeds
from category_detector import detect_category


# ------------------------------------------------------------
# KONFIGURASI
# ------------------------------------------------------------

OUTPUT_DIR = Path("data")
OUTPUT_PREFIX = "geohazard_news_scrape_"

TIMEOUT = 25
JEDA_ANTAR_FEED = 1.0  # detik, agar tidak membebani server sumber

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "GeoHazard-News-Locator/1.0"
    ),
    "Accept": (
        "application/rss+xml, application/atom+xml, "
        "application/xml, text/xml, */*"
    ),
}

FIELDNAMES = [
    "judul",
    "published_time",
    "event_time",
    "sumber",
    "source_id",
    "kategori",
    "provinsi",
    "kabupaten_kota",
    "kecamatan",
    "desa_kelurahan",
    "dusun_kampung",
    "rw",
    "rt",
    "alamat_detail",
    "url",
    "isi_berita",
    "duplicate_of",
    "duplicate_reason",
]


# ------------------------------------------------------------
# UTILITAS TEKS
# ------------------------------------------------------------

def strip_html(teks):
    """Ubah potongan HTML menjadi teks biasa."""
    if not teks:
        return ""
    soup = BeautifulSoup(teks, "html.parser")
    teks = soup.get_text(" ", strip=True)
    teks = re.sub(r"\s+", " ", teks)
    return teks.strip()


def normalisasi_waktu(nilai):
    """Normalisasi waktu valid ke ISO 8601; kembalikan string kosong jika tidak valid."""
    if nilai is None or nilai == "":
        return ""

    if isinstance(nilai, datetime):
        dt = nilai
    elif isinstance(nilai, (tuple, list)) and len(nilai) >= 6:
        try:
            dt = datetime(*nilai[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return ""
    else:
        teks = str(nilai).strip()
        if not teks or not re.search(r"\d{1,2}:\d{2}", teks):
            return ""
        if teks.endswith(("Z", "z")):
            teks = teks[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(teks)
        except ValueError:
            try:
                dt = parsedate_to_datetime(teks)
            except (TypeError, ValueError, OverflowError):
                return ""

    if dt is None:
        return ""
    try:
        return dt.isoformat()
    except (ValueError, OverflowError):
        return ""


def buat_output_path(now=None):
    """Buat path CSV baru bertimestamp; tidak pernah memakai dataset lama."""
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


def tandai_duplikat(rows):
    """Tandai duplikat tanpa menghapus baris."""
    seen_guid = {}
    seen_url = {}
    for row in rows:
        guid = row.get("_guid") or ""
        url = row.get("url") or ""
        alasan = []
        referensi = []

        if guid and guid in seen_guid:
            alasan.append("guid_sama")
            referensi.append(seen_guid[guid])
        if url and url in seen_url:
            alasan.append("url_sama")
            referensi.append(seen_url[url])

        row["duplicate_reason"] = "+".join(alasan)
        row["duplicate_of"] = referensi[0] if referensi else ""

        if guid and guid not in seen_guid:
            seen_guid[guid] = guid
        if url and url not in seen_url:
            seen_url[url] = guid or url

    return rows


# ------------------------------------------------------------
# PENGAMBILAN DATA
# ------------------------------------------------------------

def fetch(url):
    """Ambil isi URL. Kembalikan bytes atau None bila gagal."""
    try:
        resp = requests.get(
            url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True
        )
        if resp.status_code != 200:
            print(f"    status HTTP {resp.status_code}")
            return None
        return resp.content
    except requests.RequestException as e:
        print(f"    gagal request: {str(e)[:80]}")
        return None


# ------------------------------------------------------------
# PARSER: RSS / ATOM
# ------------------------------------------------------------

def ambil_ringkasan(entry):
    """Ambil ringkasan dari summary/description/content."""
    for kunci in ("summary", "description"):
        nilai = entry.get(kunci)
        if nilai:
            return nilai
    konten = entry.get("content")
    if konten and isinstance(konten, list) and konten:
        return konten[0].get("value", "")
    return ""


def parse_rss(cfg, content):
    """Ubah isi feed RSS/Atom menjadi daftar baris."""
    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        print(f"    feed tidak terbaca: {str(feed.bozo_exception)[:80]}")
        return []

    batas = cfg.get("max_items")
    filter_id = cfg.get("filter_indonesia", False)

    baris = []
    for entry in feed.entries:
        judul = strip_html(entry.get("title", ""))
        link = entry.get("link", "")
        published = normalisasi_waktu(
            entry.get("published_parsed") or entry.get("published")
        )

        ringkasan = strip_html(ambil_ringkasan(entry))
        guid = entry.get("id") or entry.get("guid") or link

        if filter_id:
            gabung = (judul + " " + ringkasan).lower()
            if "indonesia" not in gabung:
                continue

        baris.append(
            buat_baris(cfg, judul, link, published, ringkasan, guid)
        )

        if batas and len(baris) >= batas:
            break

    return baris


# ------------------------------------------------------------
# PARSER: BMKG GEMPA (XML)
# ------------------------------------------------------------

def parse_bmkg_xml(cfg, content):
    """Ubah autogempa/gempaterkini/gempadirasakan.xml jadi baris."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"    XML tidak valid: {str(e)[:80]}")
        return []

    baris = []
    for gempa in root.iter("gempa"):
        data = {}
        for anak in gempa:
            data[anak.tag] = (anak.text or "").strip()

        mag = data.get("Magnitude", "")
        wilayah = data.get("Wilayah", "")
        tanggal = data.get("Tanggal", "")
        jam = data.get("Jam", "")
        datetime_ = data.get("DateTime", "") or f"{tanggal} {jam}".strip()
        event_time = normalisasi_waktu(datetime_)
        kedalaman = data.get("Kedalaman", "")
        lintang = data.get("Lintang", "")
        bujur = data.get("Bujur", "")

        judul = f"Gempa M{mag} {wilayah}".strip()

        bagian = [
            f"Tanggal: {tanggal} {jam}".strip(),
            f"Koordinat: {data.get('Coordinates', '')}",
            f"Magnitudo: {mag}",
            f"Kedalaman: {kedalaman}",
            f"Wilayah: {wilayah}",
        ]
        for label in ("Potensi", "Dirasakan"):
            nilai = data.get(label, "")
            if nilai:
                bagian.append(f"{label}: {nilai}")
        isi = "\n".join(b for b in bagian if b)

        query = urlencode(
            {"t": datetime_, "lat": lintang, "lon": bujur, "mag": mag}
        )
        url = f"https://www.bmkg.go.id/gempabumi/?{query}"
        guid = f"{cfg['id']}:{datetime_}:{lintang}:{bujur}"

        baris.append(
            buat_baris(cfg, judul, url, "", isi, guid, event_time=event_time)
        )

    return baris


# ------------------------------------------------------------
# PEMBENTUK BARIS
# ------------------------------------------------------------

def buat_baris(cfg, judul, url, published, isi, guid, event_time=""):
    """Susun satu dict sesuai FIELDNAMES."""
    row = {k: "" for k in FIELDNAMES}
    row["judul"] = judul
    row["published_time"] = published or ""
    row["event_time"] = event_time or ""
    row["sumber"] = cfg["sumber"]
    row["source_id"] = cfg.get("id", "")
    row["kategori"] = detect_category(judul, isi)
    row["url"] = url
    row["isi_berita"] = isi
    row["_guid"] = guid or url
    return row


# ------------------------------------------------------------
# PROGRAM UTAMA
# ------------------------------------------------------------

def main():
    print("=" * 70)
    print("GEOHAZARD NEWS LOCATOR")
    print("SCRAPER RSS / ATOM")
    print("=" * 70)

    aktif = get_active_feeds()
    output_file = buat_output_path()
    print(f"\nFeed aktif: {len(aktif)}")
    print(f"Output    : {output_file}\n")

    semua = []
    ringkasan = []

    for nomor, cfg in enumerate(aktif, start=1):
        print(f"[{nomor}/{len(aktif)}] {cfg['nama']}")
        print(f"    {cfg['url']}")

        content = fetch(cfg["url"])

        if content is None:
            ringkasan.append((cfg["nama"], 0))
            time.sleep(JEDA_ANTAR_FEED)
            continue

        if cfg["tipe"] == "rss":
            baris = parse_rss(cfg, content)
        elif cfg["tipe"] == "bmkg_xml":
            baris = parse_bmkg_xml(cfg, content)
        else:
            print(f"    tipe '{cfg['tipe']}' belum didukung, dilewati")
            baris = []

        print(f"    -> {len(baris)} item")
        semua.extend(baris)
        ringkasan.append((cfg["nama"], len(baris)))

        time.sleep(JEDA_ANTAR_FEED)

    # --------------------------------------------------------
    # TANDAI DUPLIKAT TANPA MENGHAPUS BARIS
    # --------------------------------------------------------
    baris_final = tandai_duplikat(semua)
    jumlah_duplikat = sum(
        1 for row in baris_final if row["duplicate_reason"]
    )

    # --------------------------------------------------------
    # SIMPAN CSV BARU
    # --------------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
        penulis = csv.DictWriter(file, fieldnames=FIELDNAMES)
        penulis.writeheader()
        for row in baris_final:
            penulis.writerow({k: row[k] for k in FIELDNAMES})

    # --------------------------------------------------------
    # RINGKASAN
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("HASIL PER SUMBER")
    print("=" * 70)
    for nama, jumlah in ringkasan:
        print(f"{nama:<45}: {jumlah}")

    print("\n" + "=" * 70)
    print("HASIL PER KATEGORI")
    print("=" * 70)
    per_kategori = {}
    for row in baris_final:
        per_kategori[row["kategori"]] = per_kategori.get(row["kategori"], 0) + 1
    for kategori, jumlah in sorted(
        per_kategori.items(), key=lambda x: -x[1]
    ):
        print(f"{kategori:<35}: {jumlah}")

    print("\n" + "=" * 70)
    print("SELESAI")
    print("=" * 70)
    print(f"Total item (sebelum penandaan duplikat): {len(semua)}")
    print(f"Total item dipertahankan              : {len(baris_final)}")
    print(f"Item bertanda duplikat                : {jumlah_duplikat}")
    print(f"File hasil                            : {output_file}")


if __name__ == "__main__":
    main()
