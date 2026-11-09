"""Aturan klasifikasi geographic scope kejadian geohazard.

Modul ini memisahkan geographic scope dari category scope. Field yang dipakai
adalah ``event_location.is_inside_indonesia`` dengan vocabulary yang sudah ada:
``ya`` (Indonesia), ``tidak`` (luar Indonesia), dan ``tidak_diketahui``.

Batas wilayah nasional Indonesia tidak tersedia sebagai polygon di repository.
Karena itu bounding box pilot hanya dipakai sebagai batas sanity check, bukan
sebagai bukti tunggal bahwa suatu titik berada di Indonesia atau di luar
Indonesia. Titik di luar bbox, di laut, atau dekat perbatasan tanpa bukti batas
yang memadai ditandai ``tidak_diketahui`` dan masuk review manual.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from wilayah_reference import PROVINCES, PROVINCE_ALIASES

ROOT = Path(__file__).resolve().parent
GAZETTEER_PATH = ROOT / "data" / "wilayah_gazetteer.json"

# Bbox pilot. Ini bukan batas hukum/wilayah nasional Indonesia.
PILOT_BBOX = (-11.0, 6.0, 95.0, 141.0)
NEAR_FIELD_KM = 50.0

INDONESIA = "indonesia"
OUTSIDE_INDONESIA = "luar_indonesia"
UNKNOWN = "tidak_diketahui"

SCOPE_TO_FLAG = {
    INDONESIA: "ya",
    OUTSIDE_INDONESIA: "tidak",
    UNKNOWN: "tidak_diketahui",
}
FLAG_TO_SCOPE = {value: key for key, value in SCOPE_TO_FLAG.items()}
VALID_FLAGS = set(FLAG_TO_SCOPE)

FOREIGN_MARKERS = re.compile(
    r"\b(?:nicaragua|fiji|papua\s+new\s+guinea|tonga|panama|"
    r"saint\s+kitts|carlsberg\s+ridge|new\s+zealand|kermadec|"
    r"ohonua|rio\s+grande|sandy\s+point|australia|malaysia|"
    r"philippines|filipina|timor[\s-]?leste|solomon|vanuatu|samoa|"
    r"guam|japan|jepang|china|tiongkok|taiwan)\b",
    re.I,
)
SEA_MARKERS = re.compile(
    r"\b(?:di\s+laut|sea|ocean|selat|samudra|samudera|"
    r"(?<!timur )(?<!barat )(?<!utara )(?<!selatan )laut)\b",
    re.I,
)
LAND_MARKERS = re.compile(r"\b(?:di\s+darat|darat)\b", re.I)
INDONESIA_LABEL = re.compile(r"\bindonesia\b", re.I)
ADMIN_PREFIX = re.compile(
    r"\b(?:kabupaten|kab\.?|kota|kecamatan|kec\.?|desa|kelurahan)\b",
    re.I,
)
DISTANCE_RE = re.compile(
    r"\b(\d+(?:[.,]\d+)?)\s*km\b",
    re.I,
)


def _normal(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _compact(text):
    return re.sub(r"\s+", "", _normal(text))


@lru_cache(maxsize=1)
def _province_keys():
    keys = {_normal(name) for name in PROVINCES}
    keys.update(_normal(alias) for alias in PROVINCE_ALIASES)
    return frozenset(key for key in keys if key)


@lru_cache(maxsize=1)
def _province_compact_keys():
    result = set()
    for key in _province_keys():
        compact = _compact(key)
        if len(compact) >= 4:
            result.add(compact)
    return result


@lru_cache(maxsize=1)
def _gazetteer_compact_names():
    if not GAZETTEER_PATH.is_file():
        return frozenset()
    with open(GAZETTEER_PATH, encoding="utf-8") as handle:
        data = json.load(handle)
    names = set()
    for item in data.get("kabupaten_kota", []):
        name = re.sub(
            r"^(kabupaten|kota)\s+",
            "",
            str(item.get("nama", "")),
            flags=re.I,
        )
        compact = _compact(name)
        if len(compact) >= 5:
            names.add(compact)
    return frozenset(names)


def province_matches(location_name):
    text = _normal(location_name)
    tokens = set(text.split())
    compact = _compact(location_name)
    matches = []
    for key in _province_keys():
        compact_key = _compact(key)
        if len(compact_key) >= 5 and compact_key in compact:
            matches.append(key)
        elif compact_key in tokens:
            matches.append(key)
    return sorted(set(matches))


def gazetteer_matches(location_name):
    compact = _compact(location_name)
    return sorted(
        name
        for name in _gazetteer_compact_names()
        if name in compact
    )


def _parse_distance(location_name):
    match = DISTANCE_RE.search(str(location_name or ""))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _parse_coordinate(latitude, longitude):
    try:
        lat = float(str(latitude).replace(",", "."))
        lon = float(str(longitude).replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return None
    return lat, lon


def is_inside_pilot_bbox(latitude, longitude):
    coordinate = _parse_coordinate(latitude, longitude)
    if coordinate is None:
        return None
    lat, lon = coordinate
    south, north, west, east = PILOT_BBOX
    return south <= lat <= north and west <= lon <= east


def _result(
    scope,
    confidence,
    basis,
    reason,
    *,
    inside_bbox=None,
    distance_km=None,
    toponyms=None,
    land_marker=False,
    sea_marker=False,
    foreign_marker=False,
    indonesia_label=False,
    requires_review=False,
):
    return {
        "geographic_scope": scope,
        "is_inside_indonesia": SCOPE_TO_FLAG[scope],
        "scope_confidence": confidence,
        "scope_basis": basis,
        "scope_reason": reason,
        "requires_review": bool(requires_review),
        "inside_pilot_bbox": inside_bbox,
        "distance_km": distance_km,
        "indonesia_toponyms": toponyms or [],
        "land_marker": bool(land_marker),
        "sea_marker": bool(sea_marker),
        "foreign_marker": bool(foreign_marker),
        "indonesia_label": bool(indonesia_label),
    }


def classify_location(
    location_name,
    latitude,
    longitude,
    coordinate_status="",
    source_id="",
    event_title="",
):
    """Klasifikasikan lokasi kejadian menjadi Indonesia/luar/unknown.

    ``event_title`` sengaja tidak dipakai sebagai bukti lokasi. Judul berita
    atau judul feed tidak boleh menjadi satu-satunya dasar geographic scope.
    """
    del event_title
    text = str(location_name or "")
    coordinate = _parse_coordinate(latitude, longitude)
    inside_bbox = is_inside_pilot_bbox(latitude, longitude)
    distance = _parse_distance(text)
    toponyms = sorted(set(province_matches(text) + gazetteer_matches(text)))
    land = bool(LAND_MARKERS.search(text))
    sea = bool(SEA_MARKERS.search(text))
    foreign = bool(FOREIGN_MARKERS.search(text))
    indonesia_label = bool(INDONESIA_LABEL.search(text))
    admin_prefix = bool(ADMIN_PREFIX.search(text))

    if coordinate is None:
        return _result(
            UNKNOWN,
            "unknown",
            "tanpa_koordinat_valid",
            "Tidak ada koordinat valid; scope geografis tidak dapat ditetapkan.",
            inside_bbox=inside_bbox,
            distance_km=distance,
            toponyms=toponyms,
            land_marker=land,
            sea_marker=sea,
            foreign_marker=foreign,
            indonesia_label=indonesia_label,
            requires_review=True,
        )

    if not toponyms and admin_prefix and str(source_id).startswith("bmkg_"):
        toponyms = ["administrative_prefix"]

    if inside_bbox is False:
        if foreign and not indonesia_label and not toponyms:
            return _result(
                OUTSIDE_INDONESIA,
                "medium",
                "koordinat_di_luar_bbox_pilot+penanda_negara_asing",
                "Koordinat di luar bbox pilot dan lokasi menyebut wilayah "
                "negara asing; tidak ada bukti toponimi Indonesia.",
                inside_bbox=inside_bbox,
                distance_km=distance,
                toponyms=toponyms,
                land_marker=land,
                sea_marker=sea,
                foreign_marker=foreign,
                indonesia_label=indonesia_label,
            )
        reason = (
            "Koordinat berada di luar bbox pilot. Bbox pilot bukan batas "
            "wilayah nasional; repository tidak memiliki polygon batas "
            "Indonesia yang dapat dipertanggungjawabkan."
        )
        if sea:
            reason += " Lokasi juga berada di laut."
        if land or toponyms or indonesia_label:
            reason += " Ada indikasi Indonesia, tetapi tidak cukup untuk "
            reason += "menetapkan scope tanpa verifikasi batas."
        return _result(
            UNKNOWN,
            "unknown",
            "koordinat_di_luar_bbox_pilot+batas_nasional_belum_tersedia",
            reason,
            inside_bbox=inside_bbox,
            distance_km=distance,
            toponyms=toponyms,
            land_marker=land,
            sea_marker=sea,
            foreign_marker=foreign,
            indonesia_label=indonesia_label,
            requires_review=True,
        )

    if sea:
        return _result(
            UNKNOWN,
            "unknown",
            "penanda_laut+tanpa_batas_nasional",
            "Episentrum berada di laut atau wilayah perairan; tanpa batas "
            "wilayah nasional yang terdokumentasi, scope tidak dipaksakan.",
            inside_bbox=inside_bbox,
            distance_km=distance,
            toponyms=toponyms,
            land_marker=land,
            sea_marker=sea,
            foreign_marker=foreign,
            indonesia_label=indonesia_label,
            requires_review=True,
        )

    if foreign:
        return _result(
            UNKNOWN,
            "unknown",
            "konflik_penanda_negara_asing_di_dalam_bbox_pilot",
            "Lokasi menyebut wilayah asing tetapi koordinat berada di dalam "
            "bbox pilot; bukti saling bertentangan.",
            inside_bbox=inside_bbox,
            distance_km=distance,
            toponyms=toponyms,
            land_marker=land,
            sea_marker=sea,
            foreign_marker=foreign,
            indonesia_label=indonesia_label,
            requires_review=True,
        )

    if toponyms:
        if land:
            return _result(
                INDONESIA,
                "medium",
                "koordinat_dalam_bbox_pilot+toponimi_indonesia+penanda_darat",
                "Koordinat sumber berada di dalam bbox pilot, lokasi resmi "
                "menyebut toponimi Indonesia, dan pusat gempa dinyatakan di "
                "darat. Koordinat belum diverifikasi.",
                inside_bbox=inside_bbox,
                distance_km=distance,
                toponyms=toponyms,
                land_marker=land,
                sea_marker=sea,
                foreign_marker=foreign,
                indonesia_label=indonesia_label,
            )
        if distance is not None and distance <= NEAR_FIELD_KM:
            return _result(
                INDONESIA,
                "medium",
                "koordinat_dalam_bbox_pilot+toponimi_indonesia+jarak_dekat",
                "Koordinat sumber berada di dalam bbox pilot dan lokasi resmi "
                "menyebut toponimi Indonesia pada jarak dekat "
                f"({distance:.0f} km). Koordinat belum diverifikasi.",
                inside_bbox=inside_bbox,
                distance_km=distance,
                toponyms=toponyms,
                land_marker=land,
                sea_marker=sea,
                foreign_marker=foreign,
                indonesia_label=indonesia_label,
            )
        if distance is not None and distance > NEAR_FIELD_KM:
            return _result(
                UNKNOWN,
                "unknown",
                "jarak_jauh_tanpa_penanda_darat",
                "Lokasi menyebut toponimi Indonesia, tetapi jarak "
                f"{distance:.0f} km dan tidak ada penanda darat yang cukup "
                "untuk menetapkan scope.",
                inside_bbox=inside_bbox,
                distance_km=distance,
                toponyms=toponyms,
                land_marker=land,
                sea_marker=sea,
                foreign_marker=foreign,
                indonesia_label=indonesia_label,
                requires_review=True,
            )
        return _result(
            UNKNOWN,
            "unknown",
            "toponimi_indonesia_tanpa_penanda_darat_atau_jarak_dekat",
            "Lokasi menyebut toponimi Indonesia, tetapi tidak ada penanda "
            "darat atau jarak dekat yang cukup untuk menetapkan scope.",
            inside_bbox=inside_bbox,
            distance_km=distance,
            toponyms=toponyms,
            land_marker=land,
            sea_marker=sea,
            foreign_marker=foreign,
            indonesia_label=indonesia_label,
            requires_review=True,
        )

    if distance is not None and distance > NEAR_FIELD_KM:
        return _result(
            UNKNOWN,
            "unknown",
            "jarak_jauh_tanpa_batas_nasional",
            "Lokasi berjarak jauh dari toponimi yang dikenali dan tidak ada "
            "batas wilayah nasional yang terdokumentasi.",
            inside_bbox=inside_bbox,
            distance_km=distance,
            toponyms=toponyms,
            land_marker=land,
            sea_marker=sea,
            foreign_marker=foreign,
            indonesia_label=indonesia_label,
            requires_review=True,
        )

    return _result(
        UNKNOWN,
        "unknown",
        "tanpa_toponimi_indonesia_yang_cukup",
        "Tidak ada toponimi Indonesia atau penanda lokasi yang cukup.",
        inside_bbox=inside_bbox,
        distance_km=distance,
        toponyms=toponyms,
        land_marker=land,
        sea_marker=sea,
        foreign_marker=foreign,
        indonesia_label=indonesia_label,
        requires_review=True,
    )
