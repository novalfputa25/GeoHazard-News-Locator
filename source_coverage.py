import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from geohazard_pipeline.util import TARGET_CATEGORIES

ROOT = Path(__file__).resolve().parent
SOURCES_PATH = ROOT / "docs" / "SOURCE_COVERAGE_SOURCES.csv"
CATEGORY_MAP_PATH = ROOT / "docs" / "SOURCE_CATEGORY_MAP.csv"
REPORT_PATH = ROOT / "reports" / "SOURCE_COVERAGE_8_CATEGORIES.md"

SOURCE_FIELDS = (
    "source_id",
    "nama_sumber",
    "institusi",
    "url",
    "peran_sumber",
    "metode_akses",
    "format_data",
    "cakupan_geografis",
    "jenis_data_utama",
    "status_akses",
    "status_izin",
    "status_implementasi",
    "terakhir_diverifikasi",
    "bukti_akses",
    "keterbatasan",
)

MAPPING_FIELDS = (
    "source_id",
    "category",
    "jenis_data",
    "status_pemetaan",
    "prioritas",
    "bukti_pemetaan",
    "keterbatasan_pemetaan",
)

DATA_TYPES = {
    "kejadian_aktual",
    "katalog_historis",
    "laporan_berita",
    "peta_risiko",
    "informasi_kerentanan",
    "penelitian_kajian",
    "informasi_manual",
    "atribut_bahaya",
    "katalog_data",
}

ACCESS_STATUSES = {
    "terverifikasi_aktif",
    "terverifikasi_manual",
    "perlu_izin",
    "belum_tersedia",
    "tidak_sesuai",
    "belum_diverifikasi",
}

PERMISSION_STATUSES = {
    "terbuka",
    "perlu_izin",
    "belum_jelas",
    "dilarang",
    "tidak_berlaku",
}

IMPLEMENTATION_STATUSES = {
    "aktif_pipeline",
    "tersedia_nonaktif",
    "belum_diimplementasikan",
    "manual",
    "tidak_direncanakan",
}

MAPPING_STATUSES = {
    "terverifikasi",
    "kandidat",
    "belum_terverifikasi",
}

PRIORITIES = {"P0", "P1", "P2"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

CONTEXT_DATA_TYPES = {
    "informasi_kerentanan",
    "penelitian_kajian",
    "informasi_manual",
    "atribut_bahaya",
    "katalog_data",
}

def _read_rows(path, fields):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Registry tidak ditemukan: {path}")

    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Registry kosong: {path}")

        missing = [field for field in fields if field not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"Kolom wajib tidak ditemukan di {path}: {', '.join(missing)}"
            )

        rows = []
        for line_number, raw in enumerate(reader, start=2):
            row = {field: str(raw.get(field) or "").strip() for field in fields}
            if not any(row.values()):
                continue
            row["_line"] = line_number
            rows.append(row)

    return rows


def load_sources(path=SOURCES_PATH):
    return _read_rows(path, SOURCE_FIELDS)


def load_category_map(path=CATEGORY_MAP_PATH):
    return _read_rows(path, MAPPING_FIELDS)


def _clean_rows(rows):
    return [{key: value for key, value in row.items() if key != "_line"} for row in rows]


def validate_registry(sources=None, mappings=None):
    if sources is None:
        sources = load_sources()
    if mappings is None:
        mappings = load_category_map()

    errors = []
    source_ids = set()
    mapping_keys = set()

    for row in sources:
        line = row.get("_line", "?")
        source_id = row["source_id"]
        if not source_id:
            errors.append(f"baris {line}: source_id kosong")
            continue
        if source_id in source_ids:
            errors.append(f"baris {line}: source_id duplikat {source_id}")
        source_ids.add(source_id)

        for field in SOURCE_FIELDS:
            if not row[field]:
                errors.append(f"baris {line}: {source_id}.{field} kosong")

        if row["status_akses"] not in ACCESS_STATUSES:
            errors.append(
                f"baris {line}: status_akses tidak dikenal {row['status_akses']}"
            )
        if row["status_izin"] not in PERMISSION_STATUSES:
            errors.append(
                f"baris {line}: status_izin tidak dikenal {row['status_izin']}"
            )
        if row["status_implementasi"] not in IMPLEMENTATION_STATUSES:
            errors.append(
                "baris "
                f"{line}: status_implementasi tidak dikenal "
                f"{row['status_implementasi']}"
            )

    categories_with_mapping = set()

    for row in mappings:
        line = row.get("_line", "?")
        source_id = row["source_id"]
        category = row["category"]
        jenis_data = row["jenis_data"]

        if source_id not in source_ids:
            errors.append(
                f"baris {line}: mapping memakai source_id tidak dikenal {source_id}"
            )
        if category not in TARGET_CATEGORIES:
            errors.append(f"baris {line}: kategori tidak dikenal {category}")
        if jenis_data not in DATA_TYPES:
            errors.append(f"baris {line}: jenis_data tidak dikenal {jenis_data}")
        if row["status_pemetaan"] not in MAPPING_STATUSES:
            errors.append(
                "baris "
                f"{line}: status_pemetaan tidak dikenal "
                f"{row['status_pemetaan']}"
            )
        if row["prioritas"] not in PRIORITIES:
            errors.append(
                f"baris {line}: prioritas tidak dikenal {row['prioritas']}"
            )

        for field in MAPPING_FIELDS:
            if not row[field]:
                errors.append(f"baris {line}: mapping.{field} kosong")

        key = (source_id, category, jenis_data)
        if key in mapping_keys:
            errors.append(
                f"baris {line}: mapping duplikat {source_id}/{category}/{jenis_data}"
            )
        mapping_keys.add(key)
        categories_with_mapping.add(category)

    for category in TARGET_CATEGORIES:
        if category not in categories_with_mapping:
            errors.append(f"kategori belum memiliki mapping: {category}")

    return errors


def load_registry():
    sources = load_sources()
    mappings = load_category_map()
    errors = validate_registry(sources, mappings)
    if errors:
        raise ValueError("Registry tidak valid:\n" + "\n".join(errors))
    return _clean_rows(sources), _clean_rows(mappings)


def categories_for_source(source_id, mappings=None):
    if mappings is None:
        mappings = load_category_map()
    found = {
        row["category"]
        for row in mappings
        if row["source_id"] == source_id
    }
    return [category for category in TARGET_CATEGORIES if category in found]


def mappings_for_category(category, mappings=None):
    if category not in TARGET_CATEGORIES:
        raise ValueError(f"Kategori tidak dikenal: {category}")
    if mappings is None:
        mappings = load_category_map()
    return [row for row in mappings if row["category"] == category]


def sources_for_category(category, sources=None, mappings=None):
    if sources is None:
        sources = load_sources()
    if mappings is None:
        mappings = load_category_map()
    source_ids = {
        row["source_id"] for row in mappings_for_category(category, mappings)
    }
    return sorted(
        [row for row in sources if row["source_id"] in source_ids],
        key=lambda row: row["source_id"],
    )


def _unique_sources(mappings, predicate):
    return {
        row["source_id"]
        for row in mappings
        if predicate(row)
    }


def _coverage_status(item):
    if item["official_active_event_sources"]:
        return "TERCAKUP_OPERASIONAL"
    if item["active_event_sources"]:
        return "TERCAKUP_SEBAGIAN"
    if item["official_candidate_event_sources"]:
        return "KANDIDAT_RESMI_PERLU_IZIN"
    if item["event_candidate_sources"]:
        return "KANDIDAT_KEJADIAN"

    labels = []
    if item["historical_sources"]:
        labels.append("KATALOG_HISTORIS")
    if item["news_sources"]:
        labels.append("BERITA")
    if item["risk_sources"]:
        labels.append("PETA_RISIKO")
    if item["research_sources"]:
        labels.append("KAJIAN")
    if item["manual_sources"]:
        labels.append("INFORMASI_MANUAL")
    if labels:
        return "HANYA_" + "_DAN_".join(labels)
    return "BELUM_ADA_SUMBER"


def _status_summary(sources):
    access_counts = dict(
        sorted(Counter(row["status_akses"] for row in sources).items())
    )
    permission_counts = dict(
        sorted(Counter(row["status_izin"] for row in sources).items())
    )
    implementation_counts = dict(
        sorted(Counter(row["status_implementasi"] for row in sources).items())
    )
    need_permission_ids = sorted(
        row["source_id"]
        for row in sources
        if row["status_izin"] == "perlu_izin"
    )
    access_permission_ids = sorted(
        row["source_id"]
        for row in sources
        if row["status_akses"] == "perlu_izin"
    )
    return {
        "access_counts": access_counts,
        "permission_counts": permission_counts,
        "implementation_counts": implementation_counts,
        "active_pipeline_ids": sorted(
            row["source_id"]
            for row in sources
            if row["status_implementasi"] == "aktif_pipeline"
        ),
        "need_permission_ids": need_permission_ids,
        "access_permission_ids": access_permission_ids,
        "need_permission_without_access_permission_ids": sorted(
            set(need_permission_ids) - set(access_permission_ids)
        ),
        "unavailable_ids": sorted(
            row["source_id"]
            for row in sources
            if row["status_akses"] in {"belum_tersedia", "tidak_sesuai"}
        ),
        "unverified_ids": sorted(
            row["source_id"]
            for row in sources
            if row["status_akses"] == "belum_diverifikasi"
        ),
    }


def coverage_summary(sources=None, mappings=None):
    if sources is None:
        sources = load_sources()
    if mappings is None:
        mappings = load_category_map()

    errors = validate_registry(sources, mappings)
    if errors:
        raise ValueError("Registry tidak valid:\n" + "\n".join(errors))

    source_by_id = {row["source_id"]: row for row in sources}
    categories = []

    for category in TARGET_CATEGORIES:
        category_mappings = mappings_for_category(category, mappings)
        source_ids = sorted({row["source_id"] for row in category_mappings})
        category_sources = [source_by_id[source_id] for source_id in source_ids]

        active_pipeline = {
            row["source_id"]
            for row in category_sources
            if row["status_implementasi"] == "aktif_pipeline"
        }
        active_event = {
            row["source_id"]
            for row in category_mappings
            if row["jenis_data"] == "kejadian_aktual"
            and row["status_pemetaan"] == "terverifikasi"
            and source_by_id[row["source_id"]]["status_implementasi"]
            == "aktif_pipeline"
        }
        official_active_event = {
            source_id
            for source_id in active_event
            if source_by_id[source_id]["peran_sumber"] == "sumber_utama_resmi"
        }
        event_candidate = {
            row["source_id"]
            for row in category_mappings
            if row["jenis_data"] == "kejadian_aktual"
            and row["status_pemetaan"] in {"terverifikasi", "kandidat"}
            and source_by_id[row["source_id"]]["status_akses"]
            not in {"belum_tersedia", "tidak_sesuai"}
        }
        official_candidate_event = {
            source_id
            for source_id in event_candidate - active_event
            if source_by_id[source_id]["peran_sumber"]
            in {"sumber_utama_resmi", "sumber_resmi_kandidat"}
        }

        news = _unique_sources(
            category_mappings, lambda row: row["jenis_data"] == "laporan_berita"
        )
        historical = _unique_sources(
            category_mappings, lambda row: row["jenis_data"] == "katalog_historis"
        )
        risk = _unique_sources(
            category_mappings, lambda row: row["jenis_data"] == "peta_risiko"
        )
        research = _unique_sources(
            category_mappings, lambda row: row["jenis_data"] == "penelitian_kajian"
        )
        manual = _unique_sources(
            category_mappings,
            lambda row: row["jenis_data"] in CONTEXT_DATA_TYPES,
        )

        priorities = [row["prioritas"] for row in category_mappings]
        priority = min(priorities, key=lambda value: PRIORITY_ORDER[value])
        data_types = Counter(row["jenis_data"] for row in category_mappings)

        item = {
            "category": category,
            "source_ids": source_ids,
            "total_sources": len(source_ids),
            "active_pipeline_sources": len(active_pipeline),
            "active_event_sources": len(active_event),
            "official_active_event_sources": len(official_active_event),
            "event_candidate_sources": len(event_candidate),
            "official_candidate_event_sources": len(official_candidate_event),
            "active_event_source_ids": sorted(active_event),
            "official_active_event_source_ids": sorted(official_active_event),
            "event_candidate_source_ids": sorted(event_candidate),
            "official_candidate_event_source_ids": sorted(official_candidate_event),
            "news_sources": len(news),
            "historical_sources": len(historical),
            "risk_sources": len(risk),
            "research_sources": len(research),
            "manual_sources": len(manual),
            "data_types": dict(sorted(data_types.items())),
            "priority": priority,
        }
        item["coverage_status"] = _coverage_status(item)
        categories.append(item)

    return {
        "generated_at": datetime.now(timezone.utc).date().isoformat(),
        "source_count": len(sources),
        "mapping_count": len(mappings),
        "categories": categories,
        **_status_summary(sources),
    }


def _source_mapping_rows(source_id, category, mappings):
    rows = [
        row
        for row in mappings
        if row["source_id"] == source_id and row["category"] == category
    ]
    rows.sort(key=lambda row: row["jenis_data"])
    return rows


def render_markdown(summary=None, sources=None, mappings=None):
    if summary is None:
        summary = coverage_summary(sources, mappings)
    if sources is None or mappings is None:
        sources, mappings = load_registry()

    lines = [
        "# Source Coverage 8 Kategori",
        "",
        f"Tanggal: **{summary['generated_at']}**  ",
        "Registry: `docs/SOURCE_COVERAGE_SOURCES.csv`  ",
        "Pemetaan: `docs/SOURCE_CATEGORY_MAP.csv`  ",
        "Status: **implementasi registry dan generator ringkasan**",
        "",
        "## 1. Batas dan definisi",
        "",
        "- Registry ini memetakan sumber ke delapan kategori geohazard target.",
        "- `kejadian_aktual` hanya dihitung sebagai cakupan operasional bila "
        "sumber aktif di pipeline dan pemetaan berstatus `terverifikasi`.",
        "- `laporan_berita`, `katalog_historis`, `peta_risiko`, "
        "`informasi_kerentanan`, `penelitian_kajian`, `informasi_manual`, "
        "`atribut_bahaya`, dan `katalog_data` tidak dihitung sebagai feed "
        "kejadian aktif.",
        "- Status akses, izin, dan implementasi disimpan terpisah agar akses "
        "HTTP tidak otomatis dianggap sebagai izin atau kesiapan operasional.",
        "- Komposisi jenis data mencakup semua status; hitungan operasional "
        "tetap memakai kolom event aktif terverifikasi.",
        "- Baseline dan database tidak diubah oleh generator laporan ini.",
        "",
        "## 2. Ringkasan registry",
        "",
        f"- Sumber terdaftar: **{summary['source_count']}**.",
        f"- Baris pemetaan sumber-kategori: **{summary['mapping_count']}**.",
        f"- Sumber aktif pipeline: **{len(summary['active_pipeline_ids'])}**.",
        f"- Sumber dengan status izin `perlu_izin`: "
        f"**{len(summary['need_permission_ids'])}**.",
        f"- Sumber belum tersedia/tidak sesuai: "
        f"**{len(summary['unavailable_ids'])}**.",
        f"- Sumber belum diverifikasi: **{len(summary['unverified_ids'])}**.",
        "",
        "### Status akses (teknis)",
        "",
        "| Status akses | Jumlah |",
        "|---|---:|",
    ]

    for status, count in summary["access_counts"].items():
        lines.append(f"| `{status}` | {count} |")

    lines.extend(
        [
            "",
            "### Status izin (legal)",
            "",
            "| Status izin | Jumlah |",
            "|---|---:|",
        ]
    )
    for status, count in summary["permission_counts"].items():
        lines.append(f"| `{status}` | {count} |")

    lines.extend(
        [
            "",
            "### Status implementasi",
            "",
            "| Status implementasi | Jumlah |",
            "|---|---:|",
        ]
    )
    for status, count in summary["implementation_counts"].items():
        lines.append(f"| `{status}` | {count} |")

    reconciliation_ids = summary["need_permission_without_access_permission_ids"]
    reconciliation_text = (
        ", ".join(f"`{source_id}`" for source_id in reconciliation_ids)
        if reconciliation_ids
        else "tidak ada"
    )
    lines.extend(
        [
            "",
            "### Rekonsiliasi status",
            "",
            f"- Status izin `perlu_izin`: **{len(summary['need_permission_ids'])}** sumber.",
            f"- Status akses `perlu_izin`: "
            f"**{summary['access_counts'].get('perlu_izin', 0)}** sumber.",
            "- Sumber dengan status izin `perlu_izin` tetapi status akses bukan "
            f"`perlu_izin`: **{len(reconciliation_ids)}** ({reconciliation_text}).",
            "- `status_akses` dan `status_izin` adalah dimensi berbeda; angka "
            "pada kedua tabel tidak dipaksakan sama.",
            "",
            "## 3. Matriks cakupan",
            "",
            "| Kategori | Sumber | Aktif pipeline | Event aktif terverifikasi | "
            "Event resmi aktif | Kandidat event resmi | Berita | Katalog historis | "
            "Peta risiko | Manual/kajian | Status cakupan | Prioritas |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )

    for item in summary["categories"]:
        lines.append(
            "| **{category}** | {total_sources} | {active_pipeline_sources} | "
            "{active_event_sources} | {official_active_event_sources} | "
            "{official_candidate_event_sources} | {news_sources} | "
            "{historical_sources} | {risk_sources} | {manual_sources} | "
            "**{coverage_status}** | {priority} |".format(**item)
        )

    lines.extend(
        [
            "",
            "## 4. Rincian sumber per kategori",
            "",
        ]
    )

    source_by_id = {row["source_id"]: row for row in sources}

    for item in summary["categories"]:
        lines.extend(
            [
                f"### {item['category']}",
                "",
                f"- Status cakupan: **{item['coverage_status']}**.",
                f"- Prioritas: **{item['priority']}**.",
                f"- Sumber: {item['total_sources']}.",
                f"- Komposisi jenis data: "
                f"{', '.join(f'`{key}`={value}' for key, value in item['data_types'].items())}.",
                "",
            ]
        )
        for source_id in item["source_ids"]:
            source = source_by_id[source_id]
            mapping_rows = _source_mapping_rows(
                source_id, item["category"], mappings
            )
            mapping_text = "; ".join(
                f"{row['jenis_data']} ({row['status_pemetaan']}; "
                f"{row['prioritas']})"
                for row in mapping_rows
            )
            lines.append(
                f"- `{source_id}` - {source['nama_sumber']} "
                f"[{source['status_akses']}; {source['status_izin']}; "
                f"{source['status_implementasi']}]: {mapping_text}."
            )
        lines.append("")

    lines.extend(
        [
            "## 5. Temuan utama",
            "",
            "- **Gempabumi** memiliki sumber resmi aktif terverifikasi dari BMKG "
            "dan sumber internasional pendukung. Ini satu-satunya kategori "
            "dengan cakupan operasional.",
            "- **Gunungapi dan Gerakan Tanah/Tanah Longsor** memiliki kandidat "
            "sumber resmi (PVMBG/Portal MBG/MAGMA) dengan status izin "
            "`perlu_izin`; belum boleh diotomatisasi.",
            "- **Tsunami** memiliki atribut potensi pada feed BMKG, kandidat "
            "kejadian internasional dari GDACS, katalog historis BMKG, dan peta "
            "bahaya BNPB. Tidak ada feed peringatan tsunami mandiri yang "
            "terverifikasi aktif.",
            "- **Likuefaksi, Abrasi dan Akresi, Penurunan Muka Tanah, dan "
            "Semburan Gas dan Lumpur** belum memiliki feed kejadian aktif "
            "terverifikasi. Yang tersedia adalah berita, peta risiko, atlas, "
            "publikasi, atau informasi manual.",
            "- Peta risiko, atlas, dashboard, dan katalog data tidak boleh "
            "menambah hitungan kejadian aktual.",
            "",
            "## 6. Sumber yang perlu ditindaklanjuti",
            "",
            "### Perlu izin (status izin)",
            "",
        ]
    )
    for source_id in summary["need_permission_ids"]:
        source = source_by_id[source_id]
        lines.append(f"- `{source_id}` (`status_akses`: `{source['status_akses']}`)")
    if not summary["need_permission_ids"]:
        lines.append("- Tidak ada.")

    lines.extend(["", "### Belum tersedia atau tidak sesuai", ""])
    for source_id in summary["unavailable_ids"]:
        lines.append(f"- `{source_id}`")
    if not summary["unavailable_ids"]:
        lines.append("- Tidak ada.")

    lines.extend(["", "### Belum diverifikasi", ""])
    for source_id in summary["unverified_ids"]:
        lines.append(f"- `{source_id}`")
    if not summary["unverified_ids"]:
        lines.append("- Tidak ada.")

    lines.extend(
        [
            "",
            "## 7. Rekomendasi",
            "",
            "1. Pertahankan klaim cakupan operasional hanya untuk Gempabumi "
            "sampai ada sumber kejadian resmi aktif untuk kategori lain.",
            "2. Urus izin tertulis PVMBG/Badan Geologi sebelum mengaktifkan "
            "API PVMBG, Portal MBG, atau MAGMA.",
            "3. Validasi katalog tsunami BMKG dan layer InaRISK sebagai sumber "
            "historis/peta, bukan feed kejadian.",
            "4. Cari sumber kejadian terstruktur untuk Likuefaksi, Abrasi dan "
            "Akresi, Penurunan Muka Tanah, dan Semburan Gas dan Lumpur.",
            "5. Jangan mengubah baseline atau database hanya karena registry "
            "ini diperbarui.",
            "",
            "## 8. Kesimpulan",
            "",
            "Registry menunjukkan bahwa delapan kategori sudah memiliki "
            "pemetaan sumber, tetapi baru Gempabumi yang tercakup secara "
            "operasional. Kategori lain memiliki kandidat resmi, berita, "
            "katalog historis, peta risiko, atau informasi manual yang harus "
            "dibedakan dari feed kejadian aktif.",
            "",
        ]
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validasi registry dan buat laporan cakupan 8 kategori."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPORT_PATH,
        help="Path laporan Markdown.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validasi registry tanpa menulis laporan.",
    )
    args = parser.parse_args()

    sources, mappings = load_registry()
    summary = coverage_summary(sources, mappings)

    if not args.check:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            render_markdown(summary, sources, mappings),
            encoding="utf-8",
        )
        print(f"Laporan ditulis: {args.output}")

    print(f"Sumber: {summary['source_count']}")
    print(f"Mapping: {summary['mapping_count']}")
    for item in summary["categories"]:
        print(f"{item['category']}: {item['coverage_status']}")


if __name__ == "__main__":
    main()
