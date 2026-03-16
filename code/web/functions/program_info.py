import re
from pathlib import Path
from typing import Any

from .common import PROJECT_CORE_ROOT, PROJECT_ROOT


def project_text_file_value(name: str) -> str:
    candidates = [PROJECT_ROOT / name, PROJECT_CORE_ROOT / name]
    resolved = Path(__file__).resolve()
    candidates.extend(parent / name for parent in resolved.parents)

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        try:
            if candidate.exists():
                return candidate.read_text(encoding="utf-8").strip()
        except Exception:
            continue
    return ""


def parse_patch_log(text_value: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in text_value.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = [part.strip() for part in raw.split("|", 2)]
        if len(parts) == 3:
            version_value, date_value, message = parts
        else:
            version_value, date_value, message = "", "", raw
        entries.append({"version": version_value, "date": date_value, "message": message})
    return entries


def parse_minor_log(text_value: str) -> list[dict[str, Any]]:
    releases: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text_value.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})\s+Version:\s+(.+)$", stripped)
        if match:
            date_value, version_value = match.groups()
            current = {"date": date_value, "version": version_value.strip(), "items": []}
            releases.append(current)
            continue
        if stripped.startswith("- "):
            if current is None:
                current = {"date": "", "version": "", "items": []}
                releases.append(current)
            current["items"].append(stripped[2:].strip())
    return releases


def app_version_value() -> str:
    try:
        return (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        return ""

def load_program_info() -> dict[str, Any]:
    version_value = project_text_file_value("VERSION")
    schema_value = project_text_file_value("SCHEMA_VERSION")
    patch_text = project_text_file_value("CHANGELOG.unreleased.md")
    patch_log = parse_patch_log(patch_text) if patch_text else []
    minor_log = parse_minor_log(project_text_file_value("CHANGELOG.md"))
    return {
        "version": version_value,
        "schema_version": schema_value,
        "patch_log": patch_log,
        "minor_count": len(minor_log),
        "patch_count": len(patch_log),
        "minor_log": minor_log,
    }
