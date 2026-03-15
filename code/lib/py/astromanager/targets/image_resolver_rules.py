from __future__ import annotations

from typing import Any, Mapping

SKYVIEW_DEFAULT_SURVEY = "DSS2 Color"
SKYVIEW_NEBULA_SURVEY = "H-Alpha"
SKYVIEW_NEBULA_HINTS = (
    "emissionsnebel",
    "emission nebula",
    "diffuser nebel",
    "diffuse nebula",
    "planetarischer nebel",
    "planetary nebula",
    "h-ii",
    "h ii",
    "hii",
    "barnard",
    "california",
    "rosettennebel",
    "rosette",
    "sh2",
    "sharpless",
    "ic 434",
)

FRAME_DEFAULTS_NO_SIZE = {
    "galaxy": 0.30,
    "cluster": 0.35,
    "nebula": 0.80,
    "default": 0.35,
}
LEGACY_FRAME_DEFAULTS_NO_SIZE = {
    "galaxy": 0.22,
    "cluster": 0.28,
    "nebula": 0.75,
    "default": 0.30,
}
FRAME_LIMITS = {
    "skyview": (0.12, 3.0),
    "legacy": (0.12, 1.5),
}
FRAME_MULTIPLIERS = {
    "skyview": {"default": 2.2, "nebula": 1.8},
    "legacy": {"default": 2.0, "nebula": 1.6},
}
LEGACY_DEFAULT_BANDS = "grz"
LEGACY_DEFAULT_PIXSCALE = 0.262
LEGACY_DEFAULT_MAX_SIZE = 512
LEGACY_NORTH_DEC_BOUNDARY = 32.375
LEGACY_LAYER_NORTH = "ls-dr9-north"
LEGACY_LAYER_SOUTH = "ls-dr10-south"

SKYVIEW_ERROR_TEXT_TOKENS = (
    "no data",
    "no pixels",
    "nothing found",
    "blank field",
    "no images",
    "no suitable surveys",
    "not found",
)
SKYVIEW_ALLOWED_IMAGE_CONTENT_TYPES = (
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "application/fits",
    "image/fits",
)
SKYVIEW_MIN_IMAGE_BYTES = 1024
SKYVIEW_BLANK_STDDEV_MAX = 2.0
SKYVIEW_BLANK_UNIQUE_VALUES_MAX = 8
SKYVIEW_BLANK_SAMPLE_SIZE = (128, 128)


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_text(value: Any) -> str:
    return norm(value).lower()


def numeric(value: Any):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def choose_query_name(row: Mapping[str, Any]) -> str:
    for key in ("final_name", "display_name", "label_de", "label_en", "canonical_name"):
        value = norm(row[key]) if key in row.keys() else ""
        if value:
            return value
    return ""


def classify_target_image_kind(row: Mapping[str, Any]) -> str:
    text = " ".join(
        [
            normalize_text(row["final_objtype"]) if "final_objtype" in row.keys() else "",
            normalize_text(row["object_type_label_de"]) if "object_type_label_de" in row.keys() else "",
            normalize_text(row["object_type_label_en"]) if "object_type_label_en" in row.keys() else "",
        ]
    )
    if "galax" in text:
        return "galaxy"
    if "cluster" in text or "sternhaufen" in text:
        return "cluster"
    if "nebel" in text or "nebula" in text:
        return "nebula"
    return "default"


def choose_skyview_survey(row: Mapping[str, Any]) -> str:
    text = " ".join(
        [
            normalize_text(row["final_objtype"]) if "final_objtype" in row.keys() else "",
            normalize_text(row["object_type_label_de"]) if "object_type_label_de" in row.keys() else "",
            normalize_text(row["object_type_label_en"]) if "object_type_label_en" in row.keys() else "",
            normalize_text(row["label_de"]) if "label_de" in row.keys() else "",
            normalize_text(row["label_en"]) if "label_en" in row.keys() else "",
            normalize_text(row["canonical_name"]) if "canonical_name" in row.keys() else "",
        ]
    )
    if any(token in text for token in SKYVIEW_NEBULA_HINTS):
        return SKYVIEW_NEBULA_SURVEY
    return SKYVIEW_DEFAULT_SURVEY


def choose_frame_deg(row: Mapping[str, Any], profile: str) -> float:
    size_arcmin = numeric(row["angular_size_arcmin"]) if "angular_size_arcmin" in row.keys() else None
    kind = classify_target_image_kind(row)
    defaults = LEGACY_FRAME_DEFAULTS_NO_SIZE if profile == "legacy" else FRAME_DEFAULTS_NO_SIZE

    if size_arcmin is None or size_arcmin <= 0:
        return defaults.get(kind, defaults["default"])

    size_deg = size_arcmin / 60.0
    multipliers = FRAME_MULTIPLIERS[profile]
    frame_deg = max(size_deg * multipliers["default"], FRAME_LIMITS[profile][0])
    if kind == "nebula":
        nebula_min = 0.30 if profile == "legacy" else 0.35
        frame_deg = max(size_deg * multipliers["nebula"], nebula_min)

    lo, hi = FRAME_LIMITS[profile]
    return round(min(max(frame_deg, lo), hi), 4)


def choose_legacy_layer(dec_deg: float) -> str:
    return LEGACY_LAYER_NORTH if dec_deg >= LEGACY_NORTH_DEC_BOUNDARY else LEGACY_LAYER_SOUTH


def legacy_size_px_from_frame(
    frame_deg: float,
    pixscale_arcsec: float = LEGACY_DEFAULT_PIXSCALE,
    max_size_px: int = LEGACY_DEFAULT_MAX_SIZE,
) -> int:
    pixels = int(round((frame_deg * 3600.0) / pixscale_arcsec))
    return max(128, min(max_size_px, pixels))
