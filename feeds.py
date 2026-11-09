# ============================================================
# GEOHAZARD NEWS LOCATOR
# KONFIGURASI SUMBER DATA
# ============================================================
#
# Berkas ini menjadi SATU-SATUNYA tempat daftar sumber data.
# Jangan hardcode URL feed di script lain; impor dari sini:
#
#   from feeds import FEEDS, get_active_feeds
#
# Setiap entri memiliki kunci:
#   id               : pengenal unik (dipakai untuk logging/dedup)
#   sumber           : label sumber yang ditulis ke kolom "sumber"
#   nama             : nama tampilan
#   url              : URL feed / endpoint data
#   tipe             : "rss" (RSS/Atom) atau "bmkg_xml" atau "api"
#   bahasa           : "id" / "en"
#   cakupan          : perkiraan kategori geohazard yang tercakup
#   filter_indonesia : (opsional) True = hanya simpan item yang
#                      menyebut "Indonesia" (untuk feed global)
#   max_items        : (opsional) batas item terpilih per sumber.
#                      Tidak diisi / None = ambil seluruh item yang tersedia.
#                      Nilai ini mengalahkan --max-items global.
#   pagination       : (opsional) dict untuk feed yang benar-benar mendukung
#                      halaman berikutnya. Contoh:
#                      {"type": "query", "param": "page", "max_pages": 3}
#                      Tipe lain: "template" dengan kunci "template", atau
#                      "path" yang menambahkan /page/<n>/.
#                      Tanpa kunci ini pipeline hanya memakai satu halaman.
#   aktif            : True = ikut diproses
#   catatan          : (opsional) keterangan tambahan
#
# URL di bawah sudah diuji pada Oktober 2026 dengan requests +
# feedparser. Yang mati/404 sengaja TIDAK dimasukkan.
# ============================================================


FEEDS = [

    # --------------------------------------------------------
    # RESMI / TERSTRUKTUR (akurasi per kejadian)
    # --------------------------------------------------------

    {
        "id": "bmkg_nowcast_id",
        "sumber": "BMKG",
        "nama": "BMKG - Peringatan Dini Cuaca",
        "url": "https://www.bmkg.go.id/alerts/nowcast/id/rss.xml",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Cuaca Ekstrem"],
        "aktif": False,
        "catatan": "JANGAN DIGUNAKAN: endpoint /alerts/ dilarang robots.txt dan di luar 8 kategori target.",
    },
    {
        "id": "bmkg_autogempa",
        "sumber": "BMKG",
        "nama": "BMKG - Gempa Terbaru (Autogempa)",
        "url": "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml",
        "tipe": "bmkg_xml",
        "bahasa": "id",
        "cakupan": ["Gempa Bumi", "Tsunami"],
        "aktif": True,
    },
    {
        "id": "bmkg_gempa_terkini",
        "sumber": "BMKG",
        "nama": "BMKG - Gempa Terkini (M5+)",
        "url": "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.xml",
        "tipe": "bmkg_xml",
        "bahasa": "id",
        "cakupan": ["Gempa Bumi", "Tsunami"],
        "aktif": True,
    },
    {
        "id": "bmkg_gempa_dirasakan",
        "sumber": "BMKG",
        "nama": "BMKG - Gempa Dirasakan",
        "url": "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.xml",
        "tipe": "bmkg_xml",
        "bahasa": "id",
        "cakupan": ["Gempa Bumi"],
        "aktif": True,
    },
    {
        "id": "gdacs_all",
        "sumber": "GDACS",
        "nama": "GDACS - Semua Kejadian (24 jam)",
        "url": "https://www.gdacs.org/xml/rss.xml",
        "tipe": "rss",
        "bahasa": "en",
        "cakupan": [
            "Gempa Bumi",
            "Tsunami",
            "Kebakaran Hutan dan Lahan",
            "Cuaca Ekstrem",
        ],
        "filter_indonesia": True,
        "aktif": True,
    },
    {
        "id": "gdacs_eq_24h",
        "sumber": "GDACS",
        "nama": "GDACS - Gempa 24 jam",
        "url": "https://www.gdacs.org/xml/rss_eq_24h.xml",
        "tipe": "rss",
        "bahasa": "en",
        "cakupan": ["Gempa Bumi", "Tsunami"],
        "filter_indonesia": True,
        "aktif": False,
        "catatan": "Cadangan; duplikasi gdacs_all.",
    },
    {
        "id": "usgs_m45",
        "sumber": "USGS",
        "nama": "USGS - Gempa M4.5+ (24 jam)",
        "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.atom",
        "tipe": "rss",
        "bahasa": "en",
        "cakupan": ["Gempa Bumi", "Tsunami"],
        "aktif": True,
        "catatan": "Cakupan global; bisa difilter wilayah Indonesia.",
    },

    # --------------------------------------------------------
    # FEED BERITA (cakupan semua kategori, difilter kategori)
    # --------------------------------------------------------

    {
        "id": "antaranews_warta_bumi",
        "sumber": "ANTARA",
        "nama": "ANTARA - Warta Bumi",
        "url": "https://www.antaranews.com/rss/warta-bumi.xml",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": [
            "Gunung Api",
            "Gempa Bumi",
            "Tsunami",
            "Cuaca Ekstrem",
            "Kebakaran Hutan dan Lahan",
        ],
        "aktif": True,
        "catatan": "Paling relevan: kanal bumi/lingkungan.",
    },
    {
        "id": "antaranews_terkini",
        "sumber": "ANTARA",
        "nama": "ANTARA - Berita Terkini",
        "url": "https://www.antaranews.com/rss/terkini.xml",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Cadangan untuk pemantauan kategori langka.",
    },
    {
        "id": "antaranews_top_news",
        "sumber": "ANTARA",
        "nama": "ANTARA - Top News",
        "url": "https://www.antaranews.com/rss/top-news.xml",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "antaranews_jatim_nasional",
        "sumber": "ANTARA Jatim",
        "nama": "ANTARA Jatim - Nasional",
        "url": "https://jatim.antaranews.com/rss/nasional.xml",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "detik_berita",
        "sumber": "detikcom",
        "nama": "detikcom - Berita",
        "url": "https://news.detik.com/berita/rss",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "cnn_indonesia_nasional",
        "sumber": "CNN Indonesia",
        "nama": "CNN Indonesia - Nasional",
        "url": "https://www.cnnindonesia.com/nasional/rss",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Cadangan; tidak masuk daftar minimum.",
    },
    {
        "id": "cnbc_indonesia_news",
        "sumber": "CNBC Indonesia",
        "nama": "CNBC Indonesia - News",
        "url": "https://www.cnbcindonesia.com/news/rss",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "tempo_nasional",
        "sumber": "Tempo",
        "nama": "Tempo - Nasional",
        "url": "https://rss.tempo.co/nasional",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "liputan6_peristiwa",
        "sumber": "Liputan6",
        "nama": "Liputan6 - Peristiwa",
        "url": "https://feed.liputan6.com/rss/news",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Cadangan; tidak masuk daftar minimum.",
    },
    {
        "id": "republika",
        "sumber": "Republika",
        "nama": "Republika - Utama",
        "url": "https://www.republika.co.id/rss",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "mediaindonesia",
        "sumber": "Media Indonesia",
        "nama": "Media Indonesia",
        "url": "https://mediaindonesia.com/feed",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Cadangan; tidak masuk daftar minimum.",
    },
    {
        "id": "sindonews",
        "sumber": "SINDOnews",
        "nama": "SINDOnews - Terkini",
        "url": "https://www.sindonews.com/rss",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "kumparan",
        "sumber": "kumparan",
        "nama": "kumparan - Terkini",
        "url": "https://lapi.kumparan.com/v2.0/rss/",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "bbc_indonesia",
        "sumber": "BBC Indonesia",
        "nama": "BBC News Indonesia",
        "url": "https://feeds.bbci.co.uk/indonesia/rss.xml",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": ["Semua kategori"],
        "aktif": False,
        "catatan": "Tidak masuk daftar minimum.",
    },
    {
        "id": "mongabay_indonesia",
        "sumber": "Mongabay",
        "nama": "Mongabay Indonesia",
        "url": "https://www.mongabay.co.id/feed/",
        "tipe": "rss",
        "bahasa": "id",
        "cakupan": [
            "Kebakaran Hutan dan Lahan",
            "Abrasi dan Akresi",
            "Gerakan Tanah / Longsor",
        ],
        "aktif": True,
        "catatan": "Spesialis lingkungan; sumber terbaik untuk karhutla.",
    },

    # --------------------------------------------------------
    # BELUM DIPAKAI (bukan RSS / perlu parse khusus)
    # --------------------------------------------------------

    {
        "id": "pvmbg_magma",
        "sumber": "PVMBG/MAGMA",
        "nama": "PVMBG - MAGMA (status gunung api)",
        "url": "https://magma.esdm.go.id",
        "tipe": "api",
        "bahasa": "id",
        "cakupan": ["Gunung Api"],
        "aktif": False,
        "catatan": "TUNGGU IZIN: PVMBG API/Portal MBG/MAGMA belum boleh diotomatisasi; bukan RSS dan perlu parse khusus.",
    },
]


OFFICIAL_INDONESIA_SOURCES = {"BMKG", "PVMBG/MAGMA"}
INTERNATIONAL_SOURCES = {"GDACS", "USGS"}
NEWS_SOURCES = {
    "ANTARA",
    "ANTARA Jatim",
    "detikcom",
    "CNN Indonesia",
    "CNBC Indonesia",
    "Tempo",
    "Liputan6",
    "Republika",
    "Media Indonesia",
    "SINDOnews",
    "kumparan",
    "BBC Indonesia",
    "Mongabay",
}

OFFICIAL_SOURCES = OFFICIAL_INDONESIA_SOURCES


def get_active_feeds(tipe=None):
    """Kembalikan daftar feed aktif, opsional difilter berdasarkan tipe."""
    hasil = [f for f in FEEDS if f.get("aktif")]
    if tipe is not None:
        hasil = [f for f in hasil if f.get("tipe") == tipe]
    return hasil


if __name__ == "__main__":
    aktif = get_active_feeds()
    print("=" * 70)
    print("GEOHAZARD NEWS LOCATOR - DAFTAR SUMBER DATA")
    print("=" * 70)
    print(f"Total feed      : {len(FEEDS)}")
    print(f"Feed aktif      : {len(aktif)}")
    print(f"Feed non-aktif  : {len(FEEDS) - len(aktif)}")
    print()

    for tipe in ("rss", "bmkg_xml", "api"):
        grup = [f for f in FEEDS if f.get("tipe") == tipe]
        print(f"[{tipe}] {len(grup)} feed")
        for f in grup:
            tanda = "  " if f.get("aktif") else "x "
            print(f"  {tanda}{f['nama']:<40} {f['url']}")
        print()
