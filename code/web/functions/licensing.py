from __future__ import annotations

try:
    from astromanager.licensing import (
        FEATURES,
        get_runtime_license_context,
        require_runtime_feature,
        runtime_has_feature,
    )
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, '/project-core/code/lib/py')
    from astromanager.licensing import (
        FEATURES,
        get_runtime_license_context,
        require_runtime_feature,
        runtime_has_feature,
    )


def build_license_context() -> dict[str, object]:
    context = get_runtime_license_context().to_template_context()
    context["feature_labels"] = {
        code: FEATURES[code].label
        for code in context["feature_codes"]
        if code in FEATURES
    }
    return context


__all__ = [
    "build_license_context",
    "require_runtime_feature",
    "runtime_has_feature",
]
