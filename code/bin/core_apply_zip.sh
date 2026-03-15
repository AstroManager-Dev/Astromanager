#!/usr/bin/env bash
set -euo pipefail

PROJECT_CORE_ROOT="${PROJECT_CORE_ROOT:-/project-core}"
ZIP_PATH="${1:-}"

HOST_UID="${HOST_UID:-1000}"
HOST_GID="${HOST_GID:-1000}"

normalize_core_ownership() {
  chown -R "${HOST_UID}:${HOST_GID}" "${PROJECT_CORE_ROOT}/code" "${PROJECT_CORE_ROOT}/scripts" 2>/dev/null || true
  chown "${HOST_UID}:${HOST_GID}" \
    "${PROJECT_CORE_ROOT}/VERSION" \
    "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" \
    "${PROJECT_CORE_ROOT}/CHANGELOG.md" \
    "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" 2>/dev/null || true
}

if [ -z "${ZIP_PATH}" ]; then
  echo "Usage: core_apply_zip.sh /path/to/upload.zip"
  exit 1
fi

if [ ! -f "${ZIP_PATH}" ]; then
  echo "ZIP nicht gefunden: ${ZIP_PATH}"
  exit 1
fi

STAGE_DIR="/tmp/core_apply_$(date +%s)"
mkdir -p "${STAGE_DIR}"

python3 - <<'PY' "${ZIP_PATH}" "${STAGE_DIR}"
import sys
import zipfile
from pathlib import Path

zip_path = Path(sys.argv[1])
stage_dir = Path(sys.argv[2]).resolve()

with zipfile.ZipFile(zip_path, "r") as zf:
    for member in zf.infolist():
        name = member.filename
        if name.startswith("/") or ".." in Path(name).parts:
            raise SystemExit(f"Unsicherer ZIP-Pfad: {name}")
        target = (stage_dir / name).resolve()
        if not str(target).startswith(str(stage_dir)):
            raise SystemExit(f"ZIP-Pfad verlässt Zielverzeichnis: {name}")
    zf.extractall(stage_dir)
PY

PAYLOAD_ROOT="${STAGE_DIR}"
if [ -d "${STAGE_DIR}/core" ]; then
  PAYLOAD_ROOT="${STAGE_DIR}/core"
fi

apply_dir_overlay() {
  local src="$1"
  local dst="$2"
  if [ -d "${src}" ]; then
    mkdir -p "${dst}"
    rsync -a "${src}/" "${dst}/"
  fi
}

apply_file_overlay() {
  local src="$1"
  local dst="$2"
  if [ -f "${src}" ]; then
    mkdir -p "$(dirname "${dst}")"
    cp -f "${src}" "${dst}"
  fi
}

apply_dir_overlay  "${PAYLOAD_ROOT}/code"                    "${PROJECT_CORE_ROOT}/code"
apply_dir_overlay  "${PAYLOAD_ROOT}/scripts"                 "${PROJECT_CORE_ROOT}/scripts"
apply_file_overlay "${PAYLOAD_ROOT}/VERSION"                 "${PROJECT_CORE_ROOT}/VERSION"
apply_file_overlay "${PAYLOAD_ROOT}/SCHEMA_VERSION"          "${PROJECT_CORE_ROOT}/SCHEMA_VERSION"
apply_file_overlay "${PAYLOAD_ROOT}/CHANGELOG.md"            "${PROJECT_CORE_ROOT}/CHANGELOG.md"
apply_file_overlay "${PAYLOAD_ROOT}/CHANGELOG.unreleased.md" "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md"

normalize_core_ownership

chown -R 1000:1000 "${PROJECT_CORE_ROOT}/code" "${PROJECT_CORE_ROOT}/scripts" 2>/dev/null || true
chown 1000:1000 "${PROJECT_CORE_ROOT}/VERSION" "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" "${PROJECT_CORE_ROOT}/CHANGELOG.md" "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" 2>/dev/null || true

rm -rf "${STAGE_DIR}"
echo "CORE zip applied safely (overlay only): ${ZIP_PATH}"
echo "Ownership normalized to ${HOST_UID}:${HOST_GID}"
