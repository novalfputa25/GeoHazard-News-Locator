import pandas as pd
from pathlib import Path

# ============================================================
# GEOHAZARD NEWS LOCATOR
# VALIDASI DATA HASIL SCRAPING
# ============================================================

INPUT_FILE = Path("data/bmkg_news.csv")

print("=" * 70)
print("GEOHAZARD NEWS LOCATOR")
print("VALIDASI DATA HASIL SCRAPING")
print("=" * 70)

# ------------------------------------------------------------
# 1. CEK FILE
# ------------------------------------------------------------

if not INPUT_FILE.exists():
    print()
    print("ERROR: File CSV tidak ditemukan!")
    print(f"File yang dicari: {INPUT_FILE}")
    print()
    print("Pastikan kamu sudah menjalankan scraper terlebih dahulu.")
    exit()

print()
print("File ditemukan:")
print(INPUT_FILE)

# ------------------------------------------------------------
# 2. BACA CSV
# ------------------------------------------------------------

try:
    df = pd.read_csv(INPUT_FILE)
except Exception as e:
    print()
    print("ERROR saat membaca CSV:")
    print(e)
    exit()

print()
print("=" * 70)
print("INFORMASI DATA")
print("=" * 70)

print()
print("Jumlah baris :", len(df))
print("Jumlah kolom :", len(df))

# ------------------------------------------------------------
# 3. TAMPILKAN NAMA KOLOM
# ------------------------------------------------------------

print()
print("=" * 70)
print("DAFTAR KOLOM")
print("=" * 70)

for nomor, kolom in enumerate(df.columns, start=1):
    print(f"{nomor}. {kolom}")

# ------------------------------------------------------------
# 4. CEK DATA KOSONG
# ------------------------------------------------------------

print()
print("=" * 70)
print("DATA KOSONG")
print("=" * 70)

for kolom in df.columns:
    jumlah_kosong = df[kolom].isna().sum()

    if jumlah_kosong > 0:
        print(f"{kolom}: {jumlah_kosong} data kosong")
    else:
        print(f"{kolom}: tidak ada data kosong")

# ------------------------------------------------------------
# 5. TAMPILKAN DATA BERITA
# ------------------------------------------------------------

print()
print("=" * 70)
print("DATA BERITA")
print("=" * 70)

for index, row in df.iterrows():

    print()
    print(f"BERITA {index + 1}")
    print("-" * 70)

    for kolom in df.columns:
        nilai = row[kolom]

        if pd.isna(nilai):
            nilai = "-"

        # Untuk isi berita yang panjang,
        # kita tampilkan sedikit saja.
        if kolom.lower() in ["content", "isi", "isi_berita"]:
            teks = str(nilai)

            if len(teks) > 200:
                teks = teks[:200] + "..."

            print(f"{kolom:<20}: {teks}")

        else:
            print(f"{kolom:<20}: {nilai}")

# ------------------------------------------------------------
# 6. CEK DUPLIKAT URL
# ------------------------------------------------------------

print()
print("=" * 70)
print("CEK DUPLIKAT")
print("=" * 70)

kolom_url = None

for kolom in df.columns:
    nama = kolom.lower()

    if nama == "url" or "url" in nama:
        kolom_url = kolom
        break

if kolom_url:

    jumlah_duplikat = df[kolom_url].duplicated().sum()

    print()
    print("Kolom URL      :", kolom_url)
    print("Duplikat URL   :", jumlah_duplikat)

    if jumlah_duplikat == 0:
        print("Status         : Tidak ada duplikat")
    else:
        print("Status         : Ada URL yang duplikat")

else:

    print()
    print("Kolom URL tidak ditemukan.")

# ------------------------------------------------------------
# 7. RINGKASAN
# ------------------------------------------------------------

print()
print("=" * 70)
print("RINGKASAN VALIDASI")
print("=" * 70)

print()
print(f"Total berita : {len(df)}")
print(f"Total kolom  : {len(df.columns)}")

print()
print("Validasi CSV selesai.")

print()
print("=" * 70)
print("SELESAI")
print("=" * 70)