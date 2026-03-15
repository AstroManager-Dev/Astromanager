#!/usr/bin/env bash
set -euo pipefail

PROJECT_CORE_ROOT="${PROJECT_CORE_ROOT:-/project-core}"
CORE_BACKUP_ROOT="${CORE_BACKUP_ROOT:-/project-core/_dev_backups/core}"
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
  ZIP_PATH="$(ls -1t "${CORE_BACKUP_ROOT}"/core_backup_*.zip 2>/dev/null | head -n 1 || true)"
fi

if [ -z "${ZIP_PATH}" ]; then
  echo "Kein Core-Backup gefunden."
  exit 1
fi

if [ ! -f "${ZIP_PATH}" ]; then
  echo "Backup-ZIP nicht gefunden: ${ZIP_PATH}"
  exit 1
fi

STAGE_DIR="/tmp/core_restore_$(date +%s)"
mkdir -p "${STAGE_DIR}"

python3 - <<'PY' "${ZIP_PATH}" "${STAGE_DIR}"
import sys
import zipfile

zip_path = sys.argv[1]
stage_dir = sys.argv[2]

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(stage_dir)
PY

PAYLOAD_ROOT="${STAGE_DIR}"
if [ -d "${STAGE_DIR}/core" ]; then
  PAYLOAD_ROOT="${STAGE_DIR}/core"
fi

restore_dir() {
  local src="$1"
  local dst="$2"
  if [ -d "${src}" ]; then
    rm -rf "${dst}"
    mkdir -p "$(dirname "${dst}")"
    cp -a "${src}" "${dst}"
  fi
}

restore_file() {
  local src="$1"
  local dst="$2"
  if [ -f "${src}" ]; then
    mkdir -p "$(dirname "${dst}")"
    cp -f "${src}" "${dst}"
  fi
}

restore_dir  "${PAYLOAD_ROOT}/code"                    "${PROJECT_CORE_ROOT}/code"
restore_dir  "${PAYLOAD_ROOT}/scripts"                 "${PROJECT_CORE_ROOT}/scripts"
restore_file "${PAYLOAD_ROOT}/VERSION"                 "${PROJECT_CORE_ROOT}/VERSION"
restore_file "${PAYLOAD_ROOT}/SCHEMA_VERSION"          "${PROJECT_CORE_ROOT}/SCHEMA_VERSION"
restore_file "${PAYLOAD_ROOT}/CHANGELOG.md"            "${PROJECT_CORE_ROOT}/CHANGELOG.md"
restore_file "${PAYLOAD_ROOT}/CHANGELOG.unreleased.md" "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md"

normalize_core_ownership

chown -R 1000:1000 "${PROJECT_CORE_ROOT}/code" "${PROJECT_CORE_ROOT}/scripts" 2>/dev/null || true
chown 1000:1000 "${PROJECT_CORE_ROOT}/VERSION" "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" "${PROJECT_CORE_ROOT}/CHANGELOG.md" "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" 2>/dev/null || true

rm -rf "${STAGE_DIR}"
echo "CORE backup restored: ${ZIP_PATH}"
echo "Ownership normalized to ${HOST_UID}:${HOST_GID}"
