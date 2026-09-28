import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


# ========================================
# 1. HALAMAN BERITA BMKG
# ========================================

url = "https://www.bmkg.go.id/berita/utama"

response = requests.get(
    url,
    timeout=10
)

print("Status halaman utama:", response.status_code)

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ========================================
# 2. CARI WADAH BERITA
# ========================================

news_container = soup.find(
    "div",
    class_="mt-6 md:mt-10 grid grid-cols-1 gap-6 lg:grid-cols-3 lg:gap-8"
)

if not news_container:
    print("Wadah berita tidak ditemukan.")
    exit()


# ========================================
# 3. AMBIL LINK BERITA PERTAMA
# ========================================

first_link = news_container.find("a")

if not first_link:
    print("Link berita tidak ditemukan.")
    exit()


relative_url = first_link.get("href")

news_url = urljoin(
    url,
    relative_url
)

print("\nURL berita:")
print(news_url)


# ========================================
# 4. BUKA HALAMAN DETAIL BERITA
# ========================================

news_response = requests.get(
    news_url,
    timeout=10
)

print(
    "\nStatus halaman berita:",
    news_response.status_code
)

news_soup = BeautifulSoup(
    news_response.text,
    "html.parser"
)


# ========================================
# 5. AMBIL JUDUL
# ========================================

title = news_soup.title

judul = ""

if title:

    judul = title.get_text(
        strip=True
    )

    judul = judul.replace(
        " - Berita Utama - BMKG",
        ""
    )


# ========================================
# 6. AMBIL TANGGAL BERITA
# ========================================

tanggal = None

semua_teks = news_soup.get_text(
    " ",
    strip=True
)

pola_tanggal = (
    r"\b\d{1,2}\s+"
    r"(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)"
    r"\s+\d{4}\b"
)

hasil_tanggal = re.search(
    pola_tanggal,
    semua_teks
)

if hasil_tanggal:

    tanggal = hasil_tanggal.group()


# ========================================
# 7. CARI PARAGRAF ARTIKEL
# ========================================

paragraphs = news_soup.find_all("p")

isi_berita = []

for paragraph in paragraphs:

    text = paragraph.get_text(
        " ",
        strip=True
    )

    if text.startswith(
        "Karanganyar, 25 September 2026"
    ):

        print(
            "\nParagraf artikel ditemukan!"
        )

        # ========================================
        # 8. CEK STRUKTUR HTML
        # ========================================

        parent = paragraph.parent

        print("\n========================================")
        print("STRUKTUR ARTIKEL")
        print("========================================")

        print("\nTAG PARENT:")
        print(parent.name)

        print("\nCLASS PARENT:")
        print(parent.get("class"))

        print("\nTAG GRANDPARENT:")
        print(parent.parent.name)

        print("\nCLASS GRANDPARENT:")
        print(
            parent.parent.get("class")
        )

        break


# ========================================
# 9. TAMPILKAN DATA DASAR
# ========================================

print("\n========================================")
print("DATA BERITA")
print("========================================")

print("Judul   :", judul)
print("Tanggal :", tanggal)
print("Sumber  : BMKG")
print("URL     :", news_url)