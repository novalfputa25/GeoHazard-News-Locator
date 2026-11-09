import unittest

import category_detector as cd


CATEGORIES = [
    "Gunungapi",
    "Gempabumi",
    "Tsunami",
    "Gerakan Tanah/Tanah Longsor",
    "Likuefaksi",
    "Abrasi dan Akresi",
    "Penurunan Muka Tanah",
    "Semburan Gas dan Lumpur",
]


class CategoryDetectorStage2Test(unittest.TestCase):
    def assert_cases(self, cases):
        for title, content, expected in cases:
            with self.subTest(title=title, content=content):
                self.assertEqual(
                    cd.detect_category(title, content),
                    expected,
                )

    def test_category_list(self):
        self.assertEqual(cd.CATEGORIES, CATEGORIES + ["Lainnya"])

    def test_eight_categories(self):
        self.assert_cases(
            [
                (
                    "Erupsi Gunung Api Merapi, hujan abu vulkanik",
                    "",
                    "Gunungapi",
                ),
                (
                    "Gempa bumi magnitudo 5,2 guncang Ambon",
                    "",
                    "Gempabumi",
                ),
                (
                    "Peringatan dini tsunami di Pantai Selatan",
                    "",
                    "Tsunami",
                ),
                (
                    "Tanah longsor timpa rumah warga di Bogor",
                    "",
                    "Gerakan Tanah/Tanah Longsor",
                ),
                (
                    "Likuefaksi merusak permukiman di Palu",
                    "",
                    "Likuefaksi",
                ),
                (
                    "Abrasi pantai menggerus permukiman nelayan",
                    "",
                    "Abrasi dan Akresi",
                ),
                (
                    "Penurunan muka tanah di Jakarta Utara meluas",
                    "",
                    "Penurunan Muka Tanah",
                ),
                (
                    "Semburan gas dan lumpur muncul di Sidoarjo",
                    "",
                    "Semburan Gas dan Lumpur",
                ),
            ]
        )

    def test_tsunami_priority_and_negation(self):
        self.assert_cases(
            [
                ("Gempa M 7,5 picu tsunami di Palu", "", "Tsunami"),
                ("Gempa bumi dan tsunami", "", "Tsunami"),
                (
                    "Gempa M 6,0, tidak berpotensi tsunami",
                    "BMKG: gempa tidak berpotensi tsunami",
                    "Gempabumi",
                ),
                ("Bukan tsunami, hanya gempa", "", "Gempabumi"),
                (
                    "Gempa bumi magnitudo 5,0",
                    "Tsunami setinggi satu meter melanda pantai.",
                    "Tsunami",
                ),
            ]
        )

    def test_usgs_magnitude_titles(self):
        self.assert_cases(
            [
                (
                    "M 4.5 - 10 km NNE of Bitung, Indonesia",
                    "",
                    "Gempabumi",
                ),
                (
                    "M4.8 - 52 km SW of Meulaboh, Indonesia",
                    "",
                    "Gempabumi",
                ),
                (
                    "M 5.1 - 12 km E of Palu, Indonesia",
                    "",
                    "Gempabumi",
                ),
            ]
        )

    def test_irrelevant_context(self):
        self.assert_cases(
            [
                (
                    "BMKG Terima Kunjungan Presiden WMO",
                    "Indonesia menghadapi berbagai ancaman bencana alam, "
                    "mulai dari cuaca ekstrem hingga gempa bumi dan tsunami.",
                    "Lainnya",
                ),
                (
                    "BMKG Perkuat Layanan",
                    "BMKG memperkuat sistem peringatan dini tsunami.",
                    "Lainnya",
                ),
                (
                    "Harga gas alam naik",
                    "Pemerintah menyesuaikan harga gas alam industri.",
                    "Lainnya",
                ),
                (
                    "Gunung Kidul diguyur hujan lebat",
                    "Hujan lebat menyebabkan genangan di jalan.",
                    "Lainnya",
                ),
                (
                    "Mayors Talk 2026",
                    "Hujan berintensitas tinggi dapat meningkatkan risiko "
                    "banjir dan longsor.",
                    "Lainnya",
                ),
            ]
        )

    def test_empty_fields(self):
        self.assert_cases(
            [
                ("", "", "Lainnya"),
                (None, None, "Lainnya"),
                (
                    "",
                    "Gempa magnitudo 5,0 terjadi di laut.",
                    "Gempabumi",
                ),
                (
                    None,
                    "Tanah longsor menimpa rumah.",
                    "Gerakan Tanah/Tanah Longsor",
                ),
                ("Laporan", "", "Lainnya"),
            ]
        )

    def test_case_and_spelling_variations(self):
        self.assert_cases(
            [
                (
                    "ERUPSI GUNUNG API MERAPI",
                    "",
                    "Gunungapi",
                ),
                (
                    "GEMPA BUMI MAGNITUDO 5,2",
                    "",
                    "Gempabumi",
                ),
                (
                    "TSUNAMI MENERJANG PANTAI",
                    "",
                    "Tsunami",
                ),
                (
                    "TANAH LONGSOR TIMPA RUMAH",
                    "",
                    "Gerakan Tanah/Tanah Longsor",
                ),
                (
                    "LIQUEFACTION MERUSAK PERMUKIMAN",
                    "",
                    "Likuefaksi",
                ),
                (
                    "ABRASI PANTAI MENGERUS PERMUKIMAN",
                    "",
                    "Abrasi dan Akresi",
                ),
                (
                    "LAND SUBSIDENCE MELUAS DI JAKARTA",
                    "",
                    "Penurunan Muka Tanah",
                ),
                (
                    "MUD VOLCANO MENYEMBUR DI SIDOARJO",
                    "",
                    "Semburan Gas dan Lumpur",
                ),
                (
                    "Laporan pagi",
                    "Badan geologi mencatat penurunan muka tanah di pesisir.",
                    "Penurunan Muka Tanah",
                ),
                (
                    "Informasi terkini",
                    "Warga melaporkan semburan lumpur panas di persawahan.",
                    "Semburan Gas dan Lumpur",
                ),
            ]
        )

    def test_rule_order(self):
        self.assert_cases(
            [
                ("Gempa M 7,5 picu tsunami", "", "Tsunami"),
                ("Erupsi Gunung Api picu gempa", "", "Gunungapi"),
                ("Gempa guncang Gunung Kidul", "", "Gempabumi"),
                (
                    "Gunung Api Merapi",
                    "Gempa vulkanik terekam",
                    "Gunungapi",
                ),
                (
                    "BMKG Edukasi Masyarakat Magetan Melalui Sekolah "
                    "Lapang Gempabumi",
                    "Peserta mendapat materi informasi gempabumi dan "
                    "peringatan dini tsunami BMKG.",
                    "Gempabumi",
                ),
            ]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
