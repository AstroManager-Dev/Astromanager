from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .edition_matrix import DEFAULT_EDITION, EDITION_FEATURES, EDITION_LABELS
from .feature_registry import FEATURES

RUNTIME_EDITION_ENV = "ASTROMANAGER_LICENSE_EDITION"


@dataclass(frozen=True)
class RuntimeLicenseContext:
    edition: str
    edition_label: str
    features: frozenset[str]
    source: str
    is_dev_override: bool

    @property
    def feature_count(self) -> int:
        return len(self.features)

    def has_feature(self, feature_code: str) -> bool:
        return feature_code in self.features

    def to_template_context(self) -> dict[str, Any]:
        return {
            "edition": self.edition,
            "edition_label": self.edition_label,
            "feature_codes": tuple(sorted(self.features)),
            "feature_count": self.feature_count,
            "is_dev_override": self.is_dev_override,
            "source": self.source,
        }


def normalize_runtime_edition(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in EDITION_FEATURES:
        return normalized
    return DEFAULT_EDITION


@lru_cache(maxsize=1)
def get_runtime_license_context() -> RuntimeLicenseContext:
    raw = os.environ.get(RUNTIME_EDITION_ENV)
    edition = normalize_runtime_edition(raw)
    return RuntimeLicenseContext(
        edition=edition,
        edition_label=EDITION_LABELS.get(edition, edition.title()),
        features=EDITION_FEATURES[edition],
        source=f"env:{RUNTIME_EDITION_ENV}",
        is_dev_override=(edition == "dev_all"),
    )


def reload_runtime_license_context() -> RuntimeLicenseContext:
    get_runtime_license_context.cache_clear()
    return get_runtime_license_context()


def runtime_has_feature(feature_code: str) -> bool:
    return get_runtime_license_context().has_feature(feature_code)


def require_runtime_feature(feature_code: str) -> None:
    if feature_code not in FEATURES:
        raise KeyError(f"Unknown license feature: {feature_code}")
    if not runtime_has_feature(feature_code):
        raise PermissionError(f"Feature not licensed for current edition: {feature_code}")
