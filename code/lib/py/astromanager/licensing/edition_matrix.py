from __future__ import annotations

from typing import Final

from .feature_registry import FEATURE_ORDER

FREE_FEATURES: Final[frozenset[str]] = frozenset({
    "core.import",
    "core.viewer",
    "core.targets",
    "core.sessions",
    "core.atlas_basic",
})

BASIC_FEATURES: Final[frozenset[str]] = FREE_FEATURES | frozenset({
    "core.stacking",
})

PLUS_FEATURES: Final[frozenset[str]] = BASIC_FEATURES | frozenset({
    "plus.progress",
    "plus.planning",
    "plus.visibility",
    "plus.recommendations",
    "plus.weather_basic",
    "plus.atlas_filters",
})

PRO_FEATURES: Final[frozenset[str]] = PLUS_FEATURES | frozenset({
    "pro.atlas_imagery",
    "pro.footprints",
    "pro.coverage",
    "pro.forecast_advanced",
    "pro.mosaic_progress",
    "pro.ai_tools",
})

EDITION_FEATURES: Final[dict[str, frozenset[str]]] = {
    "free": FREE_FEATURES,
    "basic": BASIC_FEATURES,
    "plus": PLUS_FEATURES,
    "pro": PRO_FEATURES,
    "dev_all": frozenset(FEATURE_ORDER),
}

EDITION_LABELS: Final[dict[str, str]] = {
    "free": "Free",
    "basic": "Basic",
    "plus": "Plus",
    "pro": "Pro",
    "dev_all": "Dev All",
}

DEFAULT_EDITION: Final[str] = "dev_all"
PUBLIC_EDITIONS: Final[tuple[str, ...]] = ("free", "basic", "plus", "pro")
