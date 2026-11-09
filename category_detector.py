import pandas as pd
import re

# ============================================================
# GEOHAZARD NEWS LOCATOR
# CATEGORY DETECTOR
# ============================================================

INPUT_FILE = "data/bmkg_news.csv"
OUTPUT_FILE = "data/bmkg_news_classified.csv"


# ============================================================
# DAFTAR KATEGORI
# ============================================================

CATEGORIES = [
    "Gunungapi",
    "Gempabumi",
    "Tsunami",
    "Gerakan Tanah/Tanah Longsor",
    "Likuefaksi",
    "Abrasi dan Akresi",
    "Penurunan Muka Tanah",
    "Semburan Gas dan Lumpur",
    "Lainnya"
]


# ============================================================
# FUNGSI MEMBERSIHKAN TEKS
# ============================================================

def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Hilangkan karakter aneh
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# POLA KATEGORI
# ============================================================

_POLA_TSUNAMI = re.compile(r"\btsunami\b")

_POLA_TSUNAMI_KEJADIAN = re.compile(
    r"\btsunami\b[^.!?;]{0,50}\b(?:menerjang|melanda|menghantam|"
    r"merendam|menggenangi|menyapu|setinggi|terjadi)\b"
    r"|\b(?:gelombang|ombak)\s+tsunami\b"
    r"|\b(?:berpotensi|picu|memicu|menimbulkan|menghasilkan|"
    r"menyebabkan)\b[^.!?;]{0,40}\btsunami\b"
    r"|\b(?:peringatan|waspada|ancaman|status|siaga)\s+"
    r"(?:dini\s+)?tsunami\b"
)

_POLA_TSUNAMI_GENERIK = re.compile(
    r"\b(?:sistem|edukasi|mitigasi|kesiapsiagaan|simulasi|pelatihan|"
    r"sosialisasi|literasi|kolaborasi|pengembangan|informasi|sekolah|"
    r"kunjungan|penghargaan|layanan|perkuat|dorong|tingkatkan|dukung|"
    r"gelar)\b"
)

_POLA_TSUNAMI_DAMPAK = re.compile(
    r"\b(?:menerjang|melanda|menghantam|merendam|menggenangi|menyapu|"
    r"setinggi|korban|kerusakan|evakuasi)\b"
)

_POLA_GUNUNGAPI_KUAT = re.compile(
    r"\b(?:erupsi|letusan\s+(?:gunung|vulkanik)|"
    r"gunung(?:\s+\w+){0,2}\s+meletus|"
    r"lava|lahar|abu\s+vulkanik|awan\s+panas|vulkanik|kaldera|magma|"
    r"kawah\s+aktif)\b"
)

_POLA_GUNUNGAPI = re.compile(
    r"\b(?:gunung\s+api|gunung\s+berapi)\b"
)

_POLA_JUDUL_GEMPA_M = re.compile(
    r"^\s*m\s*\d+(?:[.,]\d+)?\s*[-–—]\s*\S"
)

_POLA_DATA_GEMPA = re.compile(
    r"\bm\s*\d+[.,]\d+\b"
    r"|\bmagnitud[oe]\s*[:=]?\s*\d+(?:[.,]\d+)?\b"
    r"|\b\d+(?:[.,]\d+)?\s*sr\b"
    r"|\bskala\s+richter\b"
)

_POLA_GEMPA_SEMUA = re.compile(
    r"\b(?:gempa\s+bumi|gempabumi|gempa|earthquake)\b"
)

_POLA_KONTEKS_GEMPA = re.compile(
    r"\b(?:magnitudo|magnitud|kekuatan|guncangan|mengguncang|guncang|"
    r"episenter|hiposenter|kedalaman|richter|sr|getaran|patahan|"
    r"terjadi|berpusat|pusat\s+gempa|korban|kerusakan|evakuasi|"
    r"melanda|menghantam|merusak|menewaskan|menimbulkan)\b"
)

_POLA_GERAKAN_TANAH = re.compile(
    r"\b(?:tanah\s+longsor|longsor(?:an)?|gerakan\s+tanah|"
    r"pergerakan\s+tanah|tanah\s+bergerak)\b"
)

_POLA_LONGSOR_KEJADIAN = re.compile(
    r"\b(?:menimpa|menutup|menimbun|merusak|menewaskan|melanda|"
    r"menghanyutkan|mengakibatkan|terjadi|korban|evakuasi|tewaskan|"
    r"material|tebing|lereng)\b"
)

_POLA_LIKUEFAKSI = re.compile(
    r"\b(?:likuefaksi|likuifaksi|liquefaction|tanah\s+mencair)\b"
)

_POLA_ABRASI = re.compile(
    r"\b(?:abrasi|akresi|erosi\s+pantai|"
    r"pengikisan\s+(?:garis\s+)?pantai|sedimentasi\s+pantai|"
    r"garis\s+pantai\s+(?:mundur|maju)|perubahan\s+garis\s+pantai)\b"
)

_POLA_PENURUNAN = re.compile(
    r"\b(?:penurunan\s+muka\s+tanah|penurunan\s+tanah|amblesan|"
    r"tanah\s+amblas|subsiden|subsidence|land\s+subsidence|"
    r"tanah\s+turun)\b"
)

_POLA_SEMBURAN = re.compile(
    r"\b(?:semburan\s+gas(?:\s+beracun)?|semburan\s+lumpur(?:\s+panas)?|"
    r"lumpur\s+panas|mud\s+volcano|gunung\s+lumpur|kawah\s+lumpur)\b"
)

_TITLE_RULES = [
    ("Gunungapi", _POLA_GUNUNGAPI_KUAT),
    ("Gempabumi", _POLA_GEMPA_SEMUA),
    ("Gempabumi", _POLA_JUDUL_GEMPA_M),
    ("Gunungapi", _POLA_GUNUNGAPI),
    ("Gerakan Tanah/Tanah Longsor", _POLA_GERAKAN_TANAH),
    ("Likuefaksi", _POLA_LIKUEFAKSI),
    ("Abrasi dan Akresi", _POLA_ABRASI),
    ("Penurunan Muka Tanah", _POLA_PENURUNAN),
    ("Semburan Gas dan Lumpur", _POLA_SEMBURAN),
]

_CONTENT_RULES = [
    ("Likuefaksi", _POLA_LIKUEFAKSI),
    ("Abrasi dan Akresi", _POLA_ABRASI),
    ("Penurunan Muka Tanah", _POLA_PENURUNAN),
    ("Semburan Gas dan Lumpur", _POLA_SEMBURAN),
]


def _ada_tsunami_eksplisit(teks):
    """True jika tsunami muncul tanpa negasi pada klausa yang sama."""
    for match in _POLA_TSUNAMI.finditer(teks):
        awal = max(0, match.start() - 60)
        prefix = teks[awal:match.start()]
        klausa = re.split(r"[.!?;]", prefix)[-1]
        ada_negasi = re.search(
            r"\b(?:tidak|bukan|tanpa|tiada|belum)\b", klausa
        )
        if ada_negasi and not re.search(r"\bhanya\b", klausa):
            continue
        return True
    return False


def _ada_tsunami_judul(teks):
    """True jika judul menyebut tsunami eksplisit, kecuali konteks generik."""
    for klausa in re.split(r"[.!?;]", teks):
        if not _POLA_TSUNAMI.search(klausa):
            continue
        if not _ada_tsunami_eksplisit(klausa):
            continue
        if (
            _POLA_TSUNAMI_GENERIK.search(klausa)
            and not _POLA_TSUNAMI_DAMPAK.search(klausa)
        ):
            continue
        return True
    return False


def _ada_tsunami_kejadian(teks):
    """True hanya untuk tsunami eksplisit sebagai kejadian atau peringatan."""
    for klausa in re.split(r"[.!?;]", teks):
        if not _POLA_TSUNAMI.search(klausa):
            continue
        if not _ada_tsunami_eksplisit(klausa):
            continue
        if not _POLA_TSUNAMI_KEJADIAN.search(klausa):
            continue
        if (
            _POLA_TSUNAMI_GENERIK.search(klausa)
            and not _POLA_TSUNAMI_DAMPAK.search(klausa)
        ):
            continue
        return True
    return False


def _ada_klausa_dengan_konteks(teks, pola_istilah, pola_konteks):
    for klausa in re.split(r"[.!?;]", teks):
        if pola_istilah.search(klausa) and pola_konteks.search(klausa):
            return True
    return False


def _ada_gempabumi_di_konten(teks):
    return _ada_klausa_dengan_konteks(
        teks,
        _POLA_GEMPA_SEMUA,
        _POLA_KONTEKS_GEMPA,
    ) or _ada_klausa_dengan_konteks(
        teks,
        _POLA_DATA_GEMPA,
        _POLA_KONTEKS_GEMPA,
    )


def _ada_longsor_di_konten(teks):
    return _ada_klausa_dengan_konteks(
        teks,
        _POLA_GERAKAN_TANAH,
        _POLA_LONGSOR_KEJADIAN,
    )


def detect_category_detail(title, content):
    """
    Klasifikasi delapan kategori geohazard beserta dasar keputusannya.

    Judul menjadi prioritas. Isi berita dipakai bila judul tidak cukup
    jelas. Tsunami eksplisit selalu didahulukan, termasuk saat disebut
    di isi berita. Jika bukti tidak cukup, hasilnya Lainnya.
    """

    title = clean_text(title)
    content = clean_text(content)

    if _ada_tsunami_judul(title) or _ada_tsunami_kejadian(content):
        return "Tsunami", "tsunami_eksplisit"

    for kategori, pola in _TITLE_RULES:
        if pola.search(title):
            return kategori, f"judul:{kategori}"

    if _POLA_GUNUNGAPI_KUAT.search(content):
        return "Gunungapi", "isi:Gunungapi"

    if _ada_gempabumi_di_konten(content):
        return "Gempabumi", "isi:Gempabumi"

    if _ada_longsor_di_konten(content):
        return "Gerakan Tanah/Tanah Longsor", "isi:Gerakan Tanah/Tanah Longsor"

    for kategori, pola in _CONTENT_RULES:
        if pola.search(content):
            return kategori, f"isi:{kategori}"

    return "Lainnya", "tidak_ada_bukti_8_kategori"


def detect_category(title, content):
    return detect_category_detail(title, content)[0]


# ============================================================
# PROGRAM UTAMA
# ============================================================

def main():

    print("=" * 70)
    print("GEOHAZARD NEWS LOCATOR")
    print("CATEGORY DETECTOR")
    print("=" * 70)

    print("\nMembaca file:")
    print(INPUT_FILE)

    # --------------------------------------------------------
    # BACA CSV
    # --------------------------------------------------------

    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print("\nERROR:")
        print(f"File tidak ditemukan: {INPUT_FILE}")
        return

    print(f"Jumlah berita: {len(df)}")

    # --------------------------------------------------------
    # PASTIKAN KOLOM ADA
    # --------------------------------------------------------

    if "judul" not in df.columns:
        print("\nERROR: Kolom 'judul' tidak ditemukan.")
        return

    if "isi_berita" not in df.columns:
        print("\nERROR: Kolom 'isi_berita' tidak ditemukan.")
        return

    # --------------------------------------------------------
    # KLASIFIKASI
    # --------------------------------------------------------

    df["kategori"] = df.apply(
        lambda row: detect_category(
            row["judul"],
            row["isi_berita"]
        ),
        axis=1
    )

    # --------------------------------------------------------
    # SIMPAN
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # HASIL
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("HASIL KLASIFIKASI")
    print("=" * 70)

    print(
        df[["judul", "kategori"]]
        .to_string(index=False)
    )

    print("\n" + "=" * 70)
    print("JUMLAH PER KATEGORI")
    print("=" * 70)

    jumlah = df["kategori"].value_counts()

    for kategori in CATEGORIES:
        total = jumlah.get(kategori, 0)
        print(f"{kategori:<35}: {total}")

    print("\n" + "=" * 70)
    print("SELESAI")
    print("=" * 70)

    print(f"\nFile hasil:")
    print(OUTPUT_FILE)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
