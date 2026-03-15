#!/usr/bin/env bash
set -euo pipefail

PROJECT_CORE_ROOT="${PROJECT_CORE_ROOT:-/project-core}"
CORE_BACKUP_ROOT="${CORE_BACKUP_ROOT:-/project-core/_dev_backups/core}"

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

STAMP="$(date +%F_%H-%M-%S)"
OUT_DIR="${CORE_BACKUP_ROOT}"
OUT_ZIP="${OUT_DIR}/core_backup_${STAMP}.zip"
STAGE_DIR="/tmp/core_backup_${STAMP}"
MANIFEST_PATH="${STAGE_DIR}/manifest.json"

mkdir -p "${OUT_DIR}"
chown -R 1000:1000 "${PROJECT_CORE_ROOT}/code" "${PROJECT_CORE_ROOT}/scripts" 2>/dev/null || true
chown 1000:1000 "${PROJECT_CORE_ROOT}/VERSION" "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" "${PROJECT_CORE_ROOT}/CHANGELOG.md" "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" 2>/dev/null || true

rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}/core"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -e "${src}" ]; then
    mkdir -p "$(dirname "${dst}")"
    cp -a "${src}" "${dst}"
  fi
}

copy_if_exists "${PROJECT_CORE_ROOT}/code" "${STAGE_DIR}/core/code"
copy_if_exists "${PROJECT_CORE_ROOT}/scripts" "${STAGE_DIR}/core/scripts"
copy_if_exists "${PROJECT_CORE_ROOT}/VERSION" "${STAGE_DIR}/core/VERSION"
copy_if_exists "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" "${STAGE_DIR}/core/SCHEMA_VERSION"
copy_if_exists "${PROJECT_CORE_ROOT}/CHANGELOG.md" "${STAGE_DIR}/core/CHANGELOG.md"
copy_if_exists "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" "${STAGE_DIR}/core/CHANGELOG.unreleased.md"

python3 - <<'PY' "${MANIFEST_PATH}" "${PROJECT_CORE_ROOT}"
import datetime
import json
import sys

manifest_path = sys.argv[1]
core_root = sys.argv[2]

manifest = {
    "backup_type": "core",
    "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "core_root": core_root,
    "items": [
        "code/",
        "scripts/",
        "VERSION",
        "SCHEMA_VERSION",
        "CHANGELOG.md",
        "CHANGELOG.unreleased.md",
    ],
}
with open(manifest_path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2, ensure_ascii=False)
PY

python3 - <<'PY' "${STAGE_DIR}/core" "${OUT_ZIP}"
import os
import sys
import zipfile

src_root = sys.argv[1]
out_zip = sys.argv[2]

with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src_root):
        dirs.sort()
        files.sort()
        for name in files:
            full_path = os.path.join(root, name)
            arcname = os.path.relpath(full_path, src_root)
            zf.write(full_path, arcname)
PY

normalize_core_ownership

rm -rf "${STAGE_DIR}"
echo "CORE backup created: ${OUT_ZIP}"
echo "Ownership normalized to ${HOST_UID}:${HOST_GID}"
