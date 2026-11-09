"""Context-aware relevance classification for GeoHazard documents.

The classifier separates two questions:

* Is this document about a geohazard (relevance)?
* If it is, which of the monitored categories does it belong to?

A document is only shown as news when its status is ``relevan``.  Documents
with an ambiguous geological signal are kept as ``perlu_review`` instead of
being silently promoted or discarded.
"""

import re

from category_detector import clean_text, detect_category_detail
from geohazard_pipeline.util import TARGET_CATEGORIES

RELEVANCE_RELEVANT = "relevan"
RELEVANCE_IRRELEVANT = "tidak_relevan"
RELEVANCE_REVIEW = "perlu_review"

RELEVANCE_STATUSES = (
    RELEVANCE_RELEVANT,
    RELEVANCE_IRRELEVANT,
    RELEVANCE_REVIEW,
)

CLASSIFIER_VERSION = "fix07-context-v1"

_RELEVANT_CATEGORIES = frozenset(TARGET_CATEGORIES)

# Terms that show a concrete hazard event, impact, risk, warning, or action.
_EVENT_OR_IMPACT = re.compile(
    r"\b(?:terjadi|berlangsung|melanda|menerjang|menghantam|mengguncang|"
    r"guncangan|getaran|merusak|menewaskan|mengakibatkan|menimbulkan|"
    r"korban|evakuasi|kerusakan|terdampak|mengungsi|waspada|siaga|"
    r"peringatan|potensi|ancaman|risiko|mitigasi|penanggulangan|"
    r"penanganan|memadamkan|terkubur|tertimpa|putus|ambles|retak|"
    r"mengeluarkan|semburan|letusan|erupsi|longsor|tsunami|abrasi|"
    r"akresi|likuefaksi|subsiden|amblesan|terendam|menggenang|"
    r"mengungsi|pengungsian|darurat|krisis|bencana|memakan\s+korban|"
    r"menghanyutkan|menutup\s+jalan|merendam|mengancam)\b"
)

# Broad geological context.  This is deliberately wider than the eight
# categories so that relevant "Lainnya" documents can still be recognised.
_GEOLOGIC_CONTEXT = re.compile(
    r"\b(?:geologi|geologis|vulkanik|vulkanologi|magma|patahan|sesar|"
    r"lempeng|tektonik|seismik|kawah|kaldera|lahar|abu\s+vulkanik|"
    r"awan\s+panas|gunung\s+berapi|gunung\s+api|tanah\s+bergerak|"
    r"gerakan\s+tanah|longsor|gempa|gempabumi|tsunami|likuefaksi|"
    r"abrasi|akresi|subsiden|amblesan|semburan\s+gas|lumpur\s+panas|"
    r"erupsi|letusan|krakatau|anak\s+krakatau|daratan\s+baru)\b"
)

_OUT_OF_SCOPE = re.compile(
    r"\b(?:banjir|kekeringan|kebakaran\s+hutan|kebakaran\s+lahan|"
    r"karhutla|cuaca\s+ekstrem|hujan\s+lebat|hujan\s+deras|petir|"
    r"angin\s+puting\s+beling|gelombang\s+tinggi|kabut\s+asap|"
    r"asap\s+karhutla|krisis\s+iklim|perubahan\s+iklim)\b"
)

_RECREATION = re.compile(
    r"\b(?:pendaki|pendakian|wisata|travel|destinasi|liburan|rekreasi|"
    r"camping|hiking|panorama|spot\s+foto|tempat\s+foto|"
    r"pemandangan|objek\s+wisata|paket\s+wisata)\b"
)

_GENERIC_EDUCATION = re.compile(
    r"\b(?:apa\s+itu|mengenal|fakta|manfaat|cara|tips|panduan|sejarah|"
    r"unik|paling|daftar|rekomendasi|penjelasan\s+ahli|begini|"
    r"kenapa|mengapa|berapa|kapan)\b"
)

_WILDLIFE_ENVIRONMENT = re.compile(
    r"\b(?:monyet|satwa|hewan|fauna|konservasi|badak|gajah|burung|"
    r"hiu|paus|trenggiling|kukang|orang\s+utan|mangrove|sampah|"
    r"pupuk|eco\s+enzyme|lingkungan|iklim|hutan|spesies|habitat|"
    r"ekosistem|keanekaragaman|flora)\b"
)

_OFF_TOPIC = re.compile(
    r"\b(?:politik|pemilu|partai|dpr|mpr|dprd|kpk|korupsi|hukum|"
    r"pengadilan|sidang|polisi|polri|kriminal|maling|tawuran|narkoba|"
    r"ekonomi|bisnis|saham|ihsg|bank|ojk|bei|investasi|harga|"
    r"pendidikan|sekolah|mahasiswa|kesehatan|rumah\s+sakit|bpjs|"
    r"olahraga|sepak\s+bola|liga|atlet|asian\s+para\s+games|"
    r"hiburan|selebriti|film|musik|festival|budaya|pariwisata|"
    r"teknologi|otomotif|kendaraan|internet|ai|digital|"
    r"agama|keagamaan|nasionalisme|perbatasan|pemerintahan|menteri|"
    r"presiden|prabowo|jokowi|gibran)\b"
)

_NON_GEOLOGIC_GEMPA = re.compile(
    r"\b(?:gempa\s+politik|gempa\s+ekonomi|gempa\s+saham|"
    r"gempa\s+di\s+dunia\s+usaha|gempa\s+pasar)\b"
)

_SEISMIC_EVIDENCE = re.compile(
    r"\b(?:magnitudo|magnitud|richter|sr|skala\s+richter|episenter|"
    r"hiposenter|kedalaman|guncangan|getaran|patahan|sesar|lempeng|"
    r"tektonik|bmkg|usgs|gempa\s+bumi|gempabumi)\b"
)

_FRAUD_CONTEXT = re.compile(
    r"\b(?:diduga|korupsi|penyelewengan|tersangka|terdakwa|saham|"
    r"beli\s+saham|dana\s+bencana|dana\s+bantuan|kejaksaan|kpk|"
    r"pengadilan|sidang|hukum|kasus\s+hukum|penjara|vonis)\b"
)

_STRONG_TITLE_EVENT = re.compile(
    r"\b(?:mengguncang|melanda|menerjang|menghantam|erupsi|meletus|"
    r"letusan|longsor|tsunami|abrasi|likuefaksi|ambles|semburan|"
    r"terkubur|tertimpa|merusak|menewaskan)\b"
    r"|\bm\s*\d+(?:[.,]\d+)?\b"
)

_SOURCE_OFFICIAL = re.compile(
    r"\b(?:bmkg|usgs|gdacs|official|resmi)\b", re.I
)


def _has(pattern, text):
    return bool(pattern.search(text))


def _base_result(status, category, basis, evidence, confidence="medium"):
    return {
        "relevance_status": status,
        "relevance_category": category or "Lainnya",
        "relevance_basis": basis,
        "relevance_confidence": confidence,
        "relevance_evidence": evidence[:1000],
        "classifier_version": CLASSIFIER_VERSION,
    }


def classify_relevance(
    title,
    content="",
    category_hint="",
    source_label="",
    source_type="",
):
    """Return a deterministic relevance decision for one document.

    ``category_hint`` is the source/legacy category.  It is only used as a
    fallback when the text itself supports a geohazard interpretation.
    """

    title_text = clean_text(title)
    content_text = clean_text(content)
    combined = f"{title_text} {content_text}".strip()
    hint = category_hint if category_hint in _RELEVANT_CATEGORIES else ""

    detected, detected_basis = detect_category_detail(title_text, content_text)
    category = detected if detected in _RELEVANT_CATEGORIES else ""
    basis = detected_basis

    # A legacy/source label may preserve a direct category when the current
    # detector only sees weak content evidence.
    if not category and hint and _has(_GEOLOGIC_CONTEXT, combined):
        category = hint
        basis = f"petunjuk:{hint}"

    event = _has(_EVENT_OR_IMPACT, combined)
    geologic = _has(_GEOLOGIC_CONTEXT, combined)
    recreation = _has(_RECREATION, title_text)
    education = _has(_GENERIC_EDUCATION, title_text)
    out_of_scope = _has(_OUT_OF_SCOPE, combined)
    off_topic = _has(_OFF_TOPIC, title_text)
    wildlife = _has(_WILDLIFE_ENVIRONMENT, combined)
    official = bool(source_type and "official" in source_type) or bool(
        _SOURCE_OFFICIAL.search(source_label or "")
    )

    evidence_parts = [
        f"detector={detected_basis}",
        f"kategori={category or 'Lainnya'}",
        f"peristiwa/dampak={'ya' if event else 'tidak'}",
        f"konteks_geologi={'ya' if geologic else 'tidak'}",
    ]

    if category:
        if _has(_FRAUD_CONTEXT, title_text) and not _has(
            _STRONG_TITLE_EVENT, title_text
        ) and not official:
            return _base_result(
                RELEVANCE_IRRELEVANT,
                "Lainnya",
                "konteks_non_geohazard",
                "; ".join(evidence_parts),
            )
        if _has(_NON_GEOLOGIC_GEMPA, combined) and not _has(
            _SEISMIC_EVIDENCE, combined
        ):
            return _base_result(
                RELEVANCE_IRRELEVANT,
                "Lainnya",
                "gempa_non_geologis",
                "; ".join(evidence_parts),
            )
        if recreation and not event:
            return _base_result(
                RELEVANCE_IRRELEVANT,
                category,
                "konteks_rekreasi",
                "; ".join(evidence_parts),
            )
        if off_topic and not event and not official:
            return _base_result(
                RELEVANCE_IRRELEVANT,
                category,
                "konteks_off_topic",
                "; ".join(evidence_parts),
            )
        if education and not event and not official:
            return _base_result(
                RELEVANCE_REVIEW,
                category,
                "edukasi_tanpa_peristiwa",
                "; ".join(evidence_parts),
            )
        return _base_result(
            RELEVANCE_RELEVANT,
            category,
            basis,
            "; ".join(evidence_parts),
            "high" if official else "medium",
        )

    if out_of_scope and not geologic:
        return _base_result(
            RELEVANCE_IRRELEVANT,
            "Lainnya",
            "di_luar_8_kategori",
            "; ".join(evidence_parts),
        )

    if geologic:
        if recreation:
            return _base_result(
                RELEVANCE_IRRELEVANT,
                "Lainnya",
                "konteks_rekreasi",
                "; ".join(evidence_parts),
            )
        if education and not event:
            return _base_result(
                RELEVANCE_REVIEW,
                "Lainnya",
                "edukasi_tanpa_peristiwa",
                "; ".join(evidence_parts),
            )
        if event:
            return _base_result(
                RELEVANCE_RELEVANT,
                "Lainnya",
                "konteks_geologi_lainnya",
                "; ".join(evidence_parts),
            )
        return _base_result(
            RELEVANCE_REVIEW,
            "Lainnya",
            "konteks_geologi_tanpa_peristiwa",
            "; ".join(evidence_parts),
        )

    if wildlife or out_of_scope or off_topic:
        return _base_result(
            RELEVANCE_IRRELEVANT,
            "Lainnya",
            "tidak_ada_konteks_geohazard",
            "; ".join(evidence_parts),
        )

    return _base_result(
        RELEVANCE_IRRELEVANT,
        "Lainnya",
        "tidak_ada_bukti_geohazard",
        "; ".join(evidence_parts),
    )
