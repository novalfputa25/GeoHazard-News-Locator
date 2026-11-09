import pandas as pd
from pathlib import Path
import re

# ============================================================
# GEOHAZARD NEWS LOCATOR
# DETEKSI KATEGORI BERITA
# ============================================================

INPUT_FILE = Path("data/bmkg_news.csv")
OUTPUT_FILE = Path("data/bmkg_news_categorized.csv")


# ============================================================
# DAFTAR KATEGORI DAN KATA KUNCI
# ============================================================

CATEGORY_KEYWORDS = {

    "Gunung Api": [
        "gunung api",
        "gunungapi",
        "erupsi",
        "letusan gunung",
        "lava",
        "awan panas",
        "guguran lava",
        "abu vulkanik",
        "status gunung api",
        "aktivitas vulkanik",
        "vulkanik"
    ],

    "Gempa Bumi": [
        "gempa bumi",
        "gempabumi",
        "gempa",
        "seismik",
        "seismologi",
        "guncangan gempa",
        "magnitudo",
        "episenter",
        "hiposenter",
        "sesar aktif"
    ],

    "Tsunami": [
        "tsunami",
        "peringatan tsunami",
        "potensi tsunami",
        "gelombang tsunami"
    ],

    "Gerakan Tanah / Longsor": [
        "longsor",
        "tanah longsor",
        "gerakan tanah",
        "pergerakan tanah",
        "runtuhan tanah",
        "tebing longsor"
    ],

    "Likuefaksi": [
        "likuefaksi",
        "likuifaksi",
        "liquefaction"
    ],

    "Abrasi dan Akresi": [
        "abrasi",
        "akresi",
        "erosi pantai",
        "perubahan garis pantai",
        "garis pantai"
    ],

    "Penurunan Muka Tanah": [
        "penurunan muka tanah",
        "subsidence",
        "amblesan",
        "tanah turun",
        "penurunan tanah"
    ],

    "Semburan Gas dan Lumpur": [
        "semburan lumpur",
        "semburan gas",
        "gas bumi",
        "lumpur panas",
        "mud volcano",
        "gunung lumpur"
    ],

    "Banjir": [
        "banjir",
        "banjir bandang",
        "genangan",
        "luapan sungai"
    ],

    "Kebakaran Hutan dan Lahan": [
        "karhutla",
        "kebakaran hutan",
        "kebakaran lahan",
        "titik panas",
        "hotspot"
    ],

    "Cuaca Ekstrem": [
        "cuaca ekstrem",
        "hujan ekstrem",
        "hujan lebat",
        "hujan sangat lebat",
        "angin kencang",
        "puting beliung",
        "angin puting beliung"
    ]
}


# ============================================================
# PRIORITAS KATEGORI
# ============================================================

CATEGORY_PRIORITY = [
    "Tsunami",
    "Gunung Api",
    "Likuefaksi",
    "Semburan Gas dan Lumpur",
    "Penurunan Muka Tanah",
    "Gerakan Tanah / Longsor",
    "Abrasi dan Akresi",
    "Gempa Bumi",
    "Kebakaran Hutan dan Lahan",
    "Banjir",
    "Cuaca Ekstrem"
]


# ============================================================
# FUNGSI MEMBERSIHKAN TEKS
# ============================================================

def clean_text(text):
    """
    Membersihkan teks agar lebih mudah dianalisis.
    """

    if pd.isna(text):
        return ""

    text = str(text)

    # Ubah menjadi huruf kecil
    text = text.lower()

    # Hilangkan karakter berlebihan
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# FUNGSI DETEKSI KATEGORI
# ============================================================

def detect_category(title, content):
    """
    Menentukan kategori berdasarkan judul dan isi berita.
    """

    title = clean_text(title)
    content = clean_text(content)

    # Judul diberi bobot lebih tinggi
    combined_text = title + " " + content

    scores = {}

    # Hitung jumlah kecocokan setiap kategori
    for category, keywords in CATEGORY_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            keyword = keyword.lower()

            # Kemunculan di judul memiliki bobot lebih besar
            title_count = title.count(keyword)

            # Kemunculan di isi berita
            content_count = content.count(keyword)

            score += title_count * 5
            score += content_count

        scores[category] = score

    # Cari kategori dengan skor tertinggi
    max_score = max(scores.values())

    # Tidak ada kata kunci yang cocok
    if max_score == 0:
        return "Lainnya"

    # Ambil semua kategori dengan skor tertinggi
    candidates = [
        category
        for category, score in scores.items()
        if score == max_score
    ]

    # Jika hanya satu
    if len(candidates) == 1:
        return candidates[0]

    # Jika seri, gunakan prioritas kategori
    for category in CATEGORY_PRIORITY:

        if category in candidates:
            return category

    return candidates[0]


# ============================================================
# PROGRAM UTAMA
# ============================================================

print("=" * 70)
print("GEOHAZARD NEWS LOCATOR")
print("DETEKSI KATEGORI BERITA")
print("=" * 70)


# ------------------------------------------------------------
# CEK FILE
# ------------------------------------------------------------

if not INPUT_FILE.exists():

    print()
    print("ERROR: File tidak ditemukan!")
    print(f"File: {INPUT_FILE}")
    print()
    print("Pastikan bmkg_news.csv sudah tersedia di folder data.")

    exit()


# ------------------------------------------------------------
# BACA CSV
# ------------------------------------------------------------

print()
print("Membaca data...")

df = pd.read_csv(INPUT_FILE)

print(f"Jumlah berita: {len(df)}")


# ------------------------------------------------------------
# CEK KOLOM
# ------------------------------------------------------------

required_columns = [
    "judul",
    "isi_berita"
]

for column in required_columns:

    if column not in df.columns:

        print()
        print(f"ERROR: Kolom '{column}' tidak ditemukan.")

        print()
        print("Kolom yang tersedia:")

        for col in df.columns:
            print("-", col)

        exit()


# ------------------------------------------------------------
# DETEKSI KATEGORI
# ------------------------------------------------------------

print()
print("=" * 70)
print("MEMPROSES KATEGORI")
print("=" * 70)

categories = []


for index, row in df.iterrows():

    title = row["judul"]
    content = row["isi_berita"]

    category = detect_category(
        title,
        content
    )

    categories.append(category)

    print()
    print(f"Berita {index + 1}")
    print("-" * 70)
    print("Judul    :", title)
    print("Kategori :", category)


# ------------------------------------------------------------
# SIMPAN HASIL
# ------------------------------------------------------------

df["kategori"] = categories


# Pastikan folder data tersedia
OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# STATISTIK KATEGORI
# ------------------------------------------------------------

print()
print("=" * 70)
print("STATISTIK KATEGORI")
print("=" * 70)

category_counts = df["kategori"].value_counts()

for category, count in category_counts.items():

    print(
        f"{category:<35} : {count} berita"
    )


# ------------------------------------------------------------
# HASIL
# ------------------------------------------------------------

print()
print("=" * 70)
print("SELESAI")
print("=" * 70)

print()
print("Data berhasil disimpan:")
print(OUTPUT_FILE)

print()
print("CSV asli TIDAK diubah.")
print("File baru berisi hasil klasifikasi kategori.")