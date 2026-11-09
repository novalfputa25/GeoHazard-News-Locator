# ============================================================
# GEOHAZARD NEWS LOCATOR
# BUILD GAZETTEER WILAYAH (provinsi + kabupaten/kota)
# ============================================================
#
# Mengunduh daftar provinsi & kabupaten/kota dari API publik
# (emsifa.com/api-wilayah-indonesia), lalu menyimpannya ke
# data/wilayah_gazetteer.json.
#
# Cukup dijalankan SEKALI (atau saat ingin memperbarui daftar).
# location_extractor.py memakai file JSON hasil ini, bukan
# mengakses jaringan setiap kali.
#
# Jalankan:
#   python build_gazetteer.py
# ============================================================

import json
import time
from pathlib import Path

import requests

from wilayah_reference import PROVINCES

BASE = "https://www.emsifa.com/api-wilayah-indonesia/api"
OUTPUT_FILE = Path("data/wilayah_gazetteer.json")
TIMEOUT = 25
HEADERS = {"User-Agent": "GeoHazard-News-Locator/1.0"}


def titlecase(nama):
    """KABUPATEN ACEH BESAR -> Kabupaten Aceh Besar."""
    return nama.title()


def tipe_wilayah(nama):
    n = nama.upper()
    if n.startswith("KOTA"):
        return "kota"
    if n.startswith("KABUPATEN"):
        return "kabupaten"
    return "lainnya"


def ambil(url):
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def main():
    print("=" * 70)
    print("BUILD GAZETTEER WILAYAH INDONESIA")
    print("=" * 70)

    print("\nMengunduh daftar provinsi...")
    provinsi = ambil(f"{BASE}/provinces.json")
    print(f"  {len(provinsi)} provinsi diterima.")

    # Peta nama provinsi (UPPERCASE dari API) -> nama kanonik
    kanonik = {p.upper(): p for p in PROVINCES}

    regencies = []

    for i, prov in enumerate(provinsi, start=1):
        nama_prov = kanonik.get(prov["name"].upper(), titlecase(prov["name"]))
        print(f"  [{i}/{len(provinsi)}] {nama_prov}...", end=" ")

        try:
            daftar = ambil(f"{BASE}/regencies/{prov['id']}.json")
        except requests.RequestException as e:
            print(f"gagal ({str(e)[:40]})")
            continue

        for kab in daftar:
            regencies.append(
                {
                    "nama": titlecase(kab["name"]),
                    "provinsi": nama_prov,
                    "tipe": tipe_wilayah(kab["name"]),
                }
            )

        print(f"{len(daftar)} kabupaten/kota")
        time.sleep(0.15)

    data = {
        "sumber": "emsifa.com/api-wilayah-indonesia",
        "jumlah_provinsi": len(provinsi),
        "jumlah_kabupaten_kota": len(regencies),
        "provinsi": PROVINCES,
        "kabupaten_kota": regencies,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"Total kabupaten/kota : {len(regencies)}")
    print(f"File                 : {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
